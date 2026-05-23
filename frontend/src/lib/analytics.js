// Analytics — optional PostHog integration
const POSTHOG_KEY = import.meta.env.VITE_POSTHOG_KEY || ''
const POSTHOG_HOST = import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com'

let posthog = null

if (POSTHOG_KEY) {
  import('posthog-js').then(mod => {
    posthog = mod.default
    posthog.init(POSTHOG_KEY, {
      api_host: POSTHOG_HOST,
      capture_pageview: true,
      capture_pageleave: true,
      persistence: 'localStorage',
    })
  }).catch(() => {
    console.warn('posthog-js not installed. Analytics disabled.')
  })
}

export function trackEvent(event, properties) {
  if (posthog) posthog.capture(event, properties)
}

export function identifyUser(userId, traits) {
  if (posthog) posthog.identify(userId, traits)
}

export function resetAnalytics() {
  if (posthog) posthog.reset()
}
