import os
import sys
from dotenv import load_dotenv
from core.common.log import logger

def main():
    load_dotenv()
    sql_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "sql", "auth_sessions.sql")
    )
    logger.warning(
        "已移除 psycopg2 依赖，自动 SQL 迁移脚本停用。"
        f"请在 Supabase SQL Editor 手动执行: {sql_path}"
    )
    sys.exit(1)

if __name__ == "__main__":
    main()
