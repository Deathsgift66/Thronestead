# Project Name: Thronestead©
# File Name: legal.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: legal.py
Role: API routes for legal.
Version: 2025-06-21
"""

from fastapi import APIRouter, HTTPException

from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/legal", tags=["legal"])


@router.get("/documents")
def list_documents():
    """
    📚 Retrieve all legal documents (ToS, Privacy Policy, etc.)

    Returns:
        - id (int): Unique document ID
        - title (str): Name of the legal document
        - summary (str): Short summary or description
        - url (str): Link to full document
    """
    supabase = get_supabase_client()
    try:
        response = (
            supabase.table("legal_documents")
            .select("id,title,summary,url,display_order")
            .order("display_order")
            .execute()
        )
        rows = getattr(response, "data", response) or []
    except Exception as e:
        # Handles database/API errors gracefully
        raise HTTPException(status_code=500, detail="Failed to fetch documents") from e

    documents = [
        {
            "id": r.get("id"),
            "title": r.get("title"),
            "summary": r.get("summary"),
            "url": r.get("url"),
        }
        for r in rows
    ]

    return {"documents": documents}
