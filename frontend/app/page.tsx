'use client'

import { useEffect, useState } from 'react'
import {
    TrendingUp,
    TrendingDown,
    Receipt,
    Users,
    ArrowUpRight,
    ArrowDownRight
} from 'lucide-react'
import StatsCard from '@/components/dashboard/StatsCard'
import RecentTransactions from '@/components/dashboard/RecentTransactions'
import ExpenseChart from '@/components/dashboard/ExpenseChart'

interface DashboardStats {
    totalIncome: number
    totalExpense: number
    netBalance: number
    transactionCount: number
    taxTotal: number
}

export default function Dashboard() {
    const [stats, setStats] = useState<DashboardStats>({
        totalIncome: 0,
        totalExpense: 0,
        netBalance: 0,
        transactionCount: 0,
        taxTotal: 0,
    })
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchStats()
    }, [])

    const fetchStats = async () => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            const response = await fetch(`${apiUrl}/reports/summary?period=month`)
            if (response.ok) {
                const data = await response.json()
                setStats({
                    totalIncome: data.total_income,
                    totalExpense: data.total_expense,
                    netBalance: data.net,
                    transactionCount: data.transaction_count,
                    taxTotal: data.tax_total,
                })
            }
        } catch (error) {
            console.error('Failed to fetch stats:', error)
        } finally {
            setLoading(false)
        }
    }

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('tr-TR', {
            style: 'currency',
            currency: 'TRY',
        }).format(amount)
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                        Dashboard
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400 mt-1">
                        Bu ayki finansal özet
                    </p>
                </div>
                <button className="btn btn-primary flex items-center gap-2">
                    <Receipt className="w-4 h-4" />
                    Fiş Yükle
                </button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatsCard
                    title="Toplam Gelir"
                    value={formatCurrency(stats.totalIncome)}
                    icon={<TrendingUp className="w-5 h-5 text-green-600" />}
                    trend={{ value: 12, isPositive: true }}
                    color="green"
                />
                <StatsCard
                    title="Toplam Gider"
                    value={formatCurrency(stats.totalExpense)}
                    icon={<TrendingDown className="w-5 h-5 text-red-600" />}
                    trend={{ value: 8, isPositive: false }}
                    color="red"
                />
                <StatsCard
                    title="Net Bakiye"
                    value={formatCurrency(stats.netBalance)}
                    icon={<Receipt className="w-5 h-5 text-blue-600" />}
                    color="blue"
                />
                <StatsCard
                    title="İşlem Sayısı"
                    value={stats.transactionCount.toString()}
                    icon={<Users className="w-5 h-5 text-purple-600" />}
                    subtitle={`KDV: ${formatCurrency(stats.taxTotal)}`}
                    color="purple"
                />
            </div>

            {/* Charts and Recent */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                    <ExpenseChart />
                </div>
                <div>
                    <RecentTransactions />
                </div>
            </div>
        </div>
    )
}
