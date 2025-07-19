"use client"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

export interface ChatRequest {
  message: string
  session_id: string
  user_id?: string
}

export interface ChatResponse {
  message: string
  intent?: string
  entities?: Record<string, any>
  results?: any[]
  ui_elements?: UIElement[]
  session_id: string
  timestamp: string
}

export interface UIElement {
  type: "button" | "link" | "card"
  text: string
  action: string
  data?: Record<string, any>
}

export interface FlightSearchRequest {
  origin: string
  destination: string
  departure_date: string
  return_date?: string
  passengers: number
  class_type: string
}

export interface HotelSearchRequest {
  location: string
  check_in: string
  check_out: string
  guests: number
  rooms: number
}

export interface BookingRequest {
  booking_type: string
  booking_id: string
  passenger_details?: Record<string, any>
  payment_info?: Record<string, any>
}

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`

    const config: RequestInit = {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error)
      throw error
    }
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify(request),
    })
  }

  async searchFlights(request: FlightSearchRequest) {
    return this.request("/search-flight", {
      method: "POST",
      body: JSON.stringify(request),
    })
  }

  async searchHotels(request: HotelSearchRequest) {
    return this.request("/search-hotel", {
      method: "POST",
      body: JSON.stringify(request),
    })
  }

  async bookTrip(request: BookingRequest) {
    return this.request("/book-trip", {
      method: "POST",
      body: JSON.stringify(request),
    })
  }

  async getConversationHistory(sessionId: string, limit?: number) {
    const params = limit ? `?limit=${limit}` : ""
    return this.request(`/conversation/${sessionId}${params}`)
  }

  async clearConversation(sessionId: string) {
    return this.request(`/conversation/${sessionId}`, {
      method: "DELETE",
    })
  }

  async getSessions() {
    return this.request("/sessions")
  }

  async createSession(userId?: string) {
    return this.request("/session/new", {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    })
  }

  async healthCheck() {
    return this.request("/health")
  }
}

export const apiClient = new ApiClient()
