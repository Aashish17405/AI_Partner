import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Partner - Your Perfect Companion Awaits',
  description: 'Chat with your ideal AI companion - girlfriend, boyfriend, or best friend. Personalized conversations powered by advanced AI.',
  keywords: 'AI companion, chatbot, girlfriend, boyfriend, best friend, AI chat',
  authors: [{ name: 'AI Partner' }],
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://aipartner.app',
    siteName: 'AI Partner',
    title: 'AI Partner - Your Perfect Companion Awaits',
    description: 'Chat with your ideal AI companion - girlfriend, boyfriend, or best friend.',
    images: [
      {
        url: 'https://images.unsplash.com/photo-1677442d019cecf8fbf5d9c89b56b92055a06c9fe?w=1200&h=630',
        width: 1200,
        height: 630,
        alt: 'AI Partner',
      },
    ],
  },
  robots: {
    index: true,
    follow: true,
    nocache: true,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
        <meta name="theme-color" content="#1a1a1a" />
        <meta name="description" content="Chat with your ideal AI companion - girlfriend, boyfriend, or best friend. Personalized conversations powered by advanced AI." />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
