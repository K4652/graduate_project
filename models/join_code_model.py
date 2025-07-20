import pymysql
import hashlib
from config import Config

def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

def get_db_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def is_valid_join_code(join_code):
    cleaned = join_code.strip()
    code_hash = hash_text(cleaned)
    print(f"[DEBUG] 해시된 코드: {code_hash}")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM join_codes WHERE code_hash = %s"
            cursor.execute(sql, (code_hash,))
            result = cursor.fetchone()
            return result is not None
    finally:
        conn.close()