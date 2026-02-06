import { ArrowUpRight, ArrowDownRight } from 'lucide-react'
import clsx from 'clsx'

interface StatsCardProps {
    title: string
    value: string
    icon: React.ReactNode
    trend?: {
        value: number
        isPositive: boolean
    }
    subtitle?: string
    color: 'green' | 'red' | 'blue' | 'purple' | 'orange'
}

const colorClasses = {
    green: 'bg-green-50 dark:bg-green-900/20',
    red: 'bg-red-50 dark:bg-red-900/20',
    blue: 'bg-blue-50 dark:bg-blue-900/20',
    purple: 'bg-purple-50 dark:bg-purple-900/20',
    orange: 'bg-orange-50 dark:bg-orange-900/20',
}

export default function StatsCard({
    title,
    value,
    icon,
    trend,
    subtitle,
    color,
}: StatsCardProps) {
    return (
        <div className="card p-5">
            <div className="flex items-start justify-between">
                <div className={clsx('p-2 rounded-lg', colorClasses[color])}>
                    {icon}
                </div>
                {trend && (
                    <div
                        className={clsx(
                            'flex items-center gap-1 text-sm font-medium',
                            trend.isPositive ? 'text-green-600' : 'text-red-600'
                        )}
                    >
                        {trend.isPositive ? (
                            <ArrowUpRight className="w-4 h-4" />
                        ) : (
                            <ArrowDownRight className="w-4 h-4" />
                        )}
                        {trend.value}%
                    </div>
                )}
            </div>
            <div className="mt-4">
                <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
                <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-white">
                    {value}
                </p>
                {subtitle && (
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                        {subtitle}
                    </p>
                )}
            </div>
        </div>
    )
}
