// Analytics — optional PostHog integration (disabled for MVP)
// To enable: install posthog-js, set VITE_POSTHOG_KEY in .env

export function trackEvent(_event, _properties) {
  // PostHog not configured
}

export function identifyUser(_userId, _traits) {
  // PostHog not configured
}

export function resetAnalytics() {
  // PostHog not configured
}
