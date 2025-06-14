# Project Name: Kingmakers Rise©
# File Name: __init__.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
This __init__.py initializes the core backend package for Kingmakers Rise©.
It sets up environment access, logging, Supabase integration, and utility loading.
This file assumes FastAPI app structure, Supabase SDK, and environment-based configuration.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Load .env variables (Render environment uses system variables by default)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KingmakersRise")

# Supabase configuration from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role key for backend tasks

# Validate config
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase credentials missing. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
    raise EnvironmentError("Supabase configuration incomplete.")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Exported objects from module
__all__ = ["supabase", "logger"]
