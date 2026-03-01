# AI Partner Frontend

A modern, Gen-Z friendly Next.js 16 frontend for the AI Companion SaaS platform. Features a beautiful landing page, partner selection flow, personalized onboarding, and real-time chat interface.

## Features

- **Landing Page** - Hero section with partner showcase and value propositions
- **Partner Selection** - Browse and choose from different AI companions (girlfriend, boyfriend, best friend)
- **Onboarding Flow** - Multi-step form to personalize user experience
- **Real-time Chat** - Beautiful chat interface with message history
- **SEO Optimized** - Proper meta tags, Open Graph, and structured data
- **Responsive Design** - Mobile-first approach with smooth animations
- **Session Management** - localStorage persistence with reconnect logic

## Tech Stack

- **Framework**: Next.js 16 with TypeScript
- **Styling**: Tailwind CSS with custom animations
- **State Management**: React hooks + localStorage
- **API Client**: Fetch-based API wrapper
- **Backend**: FastAPI (configurable via environment variables)

## Getting Started

### Prerequisites

- Node.js 18+ and npm/pnpm/yarn/bun
- FastAPI backend running on localhost:8000 (or configured URL)

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local

# Edit .env.local and update NEXT_PUBLIC_API_BASE_URL if needed
# Default: http://localhost:8000
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the app.

### Building

```bash
npm run build
npm start
```

## Environment Variables

```env
# FastAPI Backend URL (default: http://localhost:8000)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# App Configuration
NEXT_PUBLIC_APP_NAME=AI Partner
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with global metadata
│   ├── page.tsx                # Landing page (/)
│   ├── globals.css             # Global styles and animations
│   ├── partners/
│   │   └── page.tsx            # Partner selection (/partners)
│   ├── onboard/
│   │   └── page.tsx            # Onboarding form (/onboard)
│   └── chat/
│       └── [sessionId]/
│           └── page.tsx        # Chat interface (/chat/[sessionId])
├── components/
│   ├── ChatMessage.tsx         # Message display component
│   └── ChatInput.tsx           # Message input component
├── lib/
│   ├── api.ts                  # API client functions
│   ├── utils.ts                # Utility functions
│   └── metadata.ts             # SEO metadata configuration
├── next.config.mjs             # Next.js configuration
├── tailwind.config.ts          # Tailwind CSS configuration
└── tsconfig.json               # TypeScript configuration
```

## API Integration

The app connects to a FastAPI backend with the following endpoints:

- `GET /` - Health check
- `GET /partners` - List all partners
- `POST /sessions` - Create new session
- `GET /sessions/{id}` - Get session metadata
- `GET /sessions/{id}/history` - Load conversation history
- `POST /sessions/{id}/chat` - Send message
- `DELETE /sessions/{id}` - End session

## Pages & Routes

### Landing Page (`/`)
- Hero section with call-to-action
- Partner showcase with selection buttons
- Features and benefits section
- Footer with links

### Partner Selection (`/partners`)
- Display all available partners
- Detailed partner cards with descriptions
- Partner type icons and personality info
- Selection feedback with visual indicators

### Onboarding (`/onboard?partner=<id>`)
- Multi-step form (Step 1-3)
- Collects: name, age, language, personality preference, interests
- Form validation with error messages
- Progress indicator
- Creates session on submission

### Chat (`/chat/[sessionId]`)
- Real-time message display
- Message history on load
- Auto-scroll to latest message
- Session header with partner info
- Message count and chat controls
- Responsive layout for mobile/desktop

## Design System

### Color Palette
- **Primary**: Purple/Pink gradient (#9333ea)
- **Secondary**: Neon Cyan (#06b6d4)
- **Accent**: Hot Pink (#ec4899)
- **Background**: Deep dark (#1a1a1a)
- **Muted**: Dark gray (#404040)

### Typography
- **Font Family**: System fonts (Inter fallback)
- **Font Scale**: Responsive heading sizes
- **Line Height**: 1.5-1.6 for body text

### Components
- Glass morphism effects with backdrop blur
- Smooth animations and transitions
- Gradient text and borders
- Custom scrollbar styling

## Performance Optimizations

- Image unoptimization disabled for development
- CSS-in-JS via Tailwind for smaller bundles
- Lazy loading for API calls
- Smooth scroll behavior
- Optimized animations using CSS transforms

## SEO Features

- Dynamic meta tags per page
- Open Graph tags for social sharing
- Twitter Card support
- Robots directives (noindex for chat pages)
- Semantic HTML structure
- Structured data (Schema.org)

## Session Management

Sessions are stored in localStorage:
- Session ID persists across page reloads
- Auto-redirect if session expires
- Message history loaded on chat page mount
- Session cleanup on "End Chat"

## Error Handling

- Network error fallbacks with user feedback
- 404 redirects for invalid sessions
- Form validation with helpful messages
- Toast-style notifications for errors
- Graceful degradation for API failures

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Contributing

1. Follow the existing code structure
2. Use TypeScript for type safety
3. Update metadata when adding new pages
4. Test responsive design on mobile devices
5. Ensure animations are smooth (60fps)

## License

Proprietary - AI Partner Inc.

## Support

For issues or questions, contact: support@aipartner.app
