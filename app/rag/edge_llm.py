"""
Supabase Edge Function integration for ZenGlow RAG pipeline.
Used for egress (LLM generation or data retrieval).
"""
import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

EDGE_FUNCTION_NAME = os.environ.get("SUPABASE_EDGE_FUNCTION", "get_gemma_response")

def get_edge_model_response(prompt: str) -> str:
    try:
        response = supabase.functions.invoke(
            EDGE_FUNCTION_NAME,
            invoke_options={
                "body": {"prompt": prompt},
                "headers": {"Content-Type": "application/json"}
            }
        )
        return response.data
    except Exception as e:
        print(f"Error calling Edge Function: {e}")
        return None
