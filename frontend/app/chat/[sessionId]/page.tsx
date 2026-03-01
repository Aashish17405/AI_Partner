'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { apiClient, Message, Partner } from '@/lib/api'
import { ChatMessage } from '@/components/ChatMessage'
import { ChatInput } from '@/components/ChatInput'
import { getSessionFromLocalStorage, clearSessionFromLocalStorage } from '@/lib/utils'

export async function generateMetadata() {
  const { chatMetadata } = await import('@/lib/metadata')
  return chatMetadata
}

export default function ChatPage() {
  const router = useRouter()
  const params = useParams()
  const sessionId = params.sessionId as string

  const [messages, setMessages] = useState<Message[]>([])
  const [partner, setPartner] = useState<Partner | null>(null)
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!sessionId) return

    const storedSessionId = getSessionFromLocalStorage()
    if (!storedSessionId && storedSessionId !== sessionId) {
      // Session may have expired
      router.push('/partners')
      return
    }

    loadChatData()
  }, [sessionId, router])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const loadChatData = async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch session metadata to get partner info
      const session = await apiClient.getSession(sessionId)

      // Find partner details
      const partners = await apiClient.getPartners()
      const selectedPartner = partners.find((p) => p.id === session.partner_id)
      if (selectedPartner) {
        setPartner(selectedPartner)
      }

      // Load message history
      const history = await apiClient.getHistory(sessionId)
      setMessages(history)
    } catch (err) {
      console.error('Failed to load chat:', err)
      setError('Failed to load chat history. Please try again.')
      // Redirect after error
      setTimeout(() => {
        router.push('/partners')
      }, 2000)
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return

    // Add user message immediately
    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])

    setSending(true)
    setError(null)

    try {
      const response = await apiClient.sendMessage(sessionId, content)

      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.reply,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      console.error('Failed to send message:', err)
      setError('Failed to send message. Please try again.')

      // Remove the user message that failed
      setMessages((prev) => prev.slice(0, -1))
    } finally {
      setSending(false)
    }
  }

  const handleEndChat = async () => {
    if (!confirm('Are you sure you want to end this chat?')) return

    try {
      await apiClient.deleteSession(sessionId)
      clearSessionFromLocalStorage()
      router.push('/partners')
    } catch (err) {
      console.error('Failed to end chat:', err)
      setError('Failed to end chat. Please try again.')
    }
  }

  if (loading) {
    return (
      <div className="h-screen bg-gradient-to-br from-background via-muted to-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-primary to-accent rounded-full animate-pulse mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading your chat...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-background via-muted to-background">
      {/* Header */}
      <div className="border-b border-muted glass-effect backdrop-blur-md sticky top-0 z-20">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            {partner && (
              <>
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-2xl">
                  {partner.partner_type === 'girlfriend' && '👩‍🦰'}
                  {partner.partner_type === 'boyfriend' && '👨‍🦱'}
                  {partner.partner_type === 'best_friend' && '🤝'}
                </div>
                <div>
                  <h1 className="font-bold text-lg">{partner.name}</h1>
                  <p className="text-xs text-muted-foreground capitalize">{partner.partner_type.replace('_', ' ')}</p>
                </div>
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            <div className="text-sm text-muted-foreground">
              {messages.length} messages
            </div>
            <button
              onClick={handleEndChat}
              className="btn-ghost text-sm"
            >
              End Chat
            </button>
            <Link href="/partners">
              <button className="btn-ghost text-sm">New Chat</button>
            </Link>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto container mx-auto px-4 py-6 scroll-smooth">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <div className="text-6xl mb-4">
              {partner?.partner_type === 'girlfriend' && '💕'}
              {partner?.partner_type === 'boyfriend' && '💪'}
              {partner?.partner_type === 'best_friend' && '🎉'}
            </div>
            <h2 className="text-2xl font-bold mb-2">No messages yet</h2>
            <p className="text-muted-foreground mb-6">Start the conversation! Say hi to {partner?.name}</p>
            <div className="text-4xl animate-bounce-soft">👇</div>
          </div>
        ) : (
          <div className="space-y-2">
            {messages.map((msg, idx) => (
              <ChatMessage
                key={idx}
                message={msg}
                partnerName={partner?.name}
                partnerType={partner?.partner_type}
              />
            ))}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error Message */}
      {error && (
        <div className="container mx-auto px-4">
          <div className="p-4 bg-accent/20 border border-accent/50 rounded-lg text-accent text-sm mb-4 animate-slide-in-left">
            {error}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-muted glass-effect backdrop-blur-md sticky bottom-0 container mx-auto px-4 py-4 w-full">
        <ChatInput
          onSend={handleSendMessage}
          disabled={false}
          loading={sending}
        />
        <p className="text-xs text-muted-foreground mt-2 text-center">
          Press Shift+Enter for new line, Enter to send
        </p>
      </div>
    </div>
  )
}
