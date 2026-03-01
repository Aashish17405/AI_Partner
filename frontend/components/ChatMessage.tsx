'use client'

import { Message } from '@/lib/api'
import { formatDate } from '@/lib/utils'

interface ChatMessageProps {
  message: Message
  partnerName?: string
  partnerType?: string
}

export function ChatMessage({ message, partnerName = 'AI Partner', partnerType = 'best_friend' }: ChatMessageProps) {
  const isUser = message.role === 'user'

  const getPartnerAvatar = () => {
    if (partnerType === 'girlfriend') return '👩‍🦰'
    if (partnerType === 'boyfriend') return '👨‍🦱'
    return '🤝'
  }

  return (
    <div className={`flex gap-4 mb-6 animate-fade-in ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-lg">
          {getPartnerAvatar()}
        </div>
      )}

      <div className={`flex flex-col gap-1 max-w-xs sm:max-w-md ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`px-4 py-3 rounded-lg transition-all duration-300 break-words ${
            isUser
              ? 'bg-primary text-primary-foreground rounded-br-none'
              : 'bg-muted text-foreground border border-muted-foreground/20 rounded-bl-none'
          }`}
        >
          <p className="text-sm sm:text-base leading-relaxed">{message.content}</p>
        </div>

        {message.timestamp && (
          <span className="text-xs text-muted-foreground px-2">
            {formatDate(message.timestamp)}
          </span>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-accent flex items-center justify-center text-lg">
          👤
        </div>
      )}
    </div>
  )
}
