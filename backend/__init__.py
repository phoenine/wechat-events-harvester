import os
from core.common.log import logger

logger.info(f"DEBUG SUPABASE_URL = {os.getenv('SUPABASE_URL')}")
logger.info(f"DEBUG SUPABASE_ANON_KEY = {os.getenv('SUPABASE_ANON_KEY')}")
