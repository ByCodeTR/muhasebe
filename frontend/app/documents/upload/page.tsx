'use client'

import { useState, useCallback } from 'react'
import { Upload, FileImage, X, Check, Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'

export default function UploadPage() {
    const router = useRouter()
    const [file, setFile] = useState<File | null>(null)
    const [preview, setPreview] = useState<string | null>(null)
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [dragActive, setDragActive] = useState(false)

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true)
        } else if (e.type === 'dragleave') {
            setDragActive(false)
        }
    }, [])

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0])
        }
    }, [])

    const handleFile = (selectedFile: File) => {
        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
        if (!allowedTypes.includes(selectedFile.type)) {
            setError('Sadece JPEG, PNG, WebP veya PDF dosyaları kabul edilir.')
            return
        }

        // Validate file size (10MB)
        if (selectedFile.size > 10 * 1024 * 1024) {
            setError('Dosya boyutu en fazla 10MB olabilir.')
            return
        }

        setFile(selectedFile)
        setError(null)

        // Create preview for images
        if (selectedFile.type.startsWith('image/')) {
            const reader = new FileReader()
            reader.onloadend = () => {
                setPreview(reader.result as string)
            }
            reader.readAsDataURL(selectedFile)
        } else {
            setPreview(null)
        }
    }

    const handleUpload = async () => {
        if (!file) return

        setUploading(true)
        setError(null)

        try {
            const result = await api.uploadDocument(file)
            // Redirect to document confirmation page
            const documentId = result.extraction_details?.document_id
            if (documentId) {
                router.push(`/documents/${documentId}`)
            } else {
                router.push('/documents')
            }
        } catch (err: any) {
            setError(err.message || 'Yükleme başarısız oldu.')
        } finally {
            setUploading(false)
        }
    }

    const clearFile = () => {
        setFile(null)
        setPreview(null)
        setError(null)
    }

    return (
        <div className="max-w-2xl mx-auto">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                    Fiş / Fatura Yükle
                </h1>
                <p className="text-gray-500 dark:text-gray-400 mt-1">
                    Görsel yükleyin, sistem otomatik olarak verileri çıkaracak
                </p>
            </div>

            {/* Upload Area */}
            <div
                className={`card p-8 border-2 border-dashed transition-colors ${dragActive
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-300 dark:border-gray-600'
                    }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
            >
                {!file ? (
                    <label className="flex flex-col items-center justify-center cursor-pointer py-8">
                        <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mb-4">
                            <Upload className="w-8 h-8 text-gray-400" />
                        </div>
                        <p className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Dosyayı sürükleyin veya tıklayın
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            JPEG, PNG, WebP veya PDF • Max 10MB
                        </p>
                        <input
                            type="file"
                            className="hidden"
                            accept="image/jpeg,image/png,image/webp,application/pdf"
                            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                        />
                    </label>
                ) : (
                    <div className="flex items-start gap-4">
                        {/* Preview */}
                        <div className="w-32 h-32 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center overflow-hidden">
                            {preview ? (
                                <img
                                    src={preview}
                                    alt="Preview"
                                    className="w-full h-full object-cover"
                                />
                            ) : (
                                <FileImage className="w-12 h-12 text-gray-400" />
                            )}
                        </div>

                        {/* File Info */}
                        <div className="flex-1">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="font-medium text-gray-900 dark:text-white">
                                        {file.name}
                                    </p>
                                    <p className="text-sm text-gray-500">
                                        {(file.size / 1024 / 1024).toFixed(2)} MB
                                    </p>
                                </div>
                                <button
                                    onClick={clearFile}
                                    className="p-1 text-gray-400 hover:text-gray-600"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Actions */}
                            <div className="mt-4 flex gap-3">
                                <button
                                    onClick={handleUpload}
                                    disabled={uploading}
                                    className="btn btn-primary flex items-center gap-2"
                                >
                                    {uploading ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            İşleniyor... (Bu 1-2 dakika sürebilir)
                                        </>
                                    ) : (
                                        <>
                                            <Check className="w-4 h-4" />
                                            Yükle ve İşle
                                        </>
                                    )}
                                </button>
                                <button
                                    onClick={clearFile}
                                    disabled={uploading}
                                    className="btn btn-secondary"
                                >
                                    İptal
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Error Message */}
            {error && (
                <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <p className="text-red-700 dark:text-red-300">{error}</p>
                </div>
            )}

            {/* Tips */}
            <div className="mt-6 card p-5">
                <h3 className="font-medium text-gray-900 dark:text-white mb-3">
                    💡 İpuçları
                </h3>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                    <li>• Fotoğrafın net ve düzgün olduğundan emin olun</li>
                    <li>• Fiş/fatura tam olarak görünür olmalı</li>
                    <li>• Işık yansıması ve gölgelerden kaçının</li>
                    <li>• PDF dosyaları için metin seçilebilir olmalı</li>
                </ul>
            </div>
        </div>
    )
}
