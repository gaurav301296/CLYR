# DPDP Act 2023 Compliance -- CLYR

## Overview

The Digital Personal Data Protection Act, 2023 (India) applies to CLYR because we process personal data of Indian citizens including:
- Names, email addresses, phone numbers
- Credit scores and financial history
- PAN numbers (in some reports)
- Account details and payment information

## Data Principal Rights Implementation

### 1. Right to Access (Section 7)
**Implementation:** `GET /api/user/me` returns all profile data. `GET /api/user/reports` returns all report data.

### 2. Right to Correction (Section 8)
**Implementation:** Users can update their profile via `PATCH /api/user/me`. Report data is regenerated on re-upload.

### 3. Right to Erasure (Section 9)
**Implementation:** `DELETE /api/user/me` triggers:
- Profile deletion from `public.profiles`
- All reports deletion from `public.reports`
- All orders deletion from `public.orders`
- Auth user deletion from `auth.users`
- Temp file cleanup (already implemented with secure overwrite)

### 4. Right to Grievance Redressal (Section 10)
**Implementation:** Support email in footer. Response within 72 hours as required.

### 5. Right to Nominate (Section 11)
**Implementation:** Profile includes nominee field.

## Data Fiduciary Obligations

### Consent Management
- Explicit consent collected at signup
- Consent recorded in `auth.users.raw_user_meta_data`
- Withdrawal via account deletion

### Data Minimization
- Only collect data necessary for credit report analysis
- No tracking beyond product analytics (PostHog)
- Credit report PDFs are processed in-memory and never stored permanently

### Purpose Limitation
- Data used ONLY for credit report analysis and recovery roadmap generation
- No data sold to third parties
- No advertising or profiling

### Storage Limitation
- Temp files: deleted immediately after processing (secure overwrite)
- Reports: retained until user deletes account
- Orders: retained for 7 years (Indian tax law requirement)
- Analytics: anonymized after 12 months

### Data Security
- Encryption at rest: Supabase PostgreSQL (AES-256)
- Encryption in transit: TLS 1.3
- Access control: Row Level Security on all tables
- Audit logging: All security events logged

## Data Processing Agreement

All subprocessors (Supabase, Razorpay, OpenAI, PostHog) have DPAs available:
- Supabase: https://supabase.com/legal/dpa
- Razorpay: https://razorpay.com/dpa/
- OpenAI: https://openai.com/policies/data-processing-addendum
- PostHog: https://posthog.com/legal/dpa

## Breach Notification

In case of a data breach:
1. Notify affected users within 72 hours
2. Notify Data Protection Board of India within 72 hours
3. Document breach details, impact, and remediation steps
4. Provide free credit monitoring to affected users for 12 months

## Cross-Border Data Transfer

- Supabase: Data stored in Mumbai region (ap-south-1)
- OpenAI: Data may be processed in US (covered by DPA)
- PostHog: EU data residency available
- Razorpay: Data stored in India

## Compliance Checklist

- [x] Privacy policy published
- [x] Terms of service published
- [x] Consent collection at signup
- [x] Data access API implemented
- [x] Data correction API implemented
- [x] Data erasure API implemented
- [x] Security event logging implemented
- [x] Encryption at rest and in transit
- [x] Row Level Security on all tables
- [x] DPA with all subprocessors
- [x] Breach notification procedure documented
- [ ] Data Protection Officer appointed (required for significant data fiduciaries)
- [ ] Annual data protection audit scheduled
- [ ] Data protection impact assessment completed
