import pymysql
import hashlib
import os, sys
# ─── 프로젝트 루트(한 단계 위) 를 파이썬 모듈 검색 경로에 추가 ───
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import Config   # 절대 import 로 복원

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

def save_user(name, email, password, join_code):
    password_hash = hash_text(password)
    join_code_hash = hash_text(join_code)

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO users (name, email, password_hash, join_code_hash)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (name, email, password_hash, join_code_hash))
        conn.commit()
    finally:
        conn.close()

def verify_user(email, password):
    password_hash = hash_text(password)

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM users WHERE email = %s AND password_hash = %s"
            cursor.execute(sql, (email, password_hash))
            return cursor.fetchone() is not None
    finally:
        conn.close()

def get_user_by_email(email: str) -> dict:
    """이메일로 사용자 조회 (로그인 이후 session 에 이름을 저장할 때 사용)"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, name, email FROM users WHERE email = %s"
            cursor.execute(sql, (email,))
            return cursor.fetchone()
    finally:
        conn.close()