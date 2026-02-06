'use client'

import { useEffect, useState } from 'react'
import { Plus, Tag, Edit2, Trash2 } from 'lucide-react'

interface Category {
    id: string
    name: string
    icon: string | null
    color: string | null
    parent_id: string | null
    created_at: string
}

export default function CategoriesPage() {
    const [categories, setCategories] = useState<Category[]>([])
    const [loading, setLoading] = useState(true)
    const [showModal, setShowModal] = useState(false)
    const [newCategory, setNewCategory] = useState({
        name: '',
        icon: '📦',
        color: '#6366f1',
    })

    const icons = ['🛒', '🍽️', '🚗', '📄', '🏥', '🎬', '👕', '📱', '🏠', '📦', '💰', '✈️', '📚', '🎮']
    const colors = [
        '#22c55e', '#f59e0b', '#3b82f6', '#ef4444', '#ec4899',
        '#8b5cf6', '#06b6d4', '#64748b', '#84cc16', '#f97316',
    ]

    useEffect(() => {
        fetchCategories()
    }, [])

    const fetchCategories = async () => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            const response = await fetch(`${apiUrl}/ledger/categories`)
            if (response.ok) {
                const data = await response.json()
                setCategories(data)
            }
        } catch (error) {
            console.error('Failed to fetch categories:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            const response = await fetch(`${apiUrl}/ledger/categories`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newCategory),
            })
            if (response.ok) {
                setShowModal(false)
                setNewCategory({ name: '', icon: '📦', color: '#6366f1' })
                fetchCategories()
            }
        } catch (error) {
            console.error('Failed to create category:', error)
        }
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                        Kategoriler
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400 mt-1">
                        Harcama ve gelir kategorilerini yönetin
                    </p>
                </div>
                <button
                    onClick={() => setShowModal(true)}
                    className="btn btn-primary flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    Yeni Kategori
                </button>
            </div>

            {/* Categories Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {loading ? (
                    <div className="col-span-full text-center py-8 text-gray-500">
                        Yükleniyor...
                    </div>
                ) : categories.length === 0 ? (
                    <div className="col-span-full text-center py-8 text-gray-500">
                        <Tag className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                        <p>Henüz kategori yok</p>
                    </div>
                ) : (
                    categories.map((cat) => (
                        <div
                            key={cat.id}
                            className="card p-4 hover:shadow-md transition-shadow group"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div
                                        className="w-10 h-10 rounded-lg flex items-center justify-center text-xl"
                                        style={{ backgroundColor: cat.color || '#6366f1' + '20' }}
                                    >
                                        {cat.icon || '📦'}
                                    </div>
                                    <span className="font-medium text-gray-900 dark:text-white">
                                        {cat.name}
                                    </span>
                                </div>
                                <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                                    <button className="p-1 text-gray-400 hover:text-gray-600">
                                        <Edit2 className="w-4 h-4" />
                                    </button>
                                    <button className="p-1 text-gray-400 hover:text-red-500">
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
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
                            Yeni Kategori
                        </h2>
                        <form onSubmit={handleCreate} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Kategori Adı *
                                </label>
                                <input
                                    type="text"
                                    required
                                    value={newCategory.name}
                                    onChange={(e) =>
                                        setNewCategory({ ...newCategory, name: e.target.value })
                                    }
                                    className="input"
                                    placeholder="Örn: Market"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    İkon
                                </label>
                                <div className="flex flex-wrap gap-2">
                                    {icons.map((icon) => (
                                        <button
                                            key={icon}
                                            type="button"
                                            onClick={() => setNewCategory({ ...newCategory, icon })}
                                            className={`w-10 h-10 rounded-lg text-xl flex items-center justify-center border-2 transition-colors ${newCategory.icon === icon
                                                    ? 'border-primary-500 bg-primary-50'
                                                    : 'border-gray-200 hover:border-gray-300'
                                                }`}
                                        >
                                            {icon}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    Renk
                                </label>
                                <div className="flex flex-wrap gap-2">
                                    {colors.map((color) => (
                                        <button
                                            key={color}
                                            type="button"
                                            onClick={() => setNewCategory({ ...newCategory, color })}
                                            className={`w-8 h-8 rounded-full border-2 transition-all ${newCategory.color === color
                                                    ? 'border-gray-900 scale-110'
                                                    : 'border-transparent'
                                                }`}
                                            style={{ backgroundColor: color }}
                                        />
                                    ))}
                                </div>
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
