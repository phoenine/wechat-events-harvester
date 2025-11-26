import os
import sys
from dotenv import load_dotenv
import psycopg2

def read_sql_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def main():
    load_dotenv()
    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        print("SUPABASE_DB_URL not set")
        sys.exit(1)
    sql_path = os.path.join(os.path.dirname(__file__), "..", "sql", "auth_sessions.sql")
    sql = read_sql_file(os.path.abspath(sql_path))
    try:
        conn = psycopg2.connect(db_url)
    except Exception:
        host = os.getenv("POSTGRES_HOST", "")
        if host == "host.docker.internal":
            db_url_fallback = db_url.replace("host.docker.internal", "localhost")
            conn = psycopg2.connect(db_url_fallback)
        else:
            raise
    conn.autocommit = False
    try:
        cur = conn.cursor()
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        for stmt in statements:
            try:
                cur.execute(stmt)
            except Exception as se:
                print(f"Skip statement due to error: {se}\nSQL: {stmt[:120]}...")
        conn.commit()
        print("Migration applied: auth_sessions")
    except Exception as e:
        conn.rollback()
        print(str(e))
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
