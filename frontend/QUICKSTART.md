# Quick Start Guide

Get the AI Partner frontend running in 5 minutes.

## 1. Prerequisites

Ensure you have:
- Node.js 18+ (`node --version`)
- FastAPI backend running (`http://localhost:8000`)

## 2. Clone & Install

```bash
cd frontend
npm install
```

## 3. Environment Setup

```bash
cp .env.example .env.local
```

The default settings work for local development. No changes needed unless your backend is on a different port.

## 4. Start Dev Server

```bash
npm run dev
```

## 5. Open in Browser

Visit **http://localhost:3000**

You should see the landing page with partner cards.

## Testing the Flow

1. **Landing Page** (`/`) - You're here!
2. Click **"Start Chatting Now"** → Partner selection page
3. Click any partner card → Onboarding form
4. Fill the form (name, age 18+, interests) → Start Chat
5. Chat with your AI companion!

## Hot Reload

Changes to files automatically refresh the browser. Just edit and save.

## Troubleshooting

### "Cannot connect to API"
- Check if FastAPI backend is running: `curl http://localhost:8000/`
- Verify `.env.local` has correct `NEXT_PUBLIC_API_BASE_URL`

### "Port 3000 already in use"
```bash
npm run dev -- -p 3001  # Use port 3001 instead
```

### TypeScript errors
```bash
npm run build  # Check for compilation errors
```

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx              ← Landing page
│   ├── partners/page.tsx     ← Partner selection
│   ├── onboard/page.tsx      ← User form
│   └── chat/[sessionId]/     ← Chat interface
├── components/               ← React components
├── lib/                      ← Utilities & API
└── public/                   ← Static assets
```

## Useful Commands

```bash
npm run dev       # Start dev server
npm run build     # Production build
npm start         # Run production server
npm run lint      # Check for issues
```

## Next Steps

1. Explore the chat functionality
2. Modify styles in `app/globals.css`
3. Update colors in `tailwind.config.ts`
4. Add new pages in `app/` directory
5. Create components in `components/`

## API Endpoints

The frontend uses these backend endpoints:

```
GET  /partners              → List all companions
POST /sessions              → Start new chat
POST /sessions/{id}/chat    → Send message
GET  /sessions/{id}/history → Load chat history
DELETE /sessions/{id}       → End session
```

See `lib/api.ts` for implementation.

## Common Customizations

### Change API Base URL

Edit `.env.local`:
```env
NEXT_PUBLIC_API_BASE_URL=http://your-api-server.com
```

### Change App Name

Edit `.env.local`:
```env
NEXT_PUBLIC_APP_NAME="Your App Name"
```

### Update Colors

Edit `app/globals.css` CSS variables:
```css
:root {
  --primary: 290 70% 55%;      /* Purple */
  --secondary: 190 85% 50%;    /* Cyan */
  --accent: 340 82% 52%;       /* Pink */
}
```

### Change Fonts

Edit `tailwind.config.ts` and `app/globals.css`:
```typescript
fontFamily: {
  sans: ['var(--font-your-font)', 'system-ui'],
}
```

## Documentation

- **Full README**: `README.md`
- **Deployment**: `DEPLOYMENT.md`
- **Backend API**: Check FastAPI docs at `/docs`

## Getting Help

Check these files first:
1. Error message in browser console (F12)
2. Terminal output for build errors
3. `.env.local` configuration
4. Backend API is running

Still stuck? Create an issue on GitHub or contact support.

Happy building!
