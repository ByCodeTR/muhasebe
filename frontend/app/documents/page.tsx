'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
    Plus,
    Search,
    FileImage,
    CheckCircle,
    Clock,
    XCircle,
    Filter,
    Download,
} from 'lucide-react'

interface Document {
    id: string
    status: 'draft' | 'posted' | 'cancelled'
    doc_type: string
    doc_date: string | null
    total_gross: number | null
    total_tax: number | null
    vendor_name: string | null
    confidence_score: number | null
    created_at: string
}

export default function DocumentsPage() {
    const [documents, setDocuments] = useState<Document[]>([])
    const [loading, setLoading] = useState(true)
    const [statusFilter, setStatusFilter] = useState<string>('')
    const [searchQuery, setSearchQuery] = useState('')

    useEffect(() => {
        fetchDocuments()
    }, [statusFilter])

    const fetchDocuments = async () => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            let url = `${apiUrl}/documents/?limit=50`
            if (statusFilter) {
                url += `&status_filter=${statusFilter}`
            }
            const response = await fetch(url)
            if (response.ok) {
                const data = await response.json()
                setDocuments(data)
            }
        } catch (error) {
            console.error('Failed to fetch documents:', error)
        } finally {
            setLoading(false)
        }
    }

    const formatCurrency = (amount: number | null) => {
        if (amount === null) return '-'
        return new Intl.NumberFormat('tr-TR', {
            style: 'currency',
            currency: 'TRY',
        }).format(amount)
    }

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return '-'
        return new Date(dateStr).toLocaleDateString('tr-TR')
    }

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'draft':
                return (
                    <span className="badge badge-warning flex items-center gap-1">
                        <Clock className="w-3 h-3" /> Taslak
                    </span>
                )
            case 'posted':
                return (
                    <span className="badge badge-success flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" /> Onaylı
                    </span>
                )
            case 'cancelled':
                return (
                    <span className="badge badge-danger flex items-center gap-1">
                        <XCircle className="w-3 h-3" /> İptal
                    </span>
                )
            default:
                return <span className="badge">{status}</span>
        }
    }

    const filteredDocuments = documents.filter((doc) => {
        if (!searchQuery) return true
        const query = searchQuery.toLowerCase()
        return (
            doc.vendor_name?.toLowerCase().includes(query) ||
            doc.doc_type?.toLowerCase().includes(query)
        )
    })

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                        Belgeler
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400 mt-1">
                        Fiş ve faturaları yönetin
                    </p>
                </div>
                <Link
                    href="/documents/upload"
                    className="btn btn-primary flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    Yeni Yükle
                </Link>
            </div>

            {/* Filters */}
            <div className="card p-4">
                <div className="flex flex-wrap gap-4">
                    {/* Search */}
                    <div className="flex-1 min-w-[200px]">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Belge veya cari ara..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="input pl-10"
                            />
                        </div>
                    </div>

                    {/* Status Filter */}
                    <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-gray-400" />
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="input w-40"
                        >
                            <option value="">Tümü</option>
                            <option value="draft">Taslaklar</option>
                            <option value="posted">Onaylılar</option>
                            <option value="cancelled">İptaller</option>
                        </select>
                    </div>

                    {/* Export */}
                    <button className="btn btn-secondary flex items-center gap-2">
                        <Download className="w-4 h-4" />
                        Dışa Aktar
                    </button>
                </div>
            </div>

            {/* Documents Table */}
            <div className="card overflow-hidden">
                <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-gray-800">
                        <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Durum
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Cari
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Tarih
                            </th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Tutar
                            </th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                KDV
                            </th>
                            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Güven
                            </th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                İşlem
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                        {loading ? (
                            <tr>
                                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                                    Yükleniyor...
                                </td>
                            </tr>
                        ) : filteredDocuments.length === 0 ? (
                            <tr>
                                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                                    <div className="flex flex-col items-center gap-2">
                                        <FileImage className="w-12 h-12 text-gray-300" />
                                        <p>Henüz belge yok</p>
                                        <Link
                                            href="/documents/upload"
                                            className="text-primary-600 hover:text-primary-700"
                                        >
                                            İlk belgenizi yükleyin
                                        </Link>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            filteredDocuments.map((doc) => (
                                <tr
                                    key={doc.id}
                                    className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                                    onClick={() => (window.location.href = `/documents/${doc.id}`)}
                                >
                                    <td className="px-4 py-3">{getStatusBadge(doc.status)}</td>
                                    <td className="px-4 py-3 text-gray-900 dark:text-white">
                                        {doc.vendor_name || (
                                            <span className="text-gray-400 italic">Bilinmeyen</span>
                                        )}
                                    </td>
                                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                                        {formatDate(doc.doc_date)}
                                    </td>
                                    <td className="px-4 py-3 text-right font-medium text-gray-900 dark:text-white">
                                        {formatCurrency(doc.total_gross)}
                                    </td>
                                    <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-400">
                                        {formatCurrency(doc.total_tax)}
                                    </td>
                                    <td className="px-4 py-3 text-center">
                                        {doc.confidence_score !== null && (
                                            <span
                                                className={`text-sm font-medium ${doc.confidence_score >= 70
                                                        ? 'text-green-600'
                                                        : doc.confidence_score >= 40
                                                            ? 'text-yellow-600'
                                                            : 'text-red-600'
                                                    }`}
                                            >
                                                %{Math.round(doc.confidence_score)}
                                            </span>
                                        )}
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <Link
                                            href={`/documents/${doc.id}`}
                                            className="text-primary-600 hover:text-primary-700 text-sm"
                                            onClick={(e) => e.stopPropagation()}
                                        >
                                            Görüntüle
                                        </Link>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
