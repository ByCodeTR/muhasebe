'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Plus, Search, Building2, Phone, MapPin, Edit2 } from 'lucide-react'

interface Vendor {
    id: string
    display_name: string
    vkn: string | null
    tckn: string | null
    address: string | null
    phone: string | null
    created_at: string
}

export default function VendorsPage() {
    const [vendors, setVendors] = useState<Vendor[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [showModal, setShowModal] = useState(false)
    const [newVendor, setNewVendor] = useState({
        display_name: '',
        vkn: '',
        phone: '',
        address: '',
    })

    useEffect(() => {
        fetchVendors()
    }, [])

    const fetchVendors = async () => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            const response = await fetch(`${apiUrl}/vendors/`)
            if (response.ok) {
                const data = await response.json()
                setVendors(data)
            }
        } catch (error) {
            console.error('Failed to fetch vendors:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleCreateVendor = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            const response = await fetch(`${apiUrl}/vendors/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newVendor),
            })
            if (response.ok) {
                setShowModal(false)
                setNewVendor({ display_name: '', vkn: '', phone: '', address: '' })
                fetchVendors()
            }
        } catch (error) {
            console.error('Failed to create vendor:', error)
        }
    }

    const filteredVendors = vendors.filter((vendor) => {
        if (!searchQuery) return true
        const query = searchQuery.toLowerCase()
        return (
            vendor.display_name.toLowerCase().includes(query) ||
            vendor.vkn?.includes(query)
        )
    })

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                        Cariler
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400 mt-1">
                        Satıcı ve tedarikçi yönetimi
                    </p>
                </div>
                <button
                    onClick={() => setShowModal(true)}
                    className="btn btn-primary flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    Yeni Cari
                </button>
            </div>

            {/* Search */}
            <div className="card p-4">
                <div className="relative max-w-md">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Cari adı veya VKN ile ara..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="input pl-10"
                    />
                </div>
            </div>

            {/* Vendors Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {loading ? (
                    <div className="col-span-full text-center py-8 text-gray-500">
                        Yükleniyor...
                    </div>
                ) : filteredVendors.length === 0 ? (
                    <div className="col-span-full text-center py-8 text-gray-500">
                        <Building2 className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                        <p>Henüz cari yok</p>
                    </div>
                ) : (
                    filteredVendors.map((vendor) => (
                        <div key={vendor.id} className="card p-5 hover:shadow-md transition-shadow">
                            <div className="flex items-start justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                                        <Building2 className="w-5 h-5 text-primary-600" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-gray-900 dark:text-white">
                                            {vendor.display_name}
                                        </h3>
                                        {vendor.vkn && (
                                            <p className="text-sm text-gray-500">VKN: {vendor.vkn}</p>
                                        )}
                                    </div>
                                </div>
                                <button className="p-1 text-gray-400 hover:text-gray-600">
                                    <Edit2 className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="mt-4 space-y-2 text-sm text-gray-600 dark:text-gray-400">
                                {vendor.phone && (
                                    <div className="flex items-center gap-2">
                                        <Phone className="w-4 h-4" />
                                        {vendor.phone}
                                    </div>
                                )}
                                {vendor.address && (
                                    <div className="flex items-start gap-2">
                                        <MapPin className="w-4 h-4 mt-0.5" />
                                        <span className="line-clamp-2">{vendor.address}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Create Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card w-full max-w-md p-6 m-4">
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                            Yeni Cari Ekle
                        </h2>
                        <form onSubmit={handleCreateVendor} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Cari Adı *
                                </label>
                                <input
                                    type="text"
                                    required
                                    value={newVendor.display_name}
                                    onChange={(e) =>
                                        setNewVendor({ ...newVendor, display_name: e.target.value })
                                    }
                                    className="input"
                                    placeholder="Örn: Migros"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    VKN (Vergi Kimlik No)
                                </label>
                                <input
                                    type="text"
                                    value={newVendor.vkn}
                                    onChange={(e) =>
                                        setNewVendor({ ...newVendor, vkn: e.target.value })
                                    }
                                    className="input"
                                    placeholder="10-11 haneli"
                                    maxLength={11}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Telefon
                                </label>
                                <input
                                    type="tel"
                                    value={newVendor.phone}
                                    onChange={(e) =>
                                        setNewVendor({ ...newVendor, phone: e.target.value })
                                    }
                                    className="input"
                                    placeholder="0500 000 00 00"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Adres
                                </label>
                                <textarea
                                    value={newVendor.address}
                                    onChange={(e) =>
                                        setNewVendor({ ...newVendor, address: e.target.value })
                                    }
                                    className="input"
                                    rows={2}
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button type="submit" className="btn btn-primary flex-1">
                                    Kaydet
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="btn btn-secondary flex-1"
                                >
                                    İptal
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
