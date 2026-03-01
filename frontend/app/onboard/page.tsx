'use client'

import { useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiClient, Partner } from '@/lib/api'
import { saveSessionToLocalStorage } from '@/lib/utils'

export async function generateMetadata() {
  const { onboardMetadata } = await import('@/lib/metadata')
  return onboardMetadata
}

export default function OnboardPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const partnerId = searchParams.get('partner')

  const [partner, setPartner] = useState<Partner | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    nickname: '',
    age: '',
    language: 'English',
    interests: '',
    personality: 'balanced',
  })
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [step, setStep] = useState(1)

  // Fetch partner details
  useState(() => {
    if (partnerId) {
      fetchPartnerDetails()
    }
  }, [partnerId])

  const fetchPartnerDetails = async () => {
    try {
      const partners = await apiClient.getPartners()
      const selected = partners.find((p) => p.id === partnerId)
      if (selected) {
        setPartner(selected)
      }
    } catch (error) {
      console.error('Failed to fetch partner:', error)
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required'
    }
    if (!formData.age || parseInt(formData.age) < 18) {
      newErrors.age = 'Must be 18 or older'
    }
    if (!formData.interests.trim()) {
      newErrors.interests = 'Please tell us about your interests'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: '',
      }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return
    if (!partnerId) {
      setErrors({ submit: 'Partner not selected' })
      return
    }

    setLoading(true)
    try {
      const interests = formData.interests
        .split(',')
        .map((i) => i.trim())
        .filter((i) => i.length > 0)

      const session = await apiClient.createSession(
        partnerId,
        formData.name,
        parseInt(formData.age),
        formData.language,
        interests,
        formData.nickname || undefined,
        formData.personality
      )

      saveSessionToLocalStorage(session.id)
      router.push(`/chat/${session.id}`)
    } catch (error) {
      console.error('Failed to create session:', error)
      setErrors({ submit: 'Failed to start chat. Please try again.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted to-background">
      {/* Background effects */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute top-1/4 -left-1/3 w-96 h-96 bg-primary/10 rounded-full blur-3xl opacity-40"></div>
        <div className="absolute -bottom-1/3 -right-1/3 w-96 h-96 bg-accent/10 rounded-full blur-3xl opacity-40"></div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-12 max-w-2xl">
        {/* Header */}
        <div className="mb-12 text-center">
          <Link href="/partners">
            <button className="btn-ghost mb-6">← Choose Different Partner</button>
          </Link>
          {partner && (
            <div className="text-6xl mb-4">
              {partner.partner_type === 'girlfriend' && '👩‍🦰'}
              {partner.partner_type === 'boyfriend' && '👨‍🦱'}
              {partner.partner_type === 'best_friend' && '🤝'}
            </div>
          )}
          <h1 className="text-4xl font-bold mb-2">
            Let's Get Started!
            {partner && <span className="gradient-text"> with {partner.name}</span>}
          </h1>
          <p className="text-muted-foreground">Tell us about yourself so we can personalize your experience</p>
        </div>

        {/* Progress indicator */}
        <div className="mb-8 flex gap-2">
          {[1, 2, 3].map((s) => (
            <div key={s} className={`flex-1 h-2 rounded-full transition-all duration-300 ${step >= s ? 'bg-primary' : 'bg-muted'}`}></div>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="glass-effect p-8 mb-8">
          {/* Step 1: Basic Info */}
          {step === 1 && (
            <div className="space-y-6 animate-fade-in">
              <h2 className="text-2xl font-bold mb-4">Basic Information</h2>

              <div>
                <label className="block text-sm font-semibold mb-2">Your Name *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="Enter your name"
                  className="w-full px-4 py-3 bg-muted border border-muted-foreground/20 rounded-lg text-foreground placeholder-muted-foreground/50 focus:outline-none focus:border-primary transition-colors"
                />
                {errors.name && <p className="text-accent text-sm mt-1">{errors.name}</p>}
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">Nickname (optional)</label>
                <input
                  type="text"
                  name="nickname"
                  value={formData.nickname}
                  onChange={handleInputChange}
                  placeholder="What should they call you?"
                  className="w-full px-4 py-3 bg-muted border border-muted-foreground/20 rounded-lg text-foreground placeholder-muted-foreground/50 focus:outline-none focus:border-primary transition-colors"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">Age *</label>
                <input
                  type="number"
                  name="age"
                  value={formData.age}
                  onChange={handleInputChange}
                  placeholder="Must be 18+"
                  className="w-full px-4 py-3 bg-muted border border-muted-foreground/20 rounded-lg text-foreground placeholder-muted-foreground/50 focus:outline-none focus:border-primary transition-colors"
                />
                {errors.age && <p className="text-accent text-sm mt-1">{errors.age}</p>}
              </div>

              <button
                type="button"
                onClick={() => setStep(2)}
                className="w-full btn-primary"
              >
                Next Step
              </button>
            </div>
          )}

          {/* Step 2: Preferences */}
          {step === 2 && (
            <div className="space-y-6 animate-fade-in">
              <h2 className="text-2xl font-bold mb-4">Your Preferences</h2>

              <div>
                <label className="block text-sm font-semibold mb-2">Language</label>
                <select
                  name="language"
                  value={formData.language}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 bg-muted border border-muted-foreground/20 rounded-lg text-foreground focus:outline-none focus:border-primary transition-colors"
                >
                  <option value="English">English</option>
                  <option value="Hindi">Hindi</option>
                  <option value="Telugu">Telugu</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">Personality Preference</label>
                <select
                  name="personality"
                  value={formData.personality}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 bg-muted border border-muted-foreground/20 rounded-lg text-foreground focus:outline-none focus:border-primary transition-colors"
                >
                  <option value="balanced">Balanced</option>
                  <option value="funny">Funny & Playful</option>
                  <option value="serious">Serious & Deep</option>
                  <option value="caring">Caring & Supportive</option>
                </select>
              </div>

              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="flex-1 btn-ghost"
                >
                  Back
                </button>
                <button
                  type="button"
                  onClick={() => setStep(3)}
                  className="flex-1 btn-primary"
                >
                  Next Step
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Interests */}
          {step === 3 && (
            <div className="space-y-6 animate-fade-in">
              <h2 className="text-2xl font-bold mb-4">What Interests You?</h2>

              <div>
                <label className="block text-sm font-semibold mb-2">Your Interests *</label>
                <textarea
                  name="interests"
                  value={formData.interests}
                  onChange={handleInputChange}
                  placeholder="e.g., gaming, music, traveling, reading, fitness..."
                  rows={4}
                  className="w-full px-4 py-3 bg-muted border border-muted-foreground/20 rounded-lg text-foreground placeholder-muted-foreground/50 focus:outline-none focus:border-primary transition-colors resize-none"
                />
                <p className="text-xs text-muted-foreground mt-2">Separate interests with commas for better personalization</p>
                {errors.interests && <p className="text-accent text-sm mt-1">{errors.interests}</p>}
              </div>

              {errors.submit && (
                <div className="p-3 bg-accent/20 border border-accent/50 rounded-lg text-accent text-sm">
                  {errors.submit}
                </div>
              )}

              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="flex-1 btn-ghost"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Starting Chat...' : '🚀 Start Chatting!'}
                </button>
              </div>
            </div>
          )}
        </form>

        {/* Info box */}
        <div className="card text-center text-sm text-muted-foreground">
          <p>Your information is used only to personalize your chat experience. We never share your data.</p>
        </div>
      </div>
    </div>
  )
}
