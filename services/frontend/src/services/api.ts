import type { Scan, ExamTemplate, User } from '../types'

interface ApiConfig {
  baseURL: string
  timeout: number
}

interface UploadOptions {
  templateId?: string
  onProgress?: (progress: number) => void
}

interface PaginationParams {
  page?: number
  limit?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

interface ScanFilters {
  status?: string[]
  dateFrom?: string
  dateTo?: string
  minScore?: number
  maxScore?: number
}

class ApiService {
  private config: ApiConfig
  private abortControllers = new Map<string, AbortController>()

  constructor(config: ApiConfig) {
    this.config = config
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {},
    trackable = false
  ): Promise<T> {
    const url = `${this.config.baseURL}${endpoint}`
    
    // Create abort controller for trackable requests
    let abortController: AbortController | undefined
    if (trackable) {
      abortController = new AbortController()
      this.abortControllers.set(endpoint, abortController)
      options.signal = abortController.signal
    }

    // Add auth token if available
    const token = localStorage.getItem('token')
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        // Add timeout
        signal: options.signal || AbortSignal.timeout(this.config.timeout)
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request was cancelled')
      }
      throw error
    } finally {
      if (trackable && abortController) {
        this.abortControllers.delete(endpoint)
      }
    }
  }

  // Auth methods
  async login(email: string, password: string): Promise<{ token: string; user: User }> {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    })
  }

  async logout(): Promise<void> {
    await this.request('/auth/logout', { method: 'POST' })
    localStorage.removeItem('token')
  }

  async refreshToken(): Promise<{ token: string }> {
    return this.request('/auth/refresh', { method: 'POST' })
  }

  // Scan methods
  async uploadScan(file: File, options: UploadOptions = {}): Promise<Scan> {
    const formData = new FormData()
    formData.append('file', file)
    
    if (options.templateId) {
      formData.append('templateId', options.templateId)
    }

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable && options.onProgress) {
          const progress = Math.round((event.loaded / event.total) * 100)
          options.onProgress(progress)
        }
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const result = JSON.parse(xhr.responseText)
            resolve(result)
          } catch (error) {
            reject(new Error('Invalid response format'))
          }
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`))
        }
      }

      xhr.onerror = () => reject(new Error('Network error during upload'))
      xhr.ontimeout = () => reject(new Error('Upload timeout'))

      const token = localStorage.getItem('token')
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      }

      xhr.timeout = this.config.timeout
      xhr.open('POST', `${this.config.baseURL}/scans`)
      xhr.send(formData)
    })
  }

  async getScans(
    pagination: PaginationParams = {},
    filters: ScanFilters = {}
  ): Promise<{ scans: Scan[]; total: number; page: number; limit: number }> {
    const params = new URLSearchParams()
    
    // Add pagination
    if (pagination.page) params.append('page', pagination.page.toString())
    if (pagination.limit) params.append('limit', pagination.limit.toString())
    if (pagination.sortBy) params.append('sortBy', pagination.sortBy)
    if (pagination.sortOrder) params.append('sortOrder', pagination.sortOrder)
    
    // Add filters
    if (filters.status?.length) {
      filters.status.forEach(status => params.append('status', status))
    }
    if (filters.dateFrom) params.append('dateFrom', filters.dateFrom)
    if (filters.dateTo) params.append('dateTo', filters.dateTo)
    if (filters.minScore !== undefined) params.append('minScore', filters.minScore.toString())
    if (filters.maxScore !== undefined) params.append('maxScore', filters.maxScore.toString())

    const queryString = params.toString()
    const endpoint = `/scans${queryString ? `?${queryString}` : ''}`
    
    return this.request(endpoint, {}, true)
  }

  async getScan(scanId: string): Promise<Scan> {
    return this.request(`/scans/${scanId}`)
  }

  async deleteScan(scanId: string): Promise<void> {
    return this.request(`/scans/${scanId}`, { method: 'DELETE' })
  }

  async reprocessScan(scanId: string, templateId?: string): Promise<Scan> {
    return this.request(`/scans/${scanId}/reprocess`, {
      method: 'POST',
      body: JSON.stringify({ templateId })
    })
  }
  /**
   * Update scan fields (e.g., nombre, curp, status)
   */
  async updateScan(scanId: string, updates: Partial<any>): Promise<Scan> {
    return this.request(`/scans/${scanId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates)
    })
  }

  async exportScan(scanId: string, format: 'xlsx' | 'csv' | 'pdf' = 'xlsx'): Promise<Blob> {
    const response = await fetch(`${this.config.baseURL}/exports/${scanId}?format=${format}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    })

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`)
    }

    return response.blob()
  }

  // Template methods
  async getTemplates(): Promise<ExamTemplate[]> {
    return this.request('/templates')
  }

  async getTemplate(templateId: string): Promise<ExamTemplate> {
    return this.request(`/templates/${templateId}`)
  }

  async createTemplate(template: Omit<ExamTemplate, 'id'>): Promise<ExamTemplate> {
    return this.request('/templates', {
      method: 'POST',
      body: JSON.stringify(template)
    })
  }

  async updateTemplate(templateId: string, updates: Partial<ExamTemplate>): Promise<ExamTemplate> {
    return this.request(`/templates/${templateId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates)
    })
  }

  async deleteTemplate(templateId: string): Promise<void> {
    return this.request(`/templates/${templateId}`, { method: 'DELETE' })
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/health')
  }

  // Cancel specific request
  cancelRequest(endpoint: string): void {
    const controller = this.abortControllers.get(endpoint)
    if (controller) {
      controller.abort()
      this.abortControllers.delete(endpoint)
    }
  }

  // Cancel all requests
  cancelAllRequests(): void {
    this.abortControllers.forEach(controller => controller.abort())
    this.abortControllers.clear()
  }
}

// Create singleton instance
export const apiService = new ApiService({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 30000 // 30 seconds
})

// Export types for use in components
export type { UploadOptions, PaginationParams, ScanFilters }