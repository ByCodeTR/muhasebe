'use client'

import { useEffect, useState } from 'react'
import { ArrowUpRight, ArrowDownRight } from 'lucide-react'

interface Transaction {
    id: string
    vendor_name: string
    amount: number
    direction: 'expense' | 'income'
    entry_date: string
}

export default function RecentTransactions() {
    const [transactions, setTransactions] = useState<Transaction[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchTransactions()
    }, [])

    const fetchTransactions = async () => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            const response = await fetch(`${apiUrl}/ledger/entries?limit=5`)
            if (response.ok) {
                const data = await response.json()
                setTransactions(data)
            }
        } catch (error) {
            console.error('Failed to fetch transactions:', error)
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

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString('tr-TR', {
            day: 'numeric',
            month: 'short',
        })
    }

    // Demo data while loading
    const demoTransactions: Transaction[] = [
        { id: '1', vendor_name: 'Migros', amount: 234.50, direction: 'expense', entry_date: '2026-02-06' },
        { id: '2', vendor_name: 'BIM', amount: 89.90, direction: 'expense', entry_date: '2026-02-05' },
        { id: '3', vendor_name: 'Freelance Ödeme', amount: 1500.00, direction: 'income', entry_date: '2026-02-04' },
        { id: '4', vendor_name: 'Vodafone', amount: 149.00, direction: 'expense', entry_date: '2026-02-03' },
        { id: '5', vendor_name: 'Shell', amount: 800.00, direction: 'expense', entry_date: '2026-02-02' },
    ]

    const displayTransactions = transactions.length > 0 ? transactions : demoTransactions

    return (
        <div className="card p-5 h-full">
            <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                    Son İşlemler
                </h3>
                <button className="text-sm text-primary-600 hover:text-primary-700">
                    Tümünü Gör
                </button>
            </div>

            <div className="space-y-3">
                {displayTransactions.map((tx) => (
                    <div
                        key={tx.id}
                        className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0"
                    >
                        <div className="flex items-center gap-3">
                            <div
                                className={`w-8 h-8 rounded-full flex items-center justify-center ${tx.direction === 'income'
                                        ? 'bg-green-100 dark:bg-green-900/30'
                                        : 'bg-red-100 dark:bg-red-900/30'
                                    }`}
                            >
                                {tx.direction === 'income' ? (
                                    <ArrowUpRight className="w-4 h-4 text-green-600" />
                                ) : (
                                    <ArrowDownRight className="w-4 h-4 text-red-600" />
                                )}
                            </div>
                            <div>
                                <p className="text-sm font-medium text-gray-900 dark:text-white">
                                    {tx.vendor_name || 'Bilinmeyen'}
                                </p>
                                <p className="text-xs text-gray-500">
                                    {formatDate(tx.entry_date)}
                                </p>
                            </div>
                        </div>
                        <p
                            className={`text-sm font-semibold ${tx.direction === 'income'
                                    ? 'text-green-600'
                                    : 'text-red-600'
                                }`}
                        >
                            {tx.direction === 'income' ? '+' : '-'}
                            {formatCurrency(tx.amount)}
                        </p>
                    </div>
                ))}
            </div>
        </div>
    )
}
