/**
 * CLYR v2 — API Client Layer
 * Centralized fetch wrapper with auth, error handling, and file upload.
 */
import { config } from '../config';

const BASE_URL = config.API_BASE || 'http://localhost:8005/api';

function getToken() {
  return localStorage.getItem('clyr_token');
}

function handleAuthError() {
  localStorage.removeItem('clyr_token');
  // Don't redirect — let the auth context handle it
}

export async function apiFetch(path, options = {}) {
  const url = `${BASE_URL}${path}`;

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url, { ...options, headers });

  const contentType = response.headers.get('content-type');
  const body =
    contentType && contentType.includes('application/json')
      ? await response.json().catch(() => null)
      : await response.text().catch(() => null);

  if (response.status === 401) {
    handleAuthError();
    const err = new Error('Authentication required');
    err.status = 401;
    throw err;
  }

  if (!response.ok) {
    const message =
      body && body.detail ? body.detail :
      body && body.message ? body.message :
      response.statusText || 'Request failed';
    const error = new Error(message);
    error.status = response.status;
    error.body = body;
    throw error;
  }

  return body;
}

export async function apiUpload(path, formData, options = {}) {
  const url = `${BASE_URL}${path}`;

  const headers = { ...options.headers };
  // Intentionally omit Content-Type so browser sets multipart boundary

  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method: 'POST',
    ...options,
    headers,
    body: formData,
  });

  const contentType = response.headers.get('content-type');
  const body =
    contentType && contentType.includes('application/json')
      ? await response.json().catch(() => null)
      : await response.text().catch(() => null);

  if (response.status === 401) {
    handleAuthError();
    const err = new Error('Authentication required');
    err.status = 401;
    throw err;
  }

  if (!response.ok) {
    const message =
      body && body.detail ? body.detail :
      body && body.message ? body.message :
      response.statusText || 'Upload failed';
    const error = new Error(message);
    error.status = response.status;
    error.body = body;
    throw error;
  }

  return body;
}
