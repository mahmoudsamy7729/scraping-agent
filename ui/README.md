# Agent Dashboard (Next.js)

## Setup

1. Install deps:
   - npm install
2. Create env file:
   - copy .env.example .env.local
3. Run dev server:
   - npm run dev

The dashboard runs on http://localhost:3000 and proxies backend calls through Next.js API routes to avoid CORS issues.

## Environment

- AGENT_API_BASE_URL: Base URL for FastAPI agent (default: http://127.0.0.1:8000)

