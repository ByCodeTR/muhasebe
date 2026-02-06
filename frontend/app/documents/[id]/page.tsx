'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import {
    ArrowLeft,
    Check,
    X,
    Edit2,
    Calendar,
    Building2,
    FileText,
    AlertCircle,
} from 'lucide-react'
import api from '@/lib/api'

interface Document {
    id: string
    status: string
    doc_type: string
    doc_date: string | null
    doc_no: string | null
    vendor_id: string | null
    total_gross: number | null
    total_tax: number | null
    total_net: number | null
    currency: string
    raw_ocr_text: string | null
    confidence_score: number | null
    image_url: string | null
    created_at: string
}

interface Vendor {
    id: string
    display_name: string
}

export default function DocumentDetailPage() {
    const params = useParams()
    const router = useRouter()
    const documentId = params.id as string

    const [document, setDocument] = useState<Document | null>(null)
    const [vendors, setVendors] = useState<Vendor[]>([])
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Editable form state
    const [formData, setFormData] = useState({
        vendor_id: '',
        doc_date: '',
        total_gross: '',
        total_tax: '',
    })

    useEffect(() => {
        fetchDocument()
        fetchVendors()
    }, [documentId])

    const fetchDocument = async () => {
        try {
            const data = await api.getDocument(documentId)
            setDocument(data)
            setFormData({
                vendor_id: data.vendor_id || '',
                doc_date: data.doc_date ? data.doc_date.split('T')[0] : '',
                total_gross: data.total_gross?.toString() || '',
                total_tax: data.total_tax?.toString() || '',
            })
        } catch (err: any) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const fetchVendors = async () => {
        try {
            const data = await api.getVendors({ limit: 100 })
            setVendors(data)
        } catch (err) {
            console.error('Failed to load vendors:', err)
        }
    }

    const handleConfirm = async () => {
        if (!document) return
        setSaving(true)
        try {
            await api.confirmDocument(documentId, {
                vendor_id: formData.vendor_id || null,
                doc_date: formData.doc_date || null,
                total_gross: formData.total_gross ? parseFloat(formData.total_gross) : null,
                total_tax: formData.total_tax ? parseFloat(formData.total_tax) : null,
            })
            router.push('/documents')
        } catch (err: any) {
            setError(err.message)
        } finally {
            setSaving(false)
        }
    }

    const formatCurrency = (amount: number | null) => {
        if (amount === null) return '-'
        return new Intl.NumberFormat('tr-TR', {
            style: 'currency',
            currency: 'TRY',
        }).format(amount)
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-gray-500">Yükleniyor...</div>
            </div>
        )
    }

    if (error || !document) {
        return (
            <div className="text-center py-12">
                <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
                <p className="text-red-600">{error || 'Belge bulunamadı'}</p>
                <Link href="/documents" className="text-primary-600 hover:underline mt-4 block">
                    Belgelere Dön
                </Link>
            </div>
        )
    }

    const isDraft = document.status === 'draft'

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Link
                    href="/documents"
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                >
                    <ArrowLeft className="w-5 h-5" />
                </Link>
                <div className="flex-1">
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                        {isDraft ? 'Taslak Onayla' : 'Belge Detayı'}
                    </h1>
                    <p className="text-gray-500 text-sm">
                        {document.doc_no || `ID: ${document.id.slice(0, 8)}`}
                    </p>
                </div>
                {document.confidence_score !== null && (
                    <div
                        className={`px-3 py-1 rounded-full text-sm font-medium ${document.confidence_score >= 70
                                ? 'bg-green-100 text-green-700'
                                : document.confidence_score >= 40
                                    ? 'bg-yellow-100 text-yellow-700'
                                    : 'bg-red-100 text-red-700'
                            }`}
                    >
                        OCR: %{Math.round(document.confidence_score)}
                    </div>
                )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Image Preview */}
                <div className="card overflow-hidden">
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                            Görsel
                        </span>
                    </div>
                    <div className="aspect-[3/4] bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
                        {document.image_url ? (
                            <img
                                src={document.image_url}
                                alt="Document"
                                className="max-w-full max-h-full object-contain"
                            />
                        ) : (
                            <FileText className="w-16 h-16 text-gray-300" />
                        )}
                    </div>
                </div>

                {/* Form */}
                <div className="space-y-4">
                    {/* Vendor */}
                    <div className="card p-4">
                        <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            <Building2 className="w-4 h-4" />
                            Cari
                        </label>
                        {isDraft ? (
                            <select
                                value={formData.vendor_id}
                                onChange={(e) => setFormData({ ...formData, vendor_id: e.target.value })}
                                className="input"
                            >
                                <option value="">Cari Seçin</option>
                                {vendors.map((v) => (
                                    <option key={v.id} value={v.id}>
                                        {v.display_name}
                                    </option>
                                ))}
                            </select>
                        ) : (
                            <p className="text-gray-900 dark:text-white">
                                {vendors.find((v) => v.id === document.vendor_id)?.display_name || '-'}
                            </p>
                        )}
                    </div>

                    {/* Date */}
                    <div className="card p-4">
                        <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            <Calendar className="w-4 h-4" />
                            Tarih
                        </label>
                        {isDraft ? (
                            <input
                                type="date"
                                value={formData.doc_date}
                                onChange={(e) => setFormData({ ...formData, doc_date: e.target.value })}
                                className="input"
                            />
                        ) : (
                            <p className="text-gray-900 dark:text-white">
                                {document.doc_date
                                    ? new Date(document.doc_date).toLocaleDateString('tr-TR')
                                    : '-'}
                            </p>
                        )}
                    </div>

                    {/* Amounts */}
                    <div className="card p-4 space-y-4">
                        <div>
                            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                                Brüt Tutar
                            </label>
                            {isDraft ? (
                                <input
                                    type="number"
                                    step="0.01"
                                    value={formData.total_gross}
                                    onChange={(e) =>
                                        setFormData({ ...formData, total_gross: e.target.value })
                                    }
                                    className="input"
                                    placeholder="0.00"
                                />
                            ) : (
                                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                                    {formatCurrency(document.total_gross)}
                                </p>
                            )}
                        </div>

                        <div>
                            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                                KDV
                            </label>
                            {isDraft ? (
                                <input
                                    type="number"
                                    step="0.01"
                                    value={formData.total_tax}
                                    onChange={(e) =>
                                        setFormData({ ...formData, total_tax: e.target.value })
                                    }
                                    className="input"
                                    placeholder="0.00"
                                />
                            ) : (
                                <p className="text-gray-600 dark:text-gray-400">
                                    {formatCurrency(document.total_tax)}
                                </p>
                            )}
                        </div>
                    </div>

                    {/* OCR Text */}
                    {document.raw_ocr_text && (
                        <div className="card p-4">
                            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                                OCR Metni
                            </label>
                            <pre className="text-xs text-gray-600 dark:text-gray-400 whitespace-pre-wrap bg-gray-50 dark:bg-gray-900 p-3 rounded-lg max-h-40 overflow-auto">
                                {document.raw_ocr_text}
                            </pre>
                        </div>
                    )}

                    {/* Actions */}
                    {isDraft && (
                        <div className="flex gap-3">
                            <button
                                onClick={handleConfirm}
                                disabled={saving}
                                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
                            >
                                <Check className="w-4 h-4" />
                                {saving ? 'Kaydediliyor...' : 'Onayla'}
                            </button>
                            <button
                                onClick={() => router.push('/documents')}
                                className="btn btn-secondary flex items-center justify-center gap-2"
                            >
                                <X className="w-4 h-4" />
                                İptal
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
