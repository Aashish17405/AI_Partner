# AI Partner Frontend - Deployment Guide

## Local Development Setup

### 1. Prerequisites
- Node.js 18+ installed
- FastAPI backend running locally on port 8000
- Git repository set up

### 2. Install Dependencies

```bash
cd frontend
npm install
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env.local

# Edit .env.local to match your backend setup
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=AI Partner
```

### 4. Run Development Server

```bash
npm run dev
```

Visit http://localhost:3000 in your browser.

## Production Deployment

### Option 1: Vercel (Recommended)

Vercel is the easiest option for Next.js apps:

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from frontend directory
cd frontend
vercel

# For production deployment
vercel --prod
```

**Environment Variables Setup:**
1. Go to Vercel dashboard → Settings → Environment Variables
2. Add:
   - `NEXT_PUBLIC_API_BASE_URL`: Your production API URL (e.g., `https://api.aipartner.app`)
   - `NEXT_PUBLIC_APP_NAME`: AI Partner

### Option 2: Self-Hosted (Docker)

Create a `Dockerfile` in the frontend directory:

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build

# Expose port
EXPOSE 3000

# Start
CMD ["npm", "start"]
```

Build and run:

```bash
# Build image
docker build -t ai-partner-frontend .

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com \
  -e NEXT_PUBLIC_APP_NAME="AI Partner" \
  ai-partner-frontend
```

### Option 3: Traditional Server (Node.js)

```bash
# Build for production
npm run build

# Start production server
npm start
```

Use a process manager like PM2:

```bash
npm install -g pm2

# Start app
pm2 start npm --name "ai-partner" -- start

# Setup auto-restart
pm2 startup
pm2 save
```

## Configuration

### API Base URL

The frontend expects the FastAPI backend at the URL specified in `NEXT_PUBLIC_API_BASE_URL`. Update this based on your deployment:

- **Local**: `http://localhost:8000`
- **Development**: `https://api-dev.aipartner.app`
- **Production**: `https://api.aipartner.app`

### CORS Configuration

Ensure your FastAPI backend has CORS enabled for your frontend domain:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://aipartner.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Performance Optimization

### Build Optimization

The Next.js build is already optimized with:
- Code splitting per route
- CSS minification via Tailwind
- Image optimization (enabled in next.config.mjs)
- Tree shaking for unused code

### Caching Strategy

- **Assets**: 1 year cache (versioned by Next.js)
- **HTML**: No cache (always fresh)
- **API calls**: No cache (real-time)

### Web Vitals

Monitor performance:
- **LCP** (Largest Contentful Paint): < 2.5s
- **FID** (First Input Delay): < 100ms
- **CLS** (Cumulative Layout Shift): < 0.1

## Database & Sessions

**Important**: Sessions are stored in browser localStorage. If users clear their browser cache, they lose their session. For production, consider:

1. **Server-side sessions** - Store session data in a database
2. **User accounts** - Implement authentication to persist across devices
3. **Session database** - Store session state server-side with short-lived tokens

To implement server-side sessions, modify:
- `lib/api.ts` - Add session token handling
- Backend - Store session metadata in database
- `app/chat/[sessionId]/page.tsx` - Fetch session from server instead of localStorage

## Monitoring & Analytics

### Error Tracking

Integrate error tracking (e.g., Sentry):

```bash
npm install @sentry/nextjs
```

### Analytics

Add analytics (e.g., Vercel Analytics):

```bash
npm install @vercel/analytics react
```

Then import in your layout:

```typescript
import { Analytics } from '@vercel/analytics/react'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
```

## Security Checklist

- [ ] HTTPS enabled in production
- [ ] API URLs use HTTPS
- [ ] CORS properly configured on backend
- [ ] Environment variables not committed to git
- [ ] .env.local in .gitignore
- [ ] No hardcoded secrets in code
- [ ] Content Security Policy headers set
- [ ] Input validation on frontend
- [ ] Rate limiting on backend

## Troubleshooting

### API Connection Issues

**Symptoms**: "Failed to fetch partners" or similar errors

**Solutions**:
1. Check if FastAPI backend is running: `curl http://localhost:8000/`
2. Verify CORS configuration on backend
3. Check `NEXT_PUBLIC_API_BASE_URL` in .env.local
4. Check browser console for detailed error messages

### Session Lost After Refresh

**Solutions**:
1. This is expected behavior with localStorage
2. For persistence across sessions, implement server-side session storage
3. Users can restart chat with "New Chat" button

### Build Failures

**Common causes**:
- TypeScript errors: Run `npm run build` locally to debug
- Missing dependencies: Verify all imports are installed
- Environment variables: Ensure all `NEXT_PUBLIC_*` vars are set

## Maintenance

### Regular Updates

```bash
# Check for outdated dependencies
npm outdated

# Update dependencies
npm update

# Update to latest (with breaking changes)
npm install --save-dev next@latest
```

### Database Cleanup

If implementing server-side sessions, periodically clean old sessions:
- Set session expiration (e.g., 7 days)
- Run cleanup cron job
- Archive completed conversations

## Support

For deployment issues:
1. Check logs: `vercel logs` (for Vercel deployment)
2. Review error messages in browser console
3. Check backend API logs
4. Contact support: support@aipartner.app
