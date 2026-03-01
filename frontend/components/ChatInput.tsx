'use client'

import { useState, useRef, useEffect } from 'react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  loading?: boolean
}

export function ChatInput({ onSend, disabled = false, loading = false }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (inputRef.current && !loading) {
      inputRef.current.focus()
    }
  }, [loading])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !disabled && !loading) {
      onSend(message)
      setMessage('')
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 items-end">
      <div className="flex-1 glass-effect p-4 rounded-lg border border-muted-foreground/20 focus-within:border-primary/50 transition-colors">
        <textarea
          ref={inputRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (Shift+Enter for new line)"
          disabled={disabled || loading}
          rows={1}
          className="w-full bg-transparent text-foreground placeholder-muted-foreground/50 outline-none resize-none max-h-32 disabled:opacity-50"
          style={{
            height: `${Math.min(Math.max(inputRef.current?.scrollHeight || 24, 24), 128)}px`,
          }}
        />
      </div>

      <button
        type="submit"
        disabled={!message.trim() || disabled || loading}
        className="flex-shrink-0 p-4 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg font-semibold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105"
        aria-label="Send message"
      >
        {loading ? (
          <div className="w-5 h-5 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin"></div>
        ) : (
          <span className="text-xl">↑</span>
        )}
      </button>
    </form>
  )
}
