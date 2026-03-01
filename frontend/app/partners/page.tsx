'use client'

import { useState, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiClient, Partner } from '@/lib/api'

export async function generateMetadata() {
  const { partnersMetadata } = await import('@/lib/metadata')
  return partnersMetadata
}

export default function PartnersPage() {
  const [partners, setPartners] = useState<Partner[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const searchParams = useSearchParams()
  const router = useRouter()

  useEffect(() => {
    const selected = searchParams.get('selected')
    if (selected) {
      setSelectedId(selected)
    }
    fetchPartners()
  }, [searchParams])

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

  const handleSelectPartner = (partnerId: string) => {
    router.push(`/onboard?partner=${partnerId}`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted to-background">
      {/* Background effects */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute top-1/4 -left-1/3 w-96 h-96 bg-primary/10 rounded-full blur-3xl opacity-40"></div>
        <div className="absolute bottom-1/4 -right-1/3 w-96 h-96 bg-accent/10 rounded-full blur-3xl opacity-40"></div>
      </div>

      {/* Header */}
      <div className="relative z-10 container mx-auto px-4 py-8 flex justify-between items-center">
        <Link href="/">
          <button className="btn-ghost">← Back</button>
        </Link>
        <h1 className="text-3xl font-bold gradient-text">Choose Your Companion</h1>
        <div className="w-20"></div>
      </div>

      {/* Partner Grid */}
      <section className="relative z-10 container mx-auto px-4 py-12">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-bounce-soft">
              <div className="w-12 h-12 bg-primary rounded-full"></div>
            </div>
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-8">
            {partners.map((partner) => (
              <div
                key={partner.id}
                className={`group glass-effect overflow-hidden transition-all duration-300 transform hover:scale-105 cursor-pointer ${
                  selectedId === partner.id ? 'border-accent ring-2 ring-accent/50' : 'hover:border-primary/50'
                }`}
                onClick={() => setSelectedId(partner.id)}
              >
                {/* Partner Avatar */}
                <div className="h-64 bg-gradient-to-br from-primary to-accent flex items-center justify-center text-8xl group-hover:scale-110 transition-transform duration-300 relative overflow-hidden">
                  {partner.partner_type === 'girlfriend' && '👩‍🦰'}
                  {partner.partner_type === 'boyfriend' && '👨‍🦱'}
                  {partner.partner_type === 'best_friend' && '🤝'}
                  
                  {/* Glow effect */}
                  <div className="absolute inset-0 bg-gradient-to-t from-transparent to-transparent group-hover:from-white/10 group-hover:to-transparent transition-all duration-300"></div>
                </div>

                {/* Content */}
                <div className="p-6 relative z-10">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-2xl font-bold mb-1">{partner.name}</h3>
                      <p className="text-sm text-accent font-semibold capitalize">
                        {partner.partner_type.replace('_', ' ')}
                      </p>
                    </div>
                    {selectedId === partner.id && (
                      <div className="text-2xl animate-bounce-soft">✓</div>
                    )}
                  </div>

                  <p className="text-muted-foreground mb-4 text-sm leading-relaxed">
                    {partner.description}
                  </p>

                  <div className="mb-6 p-3 bg-muted/50 rounded-lg border border-muted-foreground/10">
                    <p className="text-xs text-muted-foreground font-semibold mb-1">Personality</p>
                    <p className="text-sm">{partner.personality}</p>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleSelectPartner(partner.id)
                    }}
                    className={`w-full py-3 rounded-lg font-semibold transition-all duration-200 ${
                      selectedId === partner.id
                        ? 'btn-primary'
                        : 'btn-secondary hover:bg-accent'
                    }`}
                  >
                    {selectedId === partner.id ? 'Get Started with ' + partner.name : 'Choose ' + partner.name}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Features */}
      <section className="relative z-10 container mx-auto px-4 py-20 mt-20 border-t border-muted">
        <h2 className="text-3xl font-bold text-center mb-12">Each Companion Brings Unique Vibes</h2>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              title: 'Your Girlfriend',
              emoji: '💕',
              traits: ['Caring & Supportive', 'Romantic & Sweet', 'Understanding & Empathetic'],
            },
            {
              title: 'Your Boyfriend',
              emoji: '💪',
              traits: ['Fun & Adventurous', 'Protective & Strong', 'Genuine & Loyal'],
            },
            {
              title: 'Your Best Friend',
              emoji: '🤝',
              traits: ['Hilarious & Real', 'Always There for You', 'Judgment-Free Zone'],
            },
          ].map((item, idx) => (
            <div key={idx} className="card hover:border-primary/50 transition-all hover:scale-105">
              <div className="text-5xl mb-4">{item.emoji}</div>
              <h3 className="text-xl font-bold mb-4">{item.title}</h3>
              <ul className="space-y-2">
                {item.traits.map((trait, i) => (
                  <li key={i} className="flex items-center text-sm text-muted-foreground">
                    <span className="text-primary mr-2">•</span>
                    {trait}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
