import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Sidebar from '@/components/layout/Sidebar'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
    title: 'Muhasebe - Kişisel Finans Takibi',
    description: 'Fiş ve fatura takibi, OCR ile veri çıkarma, raporlama',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="tr">
            <body className={inter.className}>
                <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
                    <Sidebar />
                    <main className="flex-1 overflow-auto">
                        <div className="p-6">
                            {children}
                        </div>
                    </main>
                </div>
            </body>
        </html>
    )
}
