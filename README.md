# 🚀 OmniLead AI

> AI-powered omnichannel lead intelligence and sales management platform that unifies customer interactions, prioritizes leads, automates follow-ups, and provides AI-driven sales insights.

![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![pgvector](https://img.shields.io/badge/pgvector-Vector_Search-336791?style=for-the-badge)
![Supabase](https://img.shields.io/badge/Supabase-Auth_%26_Data-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-AI_Workflows-1C3C3C?style=for-the-badge)
![Gemini](https://img.shields.io/badge/Google_Gemini-LLM-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-Background_Jobs-37814A?style=for-the-badge)
![Redis](https://img.shields.io/badge/Redis-Task_Queue-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-E2E-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-Testing-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)

> **Status:** 🚧 Active Development  
> **Deployment:** Not publicly deployed yet

---

## 📌 Overview

**OmniLead AI** is an AI-powered omnichannel lead intelligence and sales management platform designed to unify customer interactions, CRM workflows, and AI-powered sales intelligence in one system.

Modern sales teams interact with prospects through multiple channels such as WhatsApp, Instagram, email, phone calls, web enquiries, and direct conversations. When this information is fragmented, businesses can lose customer context, miss follow-ups, create duplicate records, and struggle to identify high-value opportunities.

OmniLead AI addresses this problem through a unified customer identity, CRM workflows, AI-powered intelligence, semantic search, conversation analysis, call intelligence, and workflow automation.

### Core Workflow

```text
Customer Interactions
        ↓
Unified Customer Identity
        ↓
CRM Data + Conversations
        ↓
AI Intelligence
        ↓
Lead Scoring & Prioritization
        ↓
Recommended Actions
        ↓
Follow-Ups & Sales Execution
        ↓
Analytics & Feedback
```

---

## 🎯 Problem Statement

Modern sales teams often manage customer information across disconnected platforms and communication channels.

This creates problems such as:

- Fragmented customer information
- Duplicate customer records
- Lost conversation context
- Missed follow-ups
- Manual lead prioritization
- Limited visibility into customer conversations
- Time-consuming call reviews
- Scattered product and enquiry information
- Difficulty converting customer activity into actionable sales intelligence

**OmniLead AI is designed to transform fragmented customer activity into structured, actionable sales intelligence.**

---

## 💡 What OmniLead AI Can Do

### 👤 Unified Customer Management

OmniLead AI separates a customer from their individual channel identities.

A customer can have multiple identities:

```text
Customer
 ├── Email
 ├── Phone
 ├── Instagram
 └── WhatsApp
```

This allows customer context to remain consistent across communication channels and reduces duplicate customer records.

### 🎯 Lead Intelligence

The platform provides foundations for:

- Lead creation and management
- Lead prioritization
- AI-assisted lead scoring
- Lead activity tracking
- Priority queues
- Sales pipeline workflows
- Lead-to-customer relationships
- Next-action recommendations

### 🧠 AI Sales Intelligence

The AI layer is designed to analyze CRM and interaction data to provide:

- Lead analysis
- Buying-intent signals
- Conversation insights
- Sales recommendations
- AI-assisted reviews
- Semantic retrieval
- Workflow-based AI reasoning
- Next-best-action suggestions

### 💬 Conversation Intelligence

Customer conversations are treated as first-class business data.

The platform provides foundations for:

- Conversation history
- Interaction tracking
- Customer context
- Conversation analysis
- AI-assisted insights
- Semantic retrieval

### 📞 Call Intelligence

OmniLead AI includes a dedicated call-intelligence architecture using **Faster-Whisper**.

```text
Audio Upload
     ↓
Validation
     ↓
Faster-Whisper
     ↓
Transcription
     ↓
Conversation Data
     ↓
AI Analysis
     ↓
Sales Insights
```

This provides the foundation for:

- Call transcription
- Call summarization
- Objection detection
- Conversation analysis
- Sales call scoring
- Sales coaching recommendations

### ⏰ Follow-Up Management

The platform supports:

- Follow-up tracking
- Upcoming sales actions
- Reminders
- Automated communication
- Scheduled workflows
- Background processing

Long-running and scheduled operations are designed around:

```text
Celery + Redis
```

### 🛍️ Products & Enquiries

Products and enquiries can be connected with:

```text
Customers
Leads
Conversations
Interactions
Follow-Ups
Sales Workflows
AI Recommendations
```

This creates a structured path from customer enquiry to sales execution.

### 📊 Sales Analytics

The dashboard and analytics architecture provides foundations for:

- Lead activity
- Sales activity
- Pipeline information
- Customer interactions
- Follow-up activity
- Sales performance
- AI-derived insights

### 👥 Team & Organization Management

The architecture supports multi-user sales environments through:

```text
Organizations
Users
Teams
Roles
Authentication
Authorization
```

### 🔔 Notifications

The notification system provides foundations for:

- Follow-up reminders
- Sales activity alerts
- Workflow events
- AI recommendations
- System notifications

---

## 🌐 Omnichannel Architecture

```text
                    Customer Channels
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
     WhatsApp         Instagram          Email
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ↓
                Unified Customer Identity
                          ↓
              ┌───────────┼───────────┐
              ↓           ↓           ↓
            Leads    Conversations   Calls
              │           │           │
              └───────────┼───────────┘
                          ↓
                   AI Intelligence
                          ↓
              ┌───────────┼───────────┐
              ↓           ↓           ↓
           Scoring     Insights    Follow-Ups
```

---

## 🏗️ System Architecture

```text
┌──────────────────────────────────────────────────────┐
│                  React + TypeScript                  │
│                                                      │
│ Dashboard │ Leads │ Customers │ Calls │ Analytics    │
│ Enquiries │ Follow-Ups │ AI Review │ Settings        │
└──────────────────────────┬───────────────────────────┘
                           │
                           │ REST API
                           ↓
┌──────────────────────────────────────────────────────┐
│                    FastAPI Backend                   │
│                                                      │
│ CRM │ AI │ Search │ Analytics │ Integrations         │
│ Auth │ Calls │ Conversations │ Webhooks              │
└───────────────┬──────────────────────┬───────────────┘
                │                      │
                ↓                      ↓
       PostgreSQL + pgvector       AI Intelligence
                                      │
                            ┌─────────┼─────────┐
                            ↓         ↓         ↓
                         Gemini   LangGraph  Embeddings
                                                │
                                                ↓
                                           pgvector
                │
                ↓
         Celery + Redis
       Background Processing
```

### Architectural Principles

The system is designed around:

- Separation of concerns
- Modular backend architecture
- Feature-based frontend architecture
- AI provider abstraction
- Organization-aware data
- API versioning
- Asynchronous processing
- Environment-driven configuration
- Human-in-the-loop AI workflows
- Testability and observability

---

## 🧠 AI Architecture

OmniLead AI is designed around structured AI workflows rather than a simple chatbot.

```text
Input
  ↓
Context Retrieval
  ↓
Business Rules / Guards
  ↓
LLM Reasoning
  ↓
Structured Output
  ↓
Validation
  ↓
Business Action
```

The AI layer contains dedicated components for:

```text
contracts/
guards/
observability/
prompts/
providers/
retrieval/
scoring/
workflows/
```

This separation allows AI capabilities to evolve independently from the core CRM application.

### AI Stack

```text
Google Gemini
      ↓
LangGraph
      ↓
AI Workflows
      ↓
Sentence Transformers
      ↓
Vector Embeddings
      ↓
PostgreSQL + pgvector
```

---

## 🔎 Semantic Search

Semantic search is built around:

```text
Sentence Transformers
        ↓
Vector Embeddings
        ↓
PostgreSQL + pgvector
        ↓
Semantic Retrieval
        ↓
AI Context
```

The architecture provides a foundation for semantic retrieval across:

- Customers
- Conversations
- Interactions
- Products
- Enquiries
- Sales information

---

## 🤖 Human-in-the-Loop AI

OmniLead AI follows an AI-assisted approach:

```text
AI Analyzes
     ↓
AI Recommends
     ↓
Sales Representative Reviews
     ↓
Human Takes Action
     ↓
CRM Records Outcome
```

AI-generated scores, recommendations, classifications, and summaries are intended as decision-support signals rather than absolute truth.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 18, TypeScript, Vite |
| UI | Tailwind CSS, Lucide React |
| Routing | React Router |
| Server State | TanStack React Query |
| Client State | Zustand |
| Forms | React Hook Form, Zod |
| Visualization | Recharts |
| Backend | Python 3.12, FastAPI |
| API Validation | Pydantic |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Database | PostgreSQL |
| Vector Search | pgvector |
| Authentication | Supabase, JWT |
| LLM | Google Gemini |
| AI Orchestration | LangGraph |
| Embeddings | Sentence Transformers |
| Speech-to-Text | Faster-Whisper |
| Background Jobs | Celery |
| Task Queue | Redis |
| Email | Resend |
| HTTP Client | HTTPX |
| Logging | Structlog |
| Backend Testing | Pytest |
| Frontend Testing | Vitest, Testing Library |
| E2E Testing | Playwright |
| Code Quality | Ruff, ESLint, Pre-commit |
| Infrastructure | Docker |
| Version Control | Git, GitHub |

---

## 📂 Project Structure

```text
OmniLead-AI/
│
├── .github/
│   └── workflows/
│
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── contracts/
│   │   │   ├── guards/
│   │   │   ├── observability/
│   │   │   ├── prompts/
│   │   │   ├── providers/
│   │   │   ├── retrieval/
│   │   │   ├── scoring/
│   │   │   └── workflows/
│   │   │
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── integrations/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── services/
│   │
│   ├── alembic/
│   └── tests/
│
├── frontend/
│   └── src/
│       ├── api/
│       ├── components/
│       ├── features/
│       ├── layouts/
│       ├── pages/
│       ├── stores/
│       ├── styles/
│       └── types/
│
├── demo/
├── docs/
├── evaluation/
├── infra/
├── scripts/
├── tests/
│   └── e2e/
│
├── .env.example
├── CONTRIBUTING.md
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── LICENSE
├── Makefile
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12
- Node.js
- npm
- PostgreSQL
- Redis
- Git
- Docker *(optional)*

### Clone Repository

```bash
git clone https://github.com/Ebbeju-Lankapalli/OmniLead-AI.git
cd OmniLead-AI
```

### Backend Setup

```bash
conda create -n omnilead-ai python=3.12
conda activate omnilead-ai

cd backend
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Environment Configuration

From the project root:

```bash
cp .env.example .env
```

Configure the required database, authentication, AI, Redis, and integration credentials.

> Never commit `.env` or production credentials.

### Database Migration

```bash
cd backend
alembic upgrade head
```

### Start Backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Start Frontend

In another terminal:

```bash
cd frontend
npm run dev
```

### Local URLs

```text
Frontend → http://localhost:5173
Backend  → http://127.0.0.1:8000
API Docs → http://127.0.0.1:8000/docs
```

---

## 🧪 Testing

OmniLead AI uses multiple testing layers.

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

### End-to-End Tests

From the project root:

```bash
npm run e2e
```

Interactive mode:

```bash
npm run e2e:ui
```

Headed mode:

```bash
npm run e2e:headed
```

View the report:

```bash
npm run e2e:report
```

### Full Validation

```bash
npm run test:all
```

Testing stack:

```text
Pytest
Vitest
Testing Library
Playwright
```

---

## 🔐 Security

Security is treated as a core production requirement.

The project provides foundations for:

- JWT authentication
- Supabase authentication
- CORS allow-listing
- Rate limiting
- Webhook signature validation
- File upload validation
- Environment-based secrets
- Structured logging
- Organization-aware data access

### Never expose server-side secrets

The following must remain backend-only:

```text
DATABASE_URL
GEMINI_API_KEY
SUPABASE_SERVICE_ROLE_KEY
META_APP_SECRET
WHATSAPP_ACCESS_TOKEN
INSTAGRAM_ACCESS_TOKEN
RESEND_API_KEY
LANGSMITH_API_KEY
```

Do not place these in frontend `VITE_*` variables.

See [`SECURITY.md`](SECURITY.md) for security guidance.

---

## 📈 Production Readiness

> **OmniLead AI is currently under active development and is not publicly deployed.**

The architecture is intentionally designed with production-oriented foundations rather than as a simple prototype.

Current foundations include:

```text
Modular Backend
Feature-Based Frontend
API Versioning
PostgreSQL
Database Migrations
Authentication
AI Provider Abstraction
Vector Search
Background Jobs
External Integrations
Automated Testing
E2E Testing
Docker Support
Security Configuration
Environment-Based Configuration
```

### Path to Production

```text
Complete Test Coverage
        ↓
Security Hardening
        ↓
Observability & Monitoring
        ↓
Performance Optimization
        ↓
Containerized Deployment
        ↓
CI/CD
        ↓
Managed PostgreSQL + Redis
        ↓
Cloud Deployment
        ↓
Production Monitoring
```

A production deployment would additionally require:

- Managed PostgreSQL
- Managed Redis
- Secure secret management
- Horizontal API scaling
- Worker scaling
- Object storage for audio and media
- Centralized logging
- Metrics and alerting
- CI/CD pipelines
- Database backups
- Disaster recovery
- Strong role-based access control
- Audit logging
- Provider/API reliability controls
- Production security testing

---

## 🗺️ Roadmap

### Core Platform

- [x] Backend architecture
- [x] Frontend architecture
- [x] Database layer
- [x] API versioning
- [x] Authentication foundation
- [x] Domain modeling
- [x] Database migrations

### CRM

- [x] Organizations
- [x] Users
- [x] Customers
- [x] Customer identities
- [x] Leads
- [x] Interactions
- [ ] Advanced conversation workflows
- [ ] Product workflows
- [ ] Enquiry workflows
- [ ] Advanced follow-up automation
- [ ] Notification workflows

### AI Intelligence

- [x] AI provider architecture
- [x] Prompt architecture
- [x] AI contracts
- [x] AI guards
- [ ] Advanced lead scoring
- [ ] AI sales recommendations
- [ ] Production semantic retrieval
- [ ] Workflow-based agents
- [ ] AI evaluation pipelines
- [ ] Production AI observability

### Omnichannel

- [ ] WhatsApp integration
- [ ] Instagram integration
- [ ] Email synchronization
- [ ] Unified interaction pipeline
- [ ] Cross-channel customer intelligence

### Call Intelligence

- [ ] Production transcription pipeline
- [ ] Call summarization
- [ ] Conversation analysis
- [ ] Objection detection
- [ ] Sales call scoring
- [ ] Coaching recommendations

### Production

- [ ] CI/CD
- [ ] Security hardening
- [ ] Production observability
- [ ] Performance optimization
- [ ] Containerized deployment
- [ ] Cloud deployment
- [ ] Production monitoring

---

## 📚 Documentation

Detailed implementation and engineering documentation is maintained separately from the main README.

```text
docs/
    ↓
Architecture
API Documentation
Development Guides
Deployment Documentation
Technical Decisions
```

Additional repository documentation:

- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`SECURITY.md`](SECURITY.md)
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- [`evaluation/`](evaluation/)

The README intentionally focuses on the product, architecture, capabilities, technology stack, setup, and production direction.

---

## 🎯 Engineering Highlights

OmniLead AI demonstrates practical engineering across:

```text
AI Engineering
Generative AI
LLM Applications
Agentic Workflows
Semantic Search
Vector Databases
Speech-to-Text
CRM Architecture
Omnichannel Systems
FastAPI
React + TypeScript
PostgreSQL
Distributed Background Jobs
Authentication
REST API Design
Testing
Docker
Security
Production-Oriented Architecture
```

The project emphasizes an important engineering principle:

> **AI should enhance a reliable software system — not replace the software system.**

The platform therefore separates:

```text
CRM Data
Business Logic
AI Intelligence
External Integrations
Background Processing
Infrastructure
```

This makes the system easier to test, maintain, extend, and evolve toward production scale.

---

## ⚠️ Disclaimer

OmniLead AI is a software engineering and AI development project.

AI-generated lead scores, recommendations, summaries, classifications, and sales insights should be treated as decision-support signals rather than absolute truth.

Human sales representatives and business operators remain responsible for consequential customer and sales decisions.

External integrations and AI providers require appropriate credentials, permissions, API access, and compliance with their respective policies.

The platform should be properly secured and configured before handling real customer information or production credentials.

---

## 👨‍💻 Author

**Ebbeju Lankapalli**

B.Tech — Computer Science & Engineering  
Specialization — Artificial Intelligence & Machine Learning

Aspiring AI / ML Engineer

GitHub:  
https://github.com/Ebbeju-Lankapalli

### Areas of Interest

```text
Machine Learning
Deep Learning
Generative AI
Agentic AI
LLMs
AI Systems
MLOps
AI Engineering
Production AI Applications
Intelligent Automation
```

---

## ⭐ Support

If you find OmniLead AI interesting, consider giving the repository a ⭐.

---

> **One customer. Every channel. One intelligent sales system.**