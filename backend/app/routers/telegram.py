"""
Telegram Bot webhook handler and message processing.
"""
import hashlib
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from collections import OrderedDict
import time

from fastapi import APIRouter, HTTPException, Header, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.config import get_settings
from app.database import async_session_maker
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.services.ocr_service import get_ocr_service
from app.services.extraction_service import get_extraction_service
from app.services.vendor_matcher import get_vendor_matcher

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/telegram", tags=["Telegram"])

# Simple cache to prevent duplicate update processing (stores last 1000 update_ids)
_processed_updates: OrderedDict[int, float] = OrderedDict()
MAX_CACHE_SIZE = 1000

def is_duplicate_update(update_id: int) -> bool:
    """Check if we've already processed this update."""
    if update_id in _processed_updates:
        return True
    
    # Add to cache
    _processed_updates[update_id] = time.time()
    
    # Trim cache if too large
    while len(_processed_updates) > MAX_CACHE_SIZE:
        _processed_updates.popitem(last=False)
    
    return False


from pydantic import BaseModel, Field

# Pydantic models for Telegram updates
class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None


class TelegramChat(BaseModel):
    id: int
    type: str
    first_name: Optional[str] = None
    username: Optional[str] = None


class TelegramPhotoSize(BaseModel):
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: Optional[int] = None


class TelegramDocument(BaseModel):
    file_id: str
    file_unique_id: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None


class TelegramMessage(BaseModel):
    message_id: int
    from_user: Optional[TelegramUser] = Field(None, alias="from")
    chat: TelegramChat
    date: int
    text: Optional[str] = None
    photo: Optional[list[TelegramPhotoSize]] = None
    document: Optional[TelegramDocument] = None
    caption: Optional[str] = None

    class Config:
        populate_by_name = True


class TelegramCallbackQuery(BaseModel):
    id: str
    from_user: TelegramUser = Field(..., alias="from")
    message: Optional[TelegramMessage] = None
    data: Optional[str] = None

    class Config:
        populate_by_name = True


class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None
    callback_query: Optional[TelegramCallbackQuery] = None


class TelegramBot:
    """Telegram Bot API wrapper."""
    
    def __init__(self, token: str):
        self.token = token
        self.api_base = f"https://api.telegram.org/bot{token}"
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: Optional[dict] = None,
        parse_mode: str = "HTML",
    ) -> dict:
        """Send a text message."""
        async with httpx.AsyncClient() as client:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = await client.post(
                f"{self.api_base}/sendMessage",
                json=payload,
                timeout=30.0,
            )
            return response.json()
    
    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False,
    ) -> dict:
        """Answer a callback query."""
        async with httpx.AsyncClient() as client:
            payload = {
                "callback_query_id": callback_query_id,
                "show_alert": show_alert,
            }
            if text:
                payload["text"] = text
            
            response = await client.post(
                f"{self.api_base}/answerCallbackQuery",
                json=payload,
                timeout=30.0,
            )
            return response.json()
    
    async def get_file(self, file_id: str) -> dict:
        """Get file info for downloading."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/getFile",
                params={"file_id": file_id},
                timeout=30.0,
            )
            return response.json()
    
    async def download_file(self, file_path: str) -> bytes:
        """Download a file from Telegram servers."""
        async with httpx.AsyncClient() as client:
            url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            response = await client.get(url, timeout=60.0)
            return response.content
    
    async def edit_message_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        reply_markup: Optional[dict] = None,
        parse_mode: str = "HTML",
    ) -> dict:
        """Edit a message."""
        async with httpx.AsyncClient() as client:
            payload = {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "parse_mode": parse_mode,
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = await client.post(
                f"{self.api_base}/editMessageText",
                json=payload,
                timeout=30.0,
            )
            return response.json()


# Create bot instance
bot = TelegramBot(settings.telegram_bot_token) if settings.telegram_bot_token else None


def verify_telegram_secret(secret: str) -> bool:
    """Verify the webhook secret token."""
    if not settings.telegram_webhook_secret:
        return True  # No secret configured, allow all
    return secret == settings.telegram_webhook_secret


async def get_or_create_user(telegram_id: str, name: str) -> User:
    """Get or create a user by Telegram ID."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                name=name,
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Created new user: {name} ({telegram_id})")
        
        return user


