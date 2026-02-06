'use client'

import { useEffect, useState } from 'react'
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from 'recharts'

interface ChartData {
    name: string
    gelir: number
    gider: number
}

export default function ExpenseChart() {
    const [data, setData] = useState<ChartData[]>([])

    useEffect(() => {
        // Demo data - will be replaced with API call
        const demoData: ChartData[] = [
            { name: 'Oca', gelir: 4000, gider: 2400 },
            { name: 'Şub', gelir: 3000, gider: 1398 },
            { name: 'Mar', gelir: 2000, gider: 9800 },
            { name: 'Nis', gelir: 2780, gider: 3908 },
            { name: 'May', gelir: 1890, gider: 4800 },
            { name: 'Haz', gelir: 2390, gider: 3800 },
        ]
        setData(demoData)
    }, [])

    return (
        <div className="card p-5 h-[400px]">
            <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                    Gelir / Gider Grafiği
                </h3>
                <select className="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-800">
                    <option value="6m">Son 6 Ay</option>
                    <option value="1y">Son 1 Yıl</option>
                    <option value="all">Tümü</option>
                </select>
            </div>

            <div className="h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis
                            dataKey="name"
                            tick={{ fill: '#6b7280', fontSize: 12 }}
                            axisLine={{ stroke: '#e5e7eb' }}
                        />
                        <YAxis
                            tick={{ fill: '#6b7280', fontSize: 12 }}
                            axisLine={{ stroke: '#e5e7eb' }}
                            tickFormatter={(value) => `₺${value / 1000}k`}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1f2937',
                                border: 'none',
                                borderRadius: '8px',
                                color: '#fff',
                            }}
                            formatter={(value: number) => [
                                `₺${value.toLocaleString('tr-TR')}`,
                            ]}
                        />
                        <Legend />
                        <Bar
                            dataKey="gelir"
                            fill="#22c55e"
                            radius={[4, 4, 0, 0]}
                            name="Gelir"
                        />
                        <Bar
                            dataKey="gider"
                            fill="#ef4444"
                            radius={[4, 4, 0, 0]}
                            name="Gider"
                        />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}
