"""
Tests for health and document endpoints.
"""
import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check returns OK."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns welcome message."""
        response = await client.get("/")
        assert response.status_code == 200


class TestDocumentsEndpoint:
    """Tests for document endpoints."""

    @pytest.mark.asyncio
    async def test_list_documents_empty(self, client: AsyncClient, test_user):
        """Test listing documents when empty."""
        response = await client.get("/documents/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_drafts_empty(self, client: AsyncClient, test_user):
        """Test listing drafts when empty."""
        response = await client.get("/documents/drafts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, client: AsyncClient):
        """Test getting non-existent document returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000099"
        response = await client.get(f"/documents/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, client: AsyncClient):
        """Test uploading invalid file type is rejected."""
        files = {"file": ("test.txt", b"hello world", "text/plain")}
        response = await client.post("/documents/upload", files=files)
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"].lower()


class TestVendorsEndpoint:
    """Tests for vendor endpoints."""

    @pytest.mark.asyncio
    async def test_list_vendors_empty(self, client: AsyncClient, test_user):
        """Test listing vendors when empty (except test vendor)."""
        response = await client.get("/vendors/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_vendor(self, client: AsyncClient, test_user):
        """Test creating a new vendor."""
        vendor_data = {
            "display_name": "New Vendor",
            "vkn": "9876543210",
        }
        response = await client.post("/vendors/", json=vendor_data)
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "New Vendor"
        assert data["vkn"] == "9876543210"

    @pytest.mark.asyncio
    async def test_search_vendors(self, client: AsyncClient, test_vendor):
        """Test searching vendors."""
        response = await client.get("/vendors/search", params={"q": "test"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestLedgerEndpoint:
    """Tests for ledger endpoints."""

    @pytest.mark.asyncio
    async def test_list_entries_empty(self, client: AsyncClient, test_user):
        """Test listing ledger entries when empty."""
        response = await client.get("/ledger/entries")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_categories(self, client: AsyncClient, test_categories):
        """Test listing categories."""
        response = await client.get("/ledger/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2


class TestReportsEndpoint:
    """Tests for report endpoints."""

    @pytest.mark.asyncio
    async def test_get_summary(self, client: AsyncClient, test_user):
        """Test getting report summary."""
        response = await client.get("/reports/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data
        assert "total_expense" in data
        assert "balance" in data

    @pytest.mark.asyncio
    async def test_get_by_vendor(self, client: AsyncClient, test_user):
        """Test getting vendor breakdown."""
        response = await client.get("/reports/by-vendor")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_export_csv(self, client: AsyncClient, test_user):
        """Test CSV export."""
        response = await client.get("/reports/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
