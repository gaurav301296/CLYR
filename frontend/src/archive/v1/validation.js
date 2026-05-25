/**
 * Centralized form validation utilities for CLYR frontend.
 */

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB in bytes
const ALLOWED_FILE_TYPES = ['application/pdf'];

/**
 * Validate an email address format.
 * @param {string} email
 * @returns {{ valid: boolean, error: string }}
 */
export function validateEmail(email) {
  const value = (email || '').trim();
  if (!value) {
    return { valid: false, error: 'Email is required' };
  }
  if (!EMAIL_REGEX.test(value)) {
    return { valid: false, error: 'Please enter a valid email address' };
  }
  return { valid: true, error: '' };
}

/**
 * Validate a password (minimum 6 characters).
 * @param {string} password
 * @returns {{ valid: boolean, error: string }}
 */
export function validatePassword(password) {
  if (!password) {
    return { valid: false, error: 'Password is required' };
  }
  if (password.length < 6) {
    return { valid: false, error: 'Password must be at least 6 characters' };
  }
  return { valid: true, error: '' };
}

/**
 * Validate that a value is not empty.
 * @param {string} value
 * @param {string} [fieldName='This field']
 * @returns {{ valid: boolean, error: string }}
 */
export function validateRequired(value, fieldName = 'This field') {
  const trimmed = (value || '').trim();
  if (!trimmed) {
    return { valid: false, error: `${fieldName} is required` };
  }
  return { valid: true, error: '' };
}

/**
 * Validate a file: must be PDF and <= 10MB.
 * @param {File|null} file
 * @returns {{ valid: boolean, error: string }}
 */
export function validateFile(file) {
  if (!file) {
    return { valid: false, error: 'Please select a file' };
  }
  if (!ALLOWED_FILE_TYPES.includes(file.type)) {
    return { valid: false, error: 'Only PDF files are accepted' };
  }
  if (file.size > MAX_FILE_SIZE) {
    return { valid: false, error: 'File size must be under 10MB' };
  }
  return { valid: true, error: '' };
}
