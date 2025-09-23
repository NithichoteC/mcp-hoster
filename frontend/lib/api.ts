import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import toast from 'react-hot-toast'

export interface ApiError {
  message: string
  status: number
  data?: any
}

class ApiClient {
  private client: AxiosInstance
  private baseURL: string

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = this.getAuthToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        return response
      },
      (error) => {
        const apiError: ApiError = {
          message: error.response?.data?.detail || error.message || 'An error occurred',
          status: error.response?.status || 500,
          data: error.response?.data,
        }

        // Handle different error types
        if (apiError.status === 401) {
          // Unauthorized - clear token and redirect to login
          this.clearAuthToken()
          if (typeof window !== 'undefined') {
            window.location.href = '/login'
          }
        } else if (apiError.status === 403) {
          // Forbidden
          toast.error('Access denied. Insufficient permissions.')
        } else if (apiError.status >= 500) {
          // Server error
          toast.error('Server error. Please try again later.')
        }

        return Promise.reject(apiError)
      }
    )
  }

  private getAuthToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('mcp_auth_token')
  }

  private setAuthToken(token: string) {
    if (typeof window === 'undefined') return
    localStorage.setItem('mcp_auth_token', token)
  }

  private clearAuthToken() {
    if (typeof window === 'undefined') return
    localStorage.removeItem('mcp_auth_token')
  }

  // Auth methods
  async login(credentials: { email?: string; password?: string; apiKey?: string }) {
    const response = await this.client.post('/auth/login', credentials)
    const { access_token } = response.data
    this.setAuthToken(access_token)
    return response.data
  }

  async logout() {
    try {
      await this.client.post('/auth/logout')
    } catch (error) {
      // Ignore logout errors
    } finally {
      this.clearAuthToken()
    }
  }

  // Generic HTTP methods
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.get(url, config)
    return response.data
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.post(url, data, config)
    return response.data
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.put(url, data, config)
    return response.data
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.patch(url, data, config)
    return response.data
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.delete(url, config)
    return response.data
  }

  // File upload
  async upload<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData()
    formData.append('file', file)

    const response: AxiosResponse<T> = await this.client.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })

    return response.data
  }

  // Server-Sent Events
  createEventSource(url: string): EventSource {
    const token = this.getAuthToken()
    const fullUrl = new URL(url, this.baseURL)

    if (token) {
      fullUrl.searchParams.set('token', token)
    }

    return new EventSource(fullUrl.toString())
  }

  // WebSocket connection
  createWebSocket(url: string): WebSocket {
    const token = this.getAuthToken()
    const wsUrl = this.baseURL.replace(/^https?/, 'ws')
    const fullUrl = new URL(url, wsUrl)

    if (token) {
      fullUrl.searchParams.set('token', token)
    }

    return new WebSocket(fullUrl.toString())
  }

  // Health check
  async healthCheck() {
    try {
      const response = await this.get('/health')
      return { healthy: true, data: response }
    } catch (error) {
      return { healthy: false, error }
    }
  }

  // Get base URL for external links
  getBaseURL(): string {
    return this.baseURL
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!this.getAuthToken()
  }
}

// Create singleton instance
const apiClient = new ApiClient()

// Export hook for use in components
export function useApi() {
  return apiClient
}

// Export client for direct use
export { apiClient as api }

// Export types (ApiError already exported as interface above)