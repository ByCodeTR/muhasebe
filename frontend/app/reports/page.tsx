'use client'

import { useEffect, useState } from 'react'
import {
    BarChart3,
    TrendingUp,
    TrendingDown,
    Download,
    Calendar,
    Building2,
} from 'lucide-react'
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
} from 'recharts'

interface Summary {
    total_income: number
    total_expense: number
    balance: number
    entry_count: number
    period_start: string
    period_end: string
}

interface VendorBreakdown {
    vendor_id: string
    vendor_name: string
    total_amount: number
    entry_count: number
}

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#ec4899', '#8b5cf6', '#06b6d4']

export default function ReportsPage() {
    const [period, setPeriod] = useState('month')
    const [summary, setSummary] = useState<Summary | null>(null)
    const [vendorData, setVendorData] = useState<VendorBreakdown[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchReports()
    }, [period])

    const fetchReports = async () => {
        setLoading(true)
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

            const [summaryRes, vendorRes] = await Promise.all([
                fetch(`${apiUrl}/reports/summary?period=${period}`),
                fetch(`${apiUrl}/reports/by-vendor?period=${period}`),
            ])

            if (summaryRes.ok) {
                setSummary(await summaryRes.json())
            }
            if (vendorRes.ok) {
                setVendorData(await vendorRes.json())
            }
        } catch (error) {
            console.error('Failed to fetch reports:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleExport = async (format: 'csv' | 'xlsx') => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            const response = await fetch(`${apiUrl}/reports/export/${format}`)
            if (response.ok) {
                const blob = await response.blob()
                const url = window.URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `rapor_${new Date().toISOString().split('T')[0]}.${format}`
                a.click()
                window.URL.revokeObjectURL(url)
            }
        } catch (error) {
            console.error('Export failed:', error)
        }
    }

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('tr-TR', {
            style: 'currency',
            currency: 'TRY',
        }).format(amount)
    }

    const chartData = vendorData.map((v) => ({
        name: v.vendor_name.length > 15 ? v.vendor_name.slice(0, 12) + '...' : v.vendor_name,
        amount: v.total_amount,
    }))

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                        Raporlar
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400 mt-1">
                        Finansal özet ve analizler
                    </p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => handleExport('csv')}
                        className="btn btn-secondary flex items-center gap-2"
                    >
                        <Download className="w-4 h-4" />
                        CSV
                    </button>
                    <button
                        onClick={() => handleExport('xlsx')}
                        className="btn btn-secondary flex items-center gap-2"
                    >
                        <Download className="w-4 h-4" />
                        Excel
                    </button>
                </div>
            </div>

            {/* Period Selector */}
            <div className="card p-4">
                <div className="flex items-center gap-4">
                    <Calendar className="w-5 h-5 text-gray-400" />
                    <div className="flex gap-2">
                        {[
                            { value: 'week', label: 'Bu Hafta' },
                            { value: 'month', label: 'Bu Ay' },
                            { value: 'quarter', label: 'Çeyrek' },
                            { value: 'year', label: 'Bu Yıl' },
                        ].map((p) => (
                            <button
                                key={p.value}
                                onClick={() => setPeriod(p.value)}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${period === p.value
                                        ? 'bg-primary-500 text-white'
                                        : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
                                    }`}
                            >
                                {p.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {loading ? (
                <div className="text-center py-8 text-gray-500">Yükleniyor...</div>
            ) : (
                <>
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="card p-5">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-gray-500">Toplam Gelir</span>
                                <TrendingUp className="w-5 h-5 text-green-500" />
                            </div>
                            <p className="text-2xl font-bold text-green-600">
                                {formatCurrency(summary?.total_income || 0)}
                            </p>
                        </div>

                        <div className="card p-5">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-gray-500">Toplam Gider</span>
                                <TrendingDown className="w-5 h-5 text-red-500" />
                            </div>
                            <p className="text-2xl font-bold text-red-600">
                                {formatCurrency(summary?.total_expense || 0)}
                            </p>
                        </div>

                        <div className="card p-5">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-gray-500">Net Bakiye</span>
                                <BarChart3 className="w-5 h-5 text-primary-500" />
                            </div>
                            <p
                                className={`text-2xl font-bold ${(summary?.balance || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                                    }`}
                            >
                                {formatCurrency(summary?.balance || 0)}
                            </p>
                        </div>

                        <div className="card p-5">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-gray-500">İşlem Sayısı</span>
                                <Building2 className="w-5 h-5 text-gray-500" />
                            </div>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                {summary?.entry_count || 0}
                            </p>
                        </div>
                    </div>

                    {/* Charts Row */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Bar Chart */}
                        <div className="card p-5">
                            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
                                Cariye Göre Harcama
                            </h3>
                            {chartData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart data={chartData}>
                                        <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                                        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                                        <YAxis tick={{ fontSize: 12 }} />
                                        <Tooltip
                                            formatter={(value: number) => formatCurrency(value)}
                                            labelStyle={{ color: '#374151' }}
                                        />
                                        <Bar dataKey="amount" fill="#6366f1" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-[300px] flex items-center justify-center text-gray-500">
                                    Veri yok
                                </div>
                            )}
                        </div>

                        {/* Pie Chart */}
                        <div className="card p-5">
                            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
                                Harcama Dağılımı
                            </h3>
                            {chartData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={300}>
                                    <PieChart>
                                        <Pie
                                            data={chartData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={60}
                                            outerRadius={100}
                                            dataKey="amount"
                                            nameKey="name"
                                            label
                                        >
                                            {chartData.map((_, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <Tooltip formatter={(value: number) => formatCurrency(value)} />
                                    </PieChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-[300px] flex items-center justify-center text-gray-500">
                                    Veri yok
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Vendor Table */}
                    <div className="card overflow-hidden">
                        <div className="p-5 border-b border-gray-200 dark:border-gray-700">
                            <h3 className="font-semibold text-gray-900 dark:text-white">
                                Cariye Göre Detay
                            </h3>
                        </div>
                        <table className="w-full">
                            <thead className="bg-gray-50 dark:bg-gray-800">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Cari
                                    </th>
                                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                                        İşlem
                                    </th>
                                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                                        Toplam
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                {vendorData.length === 0 ? (
                                    <tr>
                                        <td colSpan={3} className="px-4 py-8 text-center text-gray-500">
                                            Bu dönemde işlem yok
                                        </td>
                                    </tr>
                                ) : (
                                    vendorData.map((v) => (
                                        <tr key={v.vendor_id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                                            <td className="px-4 py-3 text-gray-900 dark:text-white font-medium">
                                                {v.vendor_name}
                                            </td>
                                            <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-400">
                                                {v.entry_count}
                                            </td>
                                            <td className="px-4 py-3 text-right font-medium text-gray-900 dark:text-white">
                                                {formatCurrency(v.total_amount)}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </div>
    )
}
