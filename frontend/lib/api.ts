const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export interface Partner {
  id: string
  name: string
  partner_type: string
  description: string
  personality: string
  avatar?: string
}

export interface Session {
  id: string
  partner_id: string
  user_name: string
  user_nickname?: string
  user_age: number
  user_language: string
  user_interests: string[]
  personality_preference?: string
  created_at: string
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

export interface ChatResponse {
  session_id: string
  reply: string
  conversation_history: Message[]
}

class APIClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const headers = {
      'Content-Type': 'application/json',
      ...options?.headers,
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`)
      }

      return response.json() as Promise<T>
    } catch (error) {
      console.error('[API] Error:', error)
      throw error
    }
  }

  // Partners endpoint
  async getPartners(): Promise<Partner[]> {
    return this.request<Partner[]>('/partners')
  }

  // Sessions endpoints
  async createSession(
    partnerId: string,
    userName: string,
    userAge: number,
    userLanguage: string,
    userInterests: string[],
    userNickname?: string,
    personalityPreference?: string
  ): Promise<Session> {
    return this.request<Session>('/sessions', {
      method: 'POST',
      body: JSON.stringify({
        partner_id: partnerId,
        user_name: userName,
        user_nickname: userNickname,
        user_age: userAge,
        user_language: userLanguage,
        user_interests: userInterests,
        personality_preference: personalityPreference,
      }),
    })
  }

  async getSession(sessionId: string): Promise<Session> {
    return this.request<Session>(`/sessions/${sessionId}`)
  }

  // Chat endpoints
  async sendMessage(sessionId: string, message: string): Promise<ChatResponse> {
    return this.request<ChatResponse>(`/sessions/${sessionId}/chat`, {
      method: 'POST',
      body: JSON.stringify({ user_message: message }),
    })
  }

  async getHistory(sessionId: string): Promise<Message[]> {
    return this.request<Message[]>(`/sessions/${sessionId}/history`)
  }

  // Delete session
  async deleteSession(sessionId: string): Promise<void> {
    return this.request<void>(`/sessions/${sessionId}`, {
      method: 'DELETE',
    })
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/')
  }
}

export const apiClient = new APIClient()
