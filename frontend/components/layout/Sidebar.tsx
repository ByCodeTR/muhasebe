'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
    LayoutDashboard,
    Receipt,
    Users,
    FolderOpen,
    BarChart3,
    Settings,
    Upload,
    Bot
} from 'lucide-react'
import clsx from 'clsx'

const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Belgeler', href: '/documents', icon: Receipt },
    { name: 'Cariler', href: '/vendors', icon: Users },
    { name: 'Kategoriler', href: '/categories', icon: FolderOpen },
    { name: 'Raporlar', href: '/reports', icon: BarChart3 },
    { name: 'Ayarlar', href: '/settings', icon: Settings },
]

export default function Sidebar() {
    const pathname = usePathname()

    return (
        <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
            {/* Logo */}
            <div className="h-16 flex items-center px-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
                        <Receipt className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h1 className="font-bold text-gray-900 dark:text-white">Muhasebe</h1>
                        <p className="text-xs text-gray-500">Kişisel Finans</p>
                    </div>
                </div>
            </div>

            {/* Upload Button */}
            <div className="p-4">
                <Link
                    href="/documents/upload"
                    className="w-full btn btn-primary flex items-center justify-center gap-2"
                >
                    <Upload className="w-4 h-4" />
                    Fiş Yükle
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 space-y-1">
                {navigation.map((item) => {
                    const isActive = pathname === item.href
                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={clsx(
                                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                                isActive
                                    ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                            )}
                        >
                            <item.icon className="w-5 h-5" />
                            {item.name}
                        </Link>
                    )
                })}
            </nav>

            {/* Telegram Bot Status */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                    <Bot className="w-5 h-5 text-blue-500" />
                    <div className="flex-1">
                        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Telegram Bot
                        </p>
                        <p className="text-xs text-gray-500">Bağlı değil</p>
                    </div>
                    <div className="w-2 h-2 rounded-full bg-gray-400" />
                </div>
            </div>
        </aside>
    )
}
