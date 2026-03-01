import type { Metadata } from 'next'

export const siteMetadata = {
  name: 'AI Partner',
  description: 'Chat with your ideal AI companion - girlfriend, boyfriend, or best friend. Personalized conversations powered by advanced AI.',
  url: 'https://aipartner.app',
  ogImage: 'https://images.unsplash.com/photo-1677442d019cecf8fbf5d9c89b56b92055a06c9fe?w=1200&h=630',
  keywords: 'AI companion, chatbot, girlfriend, boyfriend, best friend, AI chat, conversation, personalized',
  twitterHandle: '@aipartnerapp',
}

export const homeMetadata: Metadata = {
  title: 'AI Partner - Your Perfect Companion Awaits',
  description: siteMetadata.description,
  keywords: siteMetadata.keywords,
  authors: [{ name: 'AI Partner' }],
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: siteMetadata.url,
    siteName: siteMetadata.name,
    title: 'AI Partner - Your Perfect Companion Awaits',
    description: siteMetadata.description,
    images: [
      {
        url: siteMetadata.ogImage,
        width: 1200,
        height: 630,
        alt: 'AI Partner',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AI Partner - Your Perfect Companion Awaits',
    description: siteMetadata.description,
    images: [siteMetadata.ogImage],
    creator: siteMetadata.twitterHandle,
  },
  robots: {
    index: true,
    follow: true,
    nocache: true,
    googleBot: {
      index: true,
      follow: true,
    },
  },
}

export const partnersMetadata: Metadata = {
  title: 'Choose Your AI Companion | AI Partner',
  description: 'Select your perfect AI companion - girlfriend, boyfriend, or best friend with unique personalities and conversation styles.',
  keywords: [...siteMetadata.keywords.split(','), 'choose companion', 'partner selection'],
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: `${siteMetadata.url}/partners`,
    siteName: siteMetadata.name,
    title: 'Choose Your AI Companion | AI Partner',
    description: 'Select your perfect AI companion with unique personalities.',
    images: [
      {
        url: siteMetadata.ogImage,
        width: 1200,
        height: 630,
        alt: 'AI Partner - Choose Companion',
      },
    ],
  },
  robots: {
    index: true,
    follow: true,
  },
}

export const onboardMetadata: Metadata = {
  title: 'Personalize Your Experience | AI Partner',
  description: 'Tell us about yourself to personalize your AI companion experience. Share your interests and preferences.',
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: `${siteMetadata.url}/onboard`,
    siteName: siteMetadata.name,
    title: 'Personalize Your Experience | AI Partner',
    description: 'Customize your AI companion to match your preferences.',
  },
}

export const chatMetadata: Metadata = {
  title: 'Chat with Your AI Companion | AI Partner',
  description: 'Enjoy real-time conversations with your AI companion.',
  robots: {
    index: false,
    follow: false,
    nocache: true,
  },
}

export function createChatPageMetadata(partnerName: string): Metadata {
  return {
    title: `Chat with ${partnerName} | AI Partner`,
    description: `Have a meaningful conversation with ${partnerName}, your AI companion.`,
    robots: {
      index: false,
      follow: false,
      nocache: true,
    },
  }
}

// Structured Data (Schema.org)
export function getOrganizationSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: siteMetadata.name,
    url: siteMetadata.url,
    logo: `${siteMetadata.url}/logo.png`,
    description: siteMetadata.description,
    sameAs: [
      'https://twitter.com/aipartnerapp',
      // Add other social profiles
    ],
    contactPoint: {
      '@type': 'ContactPoint',
      contactType: 'Customer Support',
      url: `${siteMetadata.url}/contact`,
    },
  }
}

export function getProductSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: 'AI Partner',
    description: siteMetadata.description,
    image: siteMetadata.ogImage,
    brand: {
      '@type': 'Brand',
      name: siteMetadata.name,
    },
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: '4.8',
      reviewCount: '1000',
    },
  }
}
