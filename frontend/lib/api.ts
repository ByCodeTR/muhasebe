/**
 * API client for backend communication
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface FetchOptions extends RequestInit {
    params?: Record<string, string>
}

class ApiClient {
    private baseUrl: string

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl
    }

    private async request<T>(
        endpoint: string,
        options: FetchOptions = {}
    ): Promise<T> {
        const { params, ...fetchOptions } = options

        let url = `${this.baseUrl}${endpoint}`
        if (params) {
            const searchParams = new URLSearchParams(params)
            url += `?${searchParams.toString()}`
        }

        const response = await fetch(url, {
            ...fetchOptions,
            headers: {
                'Content-Type': 'application/json',
                ...fetchOptions.headers,
            },
        })

        if (!response.ok) {
            const error = await response.json().catch(() => ({}))
            throw new Error(error.detail || `API Error: ${response.status}`)
        }

        return response.json()
    }

    // Health
    async healthCheck() {
        return this.request('/health')
    }

    // Documents
    async getDocuments(params?: { status?: string; limit?: number; offset?: number }) {
        return this.request('/documents/', {
            params: params as Record<string, string>,
        })
    }

    async getDrafts() {
        return this.request('/documents/drafts')
    }

    async getDocument(id: string) {
        return this.request(`/documents/${id}`)
    }

    async uploadDocument(file: File) {
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch(`${this.baseUrl}/documents/upload`, {
            method: 'POST',
            body: formData,
        })

        if (!response.ok) {
            const error = await response.json().catch(() => ({}))
            throw new Error(error.detail || 'Upload failed')
        }

        return response.json()
    }

    async confirmDocument(id: string, data: any) {
        return this.request(`/documents/${id}/confirm`, {
            method: 'POST',
            body: JSON.stringify(data),
        })
    }

    async updateDocument(id: string, data: any) {
        return this.request(`/documents/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        })
    }

    // Vendors
    async getVendors(params?: { search?: string; limit?: number }) {
        return this.request('/vendors/', {
            params: params as Record<string, string>,
        })
    }

    async searchVendors(q: string) {
        return this.request('/vendors/search', { params: { q } })
    }

    async createVendor(data: any) {
        return this.request('/vendors/', {
            method: 'POST',
            body: JSON.stringify(data),
        })
    }

    // Ledger
    async getLedgerEntries(params?: {
        direction?: string
        vendor_id?: string
        limit?: number
    }) {
        return this.request('/ledger/entries', {
            params: params as Record<string, string>,
        })
    }

    async createLedgerEntry(data: any) {
        return this.request('/ledger/entries', {
            method: 'POST',
            body: JSON.stringify(data),
        })
    }

    async getCategories() {
        return this.request('/ledger/categories')
    }

    // Reports
    async getSummary(period: string = 'month') {
        return this.request('/reports/summary', { params: { period } })
    }

    async getByVendor(period: string = 'month') {
        return this.request('/reports/by-vendor', { params: { period } })
    }

    async exportCsv(startDate?: string, endDate?: string) {
        let url = `${this.baseUrl}/reports/export/csv`
        const params = new URLSearchParams()
        if (startDate) params.append('start_date', startDate)
        if (endDate) params.append('end_date', endDate)
        if (params.toString()) url += `?${params.toString()}`

        const response = await fetch(url)
        return response.blob()
    }

    async exportXlsx(startDate?: string, endDate?: string) {
        let url = `${this.baseUrl}/reports/export/xlsx`
        const params = new URLSearchParams()
        if (startDate) params.append('start_date', startDate)
        if (endDate) params.append('end_date', endDate)
        if (params.toString()) url += `?${params.toString()}`

        const response = await fetch(url)
        return response.blob()
    }
}

export const api = new ApiClient(API_URL)
export default api
