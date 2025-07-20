import pymysql
from config import Config

def get_db_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

def fetch_all_violations():
    """
    violation_result 테이블의 모든 행을 가져옵니다.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT
                  id,
                  video_name,
                  violation_type,
                  helmet_violation
                FROM violation_result
            """
            cur.execute(sql)
            return cur.fetchall()   # [{ 'id':1, 'video_name':'foo.mp4', ... }, …]
    finally:
        conn.close()

def fetch_violation_by_video(video_name):
    """
    주어진 video_name 에 매칭되는 위반 정보를 하나 가져옵니다.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT violation_type, helmet_violation
                  FROM violation_result
                 WHERE video_name = %s
            """
            cur.execute(sql, (video_name,))
            return cur.fetchone()   # { 'violation_type':…, 'helmet_violation':… } or None
    finally:
        conn.close()