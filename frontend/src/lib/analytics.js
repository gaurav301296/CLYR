import posthog from 'posthog-js'

const POSTHOG_KEY = import.meta.env.VITE_POSTHOG_KEY || ''
const POSTHOG_HOST = import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com'

if (POSTHOG_KEY) {
  posthog.init(POSTHOG_KEY, {
    api_host: POSTHOG_HOST,
    capture_pageview: true,
    capture_pageleave: true,
    persistence: 'localStorage',
  })
}

export function trackEvent(event, properties) {
  if (POSTHOG_KEY) {
    posthog.capture(event, properties)
  }
}

export function identifyUser(userId, traits) {
  if (POSTHOG_KEY) {
    posthog.identify(userId, traits)
  }
}

export function resetAnalytics() {
  if (POSTHOG_KEY) {
    posthog.reset()
  }
}

export { posthog }
