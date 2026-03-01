'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { apiClient, Partner } from '@/lib/api'

export async function generateMetadata() {
  const { homeMetadata } = await import('@/lib/metadata')
  return homeMetadata
}

export default function HomePage() {
  const [partners, setPartners] = useState<Partner[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPartners()
  }, [])

  const fetchPartners = async () => {
    try {
      const data = await apiClient.getPartners()
      setPartners(data)
    } catch (error) {
      console.error('Failed to fetch partners:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted to-background overflow-hidden">
      {/* Animated background elements */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute top-0 -left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl opacity-40 animate-bounce-soft"></div>
        <div className="absolute bottom-0 -right-1/4 w-96 h-96 bg-accent/20 rounded-full blur-3xl opacity-40 animate-bounce-soft" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-secondary/20 rounded-full blur-3xl opacity-30 animate-bounce-soft" style={{ animationDelay: '2s' }}></div>
      </div>

      {/* Navigation */}
      <nav className="relative z-10 container mx-auto px-4 py-6 flex justify-between items-center">
        <div className="text-2xl font-bold gradient-text">AI Partner</div>
        <div className="flex gap-4">
          <button className="btn-ghost">About</button>
          <button className="btn-ghost">FAQ</button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 container mx-auto px-4 py-20 text-center">
        <div className="animate-fade-in">
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            <span className="gradient-text">Never feel alone again</span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto leading-relaxed">
            Meet your perfect AI companion. Whether you want a girlfriend, boyfriend, or best friend - we've got you covered with genuine, personalized conversations.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link href="/partners">
              <button className="btn-primary w-full sm:w-auto">
                Start Chatting Now
              </button>
            </Link>
            <button className="btn-ghost w-full sm:w-auto">
              Learn More
            </button>
          </div>
        </div>
      </section>

      {/* Partner Preview Section */}
      <section className="relative z-10 container mx-auto px-4 py-20">
        <h2 className="text-4xl font-bold text-center mb-16">Choose Your Companion</h2>
        
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-bounce-soft">
              <div className="w-12 h-12 bg-primary rounded-full"></div>
            </div>
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-8">
            {partners.map((partner, index) => (
              <div
                key={partner.id}
                className="group glass-effect hover:border-accent/50 transition-all duration-300 cursor-pointer hover:scale-105 transform"
                style={{
                  animationDelay: `${index * 150}ms`,
                }}
              >
                {/* Avatar */}
                <div className="h-48 bg-gradient-to-br from-primary to-accent rounded-lg mb-6 flex items-center justify-center text-6xl group-hover:scale-110 transition-transform duration-300">
                  {partner.partner_type === 'girlfriend' && '👩‍🦰'}
                  {partner.partner_type === 'boyfriend' && '👨‍🦱'}
                  {partner.partner_type === 'best_friend' && '🤝'}
                </div>

                <h3 className="text-2xl font-bold mb-2">{partner.name}</h3>
                <p className="text-sm text-accent mb-4 capitalize">{partner.partner_type.replace('_', ' ')}</p>
                <p className="text-muted-foreground mb-6">{partner.description}</p>
                
                <Link href={`/partners?selected=${partner.id}`}>
                  <button className="w-full btn-secondary hover:bg-accent transition-colors">
                    Choose {partner.name}
                  </button>
                </Link>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Features Section */}
      <section className="relative z-10 container mx-auto px-4 py-20">
        <h2 className="text-4xl font-bold text-center mb-16">Why Choose AI Partner?</h2>
        
        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: '💬',
              title: 'Real Conversations',
              description: 'Engage in meaningful, personalized conversations tailored to your interests and personality.',
            },
            {
              icon: '🎯',
              title: 'Always Available',
              description: 'Your companion is always there for you, 24/7, whenever you need to chat or talk.',
            },
            {
              icon: '🎭',
              title: 'Custom Personalities',
              description: 'Choose from different personality types - funny, caring, serious - to match your vibe.',
            },
          ].map((feature, index) => (
            <div
              key={index}
              className="card hover:border-primary/50 transition-all duration-300 hover:scale-105 transform"
              style={{
                animationDelay: `${index * 150}ms`,
              }}
            >
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
              <p className="text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 container mx-auto px-4 py-12 border-t border-muted mt-20">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          <div>
            <h4 className="font-bold mb-4">AI Partner</h4>
            <p className="text-sm text-muted-foreground">Your perfect AI companion awaits.</p>
          </div>
          <div>
            <h5 className="font-semibold mb-4">Product</h5>
            <ul className="text-sm text-muted-foreground space-y-2">
              <li><a href="#" className="hover:text-primary transition">Features</a></li>
              <li><a href="#" className="hover:text-primary transition">Pricing</a></li>
              <li><a href="#" className="hover:text-primary transition">Blog</a></li>
            </ul>
          </div>
          <div>
            <h5 className="font-semibold mb-4">Company</h5>
            <ul className="text-sm text-muted-foreground space-y-2">
              <li><a href="#" className="hover:text-primary transition">About</a></li>
              <li><a href="#" className="hover:text-primary transition">Contact</a></li>
              <li><a href="#" className="hover:text-primary transition">Careers</a></li>
            </ul>
          </div>
          <div>
            <h5 className="font-semibold mb-4">Legal</h5>
            <ul className="text-sm text-muted-foreground space-y-2">
              <li><a href="#" className="hover:text-primary transition">Privacy</a></li>
              <li><a href="#" className="hover:text-primary transition">Terms</a></li>
              <li><a href="#" className="hover:text-primary transition">Cookies</a></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-muted pt-8 text-center text-sm text-muted-foreground">
          <p>&copy; 2024 AI Partner. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
