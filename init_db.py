# init_db.py
import pymysql
from config import Config

# 1) 루트 연결 (아직 DB는 지정하지 않음)
conn = pymysql.connect(
    host=Config.DB_HOST,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with conn.cursor() as cur:
        # 2) 데이터베이스 생성
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    conn.commit()
finally:
    conn.close()

# 3) 방금 만든 DB에 연결해서 테이블 생성
conn = pymysql.connect(
    host=Config.DB_HOST,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    database=Config.DB_NAME,
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with conn.cursor() as cur:
        # users 테이블
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            join_code_hash VARCHAR(64) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # join_codes 테이블
        cur.execute("""
        CREATE TABLE IF NOT EXISTS join_codes (
            id INT PRIMARY KEY AUTO_INCREMENT,
            code_hash VARCHAR(255) NOT NULL,
            description VARCHAR(100)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # public_reports 테이블
        cur.execute("""
        CREATE TABLE IF NOT EXISTS public_reports (
            report_id      INT AUTO_INCREMENT PRIMARY KEY,
            media_path     VARCHAR(255) NOT NULL,
            location       VARCHAR(255) NOT NULL,
            title          VARCHAR(100) NOT NULL,
            content        TEXT NOT NULL,
            vehicle_number VARCHAR(20),
            incident_date  DATE NOT NULL,
            incident_time  TIME NOT NULL,
            phone_number   VARCHAR(20),
            reporter_type  ENUM('개인','기관','단체','기업') NOT NULL,
            reporter_name  VARCHAR(50) NOT NULL,
            reporter_email VARCHAR(100) NOT NULL,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # violation_result 테이블
        cur.execute("""
        CREATE TABLE IF NOT EXISTS violation_result (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            video_name       VARCHAR(255),
            violation_type   VARCHAR(20),
            helmet_violation VARCHAR(20)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # violation_frame 테이블
        cur.execute("""
        CREATE TABLE IF NOT EXISTS violation_frame (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            result_id   INT,
            frame_type  VARCHAR(20),
            frame_index INT,
            image_path  VARCHAR(255),
            FOREIGN KEY (result_id) REFERENCES violation_result(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
    conn.commit()
finally:
    conn.close()

print("✅ 데이터베이스 및 테이블 생성 완료")