async def process_photo(
    bot: TelegramBot,
    chat_id: int,
    user: User,
    photo_sizes: list[TelegramPhotoSize],
) -> None:
    """Process a photo message - download, OCR, and create draft."""
    # Get the largest photo
    largest = max(photo_sizes, key=lambda p: p.file_size or 0)
    
    try:
        # Notify user we're processing
        await bot.send_message(chat_id, "📄 Fiş/fatura işleniyor...")
        
        # Download file
        file_info = await bot.get_file(largest.file_id)
        if not file_info.get("ok"):
            await bot.send_message(chat_id, "❌ Dosya indirilemedi.")
            return
        
        file_path = file_info["result"]["file_path"]
        content = await bot.download_file(file_path)
        
        # Save locally
        file_hash = hashlib.sha256(content).hexdigest()
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        local_path = upload_dir / f"{file_hash}.jpg"
        
        with open(local_path, "wb") as f:
            f.write(content)
        
        # OCR processing
        ocr_service = get_ocr_service()
        extraction_service = get_extraction_service()
        vendor_matcher = get_vendor_matcher()
        
        ocr_result = ocr_service.extract_text(str(local_path))
        raw_text = ocr_result.get("text", "")
        extraction = extraction_service.extract(raw_text)
        
        # Match vendor
        async with async_session_maker() as db:
            vendor_match = await vendor_matcher.find_match(
                db,
                user.id,
                vendor_name=extraction.vendor_name,
                vkn=extraction.vendor_vkn,
            )
            
            # Create document
            document = Document(
                user_id=user.id,
                vendor_id=vendor_match.vendor_id if not vendor_match.is_new else None,
                status=DocumentStatus.DRAFT.value,
                doc_date=extraction.doc_date,
                doc_no=extraction.doc_no,
                currency=extraction.currency,
                total_gross=extraction.total_gross,
                total_tax=extraction.total_tax,
                total_net=extraction.total_net,
                raw_ocr_text=raw_text,
                extraction_json=extraction.to_dict(),
                confidence_score=extraction.confidence,
                image_url=str(local_path),
                image_sha256=file_hash,
            )
            db.add(document)
            await db.commit()
            await db.refresh(document)
        
        # Format response
        vendor_text = extraction.vendor_name or "Bilinmeyen Cari"
        date_text = extraction.doc_date.strftime("%d.%m.%Y") if extraction.doc_date else "-"
        amount_text = f"{extraction.total_gross:.2f} ₺" if extraction.total_gross else "-"
        tax_text = f"{extraction.total_tax:.2f} ₺" if extraction.total_tax else "0.00 ₺"
        
        message = f"""
📋 <b>Taslak Oluşturuldu</b>

🏢 <b>Cari:</b> {vendor_text}
📅 <b>Tarih:</b> {date_text}
💰 <b>Tutar:</b> {amount_text}
💸 <b>KDV:</b> {tax_text}

Bu taslağı onaylayın veya düzenleyin.
"""
        
        # Inline keyboard
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Onayla", "callback_data": f"confirm:{document.id}"},
                    {"text": "✏️ Düzenle", "callback_data": f"edit:{document.id}"},
                ],
                [
                    {"text": "❌ İptal", "callback_data": f"cancel:{document.id}"},
                ],
            ]
        }
        
        await bot.send_message(chat_id, message, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await bot.send_message(chat_id, f"❌ Hata: {str(e)}")


async def handle_callback(
    bot: TelegramBot,
    callback: TelegramCallbackQuery,
    user: User,
) -> None:
    """Handle callback query from inline keyboard."""
    data = callback.data or ""
    chat_id = callback.message.chat.id if callback.message else 0
    message_id = callback.message.message_id if callback.message else 0
    
    if data.startswith("confirm:"):
        doc_id = data.split(":")[1]
        async with async_session_maker() as db:
            result = await db.execute(
                select(Document).where(Document.id == uuid.UUID(doc_id))
            )
            document = result.scalar_one_or_none()
            
            if document and document.status == DocumentStatus.DRAFT.value:
                document.status = DocumentStatus.POSTED.value
                document.updated_at = datetime.utcnow()
                await db.commit()
                
                await bot.edit_message_text(
                    chat_id,
                    message_id,
                    "✅ <b>Belge onaylandı!</b>\n\nKayıt deftere eklendi.",
                )
            else:
                await bot.answer_callback_query(
                    callback.id,
                    text="Bu belge zaten işlenmiş.",
                    show_alert=True,
                )
    
    elif data.startswith("cancel:"):
        doc_id = data.split(":")[1]
        async with async_session_maker() as db:
            result = await db.execute(
                select(Document).where(Document.id == uuid.UUID(doc_id))
            )
            document = result.scalar_one_or_none()
            
            if document:
                document.status = DocumentStatus.CANCELLED.value
                document.updated_at = datetime.utcnow()
                await db.commit()
                
                # Show popup alert
                await bot.answer_callback_query(
                    callback.id,
                    text="Fiş iptal edildi ✅",
                    show_alert=True,
                )
                
                await bot.edit_message_text(
                    chat_id,
                    message_id,
                    "❌ <b>Belge iptal edildi.</b>",
                )
    
    elif data.startswith("edit:"):
        await bot.answer_callback_query(
            callback.id,
            text="Düzenleme için web panelini kullanın.",
            show_alert=True,
        )
    
    # Answer the callback
    await bot.answer_callback_query(callback.id)


async def handle_command(
    bot: TelegramBot,
    chat_id: int,
    user: User,
    command: str,
) -> None:
    """Handle bot commands."""
    if command == "/start":
        await bot.send_message(
            chat_id,
            f"""
👋 Merhaba <b>{user.name}</b>!

Ben kişisel muhasebe asistanınım. 

📸 Fiş veya fatura fotoğrafı gönderin, otomatik olarak işleyeyim.

<b>Komutlar:</b>
/report - Bu ayın özeti
/export - Excel raporu al
/help - Yardım
""",
        )
    
    elif command == "/help":
        await bot.send_message(
            chat_id,
            """
<b>📚 Yardım</b>

1️⃣ Fiş/fatura fotoğrafı gönderin
2️⃣ OCR ile otomatik veri çıkarılır
3️⃣ Taslağı onaylayın veya düzenleyin
4️⃣ Raporlarınızı görüntüleyin

<b>Komutlar:</b>
/report - Aylık özet
/export - Excel indirin
/start - Başlangıç mesajı
""",
        )
    
    elif command == "/report":
        async with async_session_maker() as db:
            from sqlalchemy import func
            from app.models.ledger import LedgerEntry
            
            result = await db.execute(
                select(
                    func.sum(LedgerEntry.amount).filter(LedgerEntry.direction == "income"),
                    func.sum(LedgerEntry.amount).filter(LedgerEntry.direction == "expense"),
                    func.count(LedgerEntry.id),
                ).where(LedgerEntry.user_id == user.id)
            )
            row = result.first()
            income = row[0] or 0
            expense = row[1] or 0
            count = row[2] or 0
            balance = income - expense
        
        await bot.send_message(
            chat_id,
            f"""
📊 <b>Bu Ay Özeti</b>

📈 Gelir: {income:,.2f} ₺
📉 Gider: {expense:,.2f} ₺
💰 Bakiye: {balance:,.2f} ₺
📝 İşlem: {count}
""",
        )


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None),
):
    """
    Telegram webhook endpoint.
    Receives updates from Telegram and processes them.
    """
    # Verify secret
    if not verify_telegram_secret(x_telegram_bot_api_secret_token or ""):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret token",
        )
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot not configured",
        )
    
    try:
        body = await request.json()
        update = TelegramUpdate(**body)
        
        # Check for duplicate update (Telegram may retry on timeout)
        if is_duplicate_update(update.update_id):
            logger.info(f"Skipping duplicate update: {update.update_id}")
            return {"ok": True, "skipped": "duplicate"}
        
        if update.message:
            message = update.message
            chat_id = message.chat.id
            
            # Get or create user
            user_name = message.from_user.first_name if message.from_user else "Unknown"
            user = await get_or_create_user(str(chat_id), user_name)
            
            # Handle photo
            if message.photo:
                await process_photo(bot, chat_id, user, message.photo)
            
            # Handle command
            elif message.text and message.text.startswith("/"):
                command = message.text.split()[0].lower()
                await handle_command(bot, chat_id, user, command)
            
            # Handle regular text
            elif message.text:
                await bot.send_message(
                    chat_id,
                    "📸 Lütfen fiş veya fatura fotoğrafı gönderin.",
                )
        
        elif update.callback_query:
            callback = update.callback_query
            user_name = callback.from_user.first_name
            user = await get_or_create_user(str(callback.from_user.id), user_name)
            await handle_callback(bot, callback, user)
        
        return {"ok": True}
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"ok": False, "error": str(e)}


@router.get("/set-webhook")
async def set_webhook(webhook_url: str):
    """
    Set the Telegram webhook URL.
    Call this endpoint once after deployment.
    """
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot not configured",
        )
    
    async with httpx.AsyncClient() as client:
        payload = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query"],
        }
        if settings.telegram_webhook_secret:
            payload["secret_token"] = settings.telegram_webhook_secret
        
        response = await client.post(
            f"{bot.api_base}/setWebhook",
            json=payload,
            timeout=30.0,
        )
        return response.json()
