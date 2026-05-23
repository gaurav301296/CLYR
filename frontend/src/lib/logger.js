/**
 * CLYR Frontend Logger
 * Structured logging with levels, timestamps, and optional remote reporting.
 */
const LOG_LEVELS = { debug: 0, info: 1, warn: 2, error: 3 };
const CURRENT_LEVEL = (import.meta.env?.VITE_LOG_LEVEL || 'info');

function shouldLog(level) {
  return LOG_LEVELS[level] >= LOG_LEVELS[CURRENT_LEVEL];
}

function formatMsg(level, msg, data) {
  const ts = new Date().toISOString();
  const base = `[${ts}] [${level.toUpperCase()}] ${msg}`;
  if (data !== undefined) {
    try {
      return `${base} | ${typeof data === 'object' ? JSON.stringify(data) : data}`;
    } catch {
      return base;
    }
  }
  return base;
}

export const logger = {
  debug(msg, data) {
    if (shouldLog('debug')) console.debug(formatMsg('debug', msg, data));
  },
  info(msg, data) {
    if (shouldLog('info')) console.info(formatMsg('info', msg, data));
  },
  warn(msg, data) {
    if (shouldLog('warn')) console.warn(formatMsg('warn', msg, data));
  },
  error(msg, data) {
    if (shouldLog('error')) console.error(formatMsg('error', msg, data));
  },
  // Track user actions for analytics
  track(event, properties = {}) {
    if (shouldLog('info')) {
      console.info(formatMsg('track', event, properties));
    }
  },
  // Track API calls
  api(method, path, status, duration) {
    if (shouldLog('info')) {
      console.info(formatMsg('api', `${method} ${path} → ${status} (${duration}ms)`));
    }
  },
};

export default logger;
