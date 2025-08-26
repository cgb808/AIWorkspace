ZenGlow RAG Dashboard
=====================

Purpose
-------
Fast, lightweight operational dashboard for:

* Health status of core services (/health, /health/ollama, /health/rag)
* Interactive /rag/query2 testing with fused, conceptual, and LTR scores

Setup
-----
1. Copy `.env.example` to `.env.local` and fill values:
   * VITE_SUPABASE_URL
   * VITE_SUPABASE_ANON_KEY (anon/public key – never the service role in browser)
   * VITE_RAG_API_BASE (e.g. http://localhost:8000 or https://api.example.com)
2. Install deps and run dev server.

Run
---
`npm start`

Build
-----
`npm run build` produces static assets in `dist/` suitable for serving behind nginx or the existing proxy.

Security Notes
--------------
* Only use anon/public Supabase key client-side.
* Optionally gate the dashboard behind auth or VPN / basic auth.

Next Enhancements (Optional)
----------------------------
* Auth + role-based gating.
* Historical metrics (persist last N query latencies in Supabase or Redis -> chart).
* Streaming token-level latency breakdown.
* Live ingestion queue depth visualization.
