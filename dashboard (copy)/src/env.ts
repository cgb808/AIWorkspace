export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL as string;
export const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY as string;
export const RAG_API_BASE = (import.meta.env.VITE_RAG_API_BASE as string) || 'http://localhost:8000';

if (!SUPABASE_URL) console.warn('[env] SUPABASE_URL missing');
if (!SUPABASE_ANON_KEY) console.warn('[env] SUPABASE_ANON_KEY missing');
