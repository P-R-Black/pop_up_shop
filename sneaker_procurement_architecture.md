# Sneaker Procurement System — Architecture & Design - ChatGPT Version

## Overview

This document outlines the architecture and design for a modular sneaker procurement system intended to:

1. Monitor sneaker releases.
2. Attempt retail checkout through supported retailers.
3. Prioritize authenticity and retail purchasing.
4. Support future concierge-style procurement requests.
5. Remain extensible so new retailer integrations can be added independently.

---

# Core Goals

## Phase 1
- Support Nike SNKRS / Nike releases
- Detect release availability
- Attempt carting and checkout
- Record outcomes

## Phase 2
Add additional retailers:
- Foot Locker
- Adidas
- New Balance
- Supreme

## Phase 3
Add concierge procurement:
- User-specific requests
- Size preferences
- Retailer preferences
- Reservation/payment workflows

---

# Architectural Principles

## 1. Modular Retailer Integrations

Each retailer should implement a shared interface:

```python
class RetailerAdapter:
    def monitor_release(self):
        pass

    def add_to_cart(self):
        pass

    def checkout(self):
        pass
```

Examples:
- NikeAdapter
- FootlockerAdapter
- AdidasAdapter
- SupremeAdapter

The procurement engine should never contain retailer-specific logic.

---

## 2. Queue-Based Execution

Use:
- Celery
- Redis

Django creates procurement jobs.
Workers process procurement attempts asynchronously.

Benefits:
- prevents blocked requests
- improves scaling
- isolates failures

---

## 3. Stateless Workers

Workers should:
- receive tasks
- execute automation
- return results

Application state should live in:
- PostgreSQL
- Redis
- encrypted storage

---

# Recommended Tech Stack

## Backend
- Django

## Queue System
- Celery
- Redis

## Browser Automation
- Playwright (recommended over Selenium)

Reasons:
- modern API
- better async support
- stronger browser tooling
- easier debugging
- better selector handling

## Database
- PostgreSQL

## Cache / Coordination
- Redis

---

# System Components

## 1. Product Monitoring Service

Responsible for:
- release monitoring
- stock detection
- queue detection

Inputs:
- SKU
- release URL
- retailer
- release time

Outputs:
- release events

---

## 2. Procurement Engine

Responsible for:
- orchestration
- retailer prioritization
- scheduling
- execution tracking

---

## 3. Retailer Adapter Layer

Each retailer has isolated automation logic.

Structure example:

```text
retailers/
├── nike/
├── footlocker/
├── adidas/
└── supreme/
```

---

## 4. Browser Automation Layer

Responsible for:
- sessions
- cookies
- retries
- screenshots
- diagnostics

---

## 5. Checkout Service

Responsible for:
- payment access
- billing profiles
- shipping profiles

Never store raw payment data in plaintext.

---

## 6. Notification Service

Responsible for:
- procurement success
- failures
- retries
- concierge updates

Channels:
- email
- SMS (future)
- push notifications (future)

---

# Suggested Folder Structure

```text
procurement/
│
├── core/
├── retailers/
├── automation/
├── checkout/
├── tasks/
├── concierge/
└── analytics/
```

---

# Suggested Django Models

## ProcurementRequest

```text
- user
- product
- sku
- retailer
- size
- status
- max_price
- procurement_type
```

## ProcurementAttempt

```text
- request
- retailer
- started_at
- ended_at
- result
- carted
- checked_out
- logs
```

## RetailerProfile

```text
- retailer_name
- account_email
- cookies
- session_tokens
```

## PaymentProfile

```text
- encrypted_payment_token
- billing_address
- shipping_address
```

---

# Procurement Workflow

## Internal Procurement Flow

1. Users show interest in sneakers
2. System aggregates demand
3. Admin approves procurement
4. Procurement engine schedules tasks
5. Retailer workers execute
6. Inventory and auctions are created

---

# Future Concierge Workflow

Users submit:
- SKU
- retailer preference
- size
- max spend

System:
- validates request
- reserves deposit
- schedules procurement
- attempts purchase
- captures payment

---

# Browser Automation Strategy

## Browser Context Isolation

Each task should use isolated browser contexts.

Benefits:
- separate cookies
- independent retries
- cleaner sessions

---

## Selector Strategy

Prefer:
- data attributes
- accessibility labels
- stable identifiers

Avoid:
- deeply nested selectors
- generated class names

---

# Security Architecture

## Payment Security

Do NOT:
- store plaintext CVV
- expose payment logs
- expose tokens

Use:
- encryption at rest
- environment variables
- vault-style secret storage

---

## Environment Security

Never commit:
- API keys
- tokens
- cookies
- payment data

Use:
- .env
- secret managers later

---

# Reliability Features

## Retry System

Implement:
- exponential backoff
- retailer-specific retry logic
- task deduplication

---

## Diagnostics

Capture:
- screenshots
- logs
- HTML snapshots

Useful for:
- debugging
- selector drift
- retailer UI changes

---

# Scaling Considerations

Future support for:
- distributed workers
- containerized execution
- cloud execution
- retailer-specific worker pools

---

# Recommended Development Order

## Phase 1 — Foundation
Build:
- Django models
- Celery infrastructure
- Playwright infrastructure
- retailer adapter interface

## Phase 2 — Nike Integration
Build:
- release monitoring
- product detection
- size selection
- cart attempts
- checkout attempts

Focus on:
- stability
- observability
- architecture

## Phase 3 — Internal Procurement
Build:
- demand aggregation
- inventory creation
- admin tools
- notifications

## Phase 4 — Multi-Retailer Support
Add:
- Footlocker
- Adidas
- New Balance
- Supreme

## Phase 5 — Concierge Procurement
Build:
- user-specific requests
- deposits
- prioritization
- fulfillment workflows

---

# Final Guidance

Avoid:
- retailer-specific logic everywhere
- synchronous execution
- overengineering too early

Keep:
- automation
- orchestration
- checkout
- notifications

loosely coupled and modular.

---

# Long-Term Vision

A modular procurement platform with:
- retailer adapters
- concierge workflows
- inventory integration
- auction integration
- analytics
- fulfillment management

Core objective:

"A procurement system where retailers, workflows, and automation strategies evolve independently without rewriting the core engine."
