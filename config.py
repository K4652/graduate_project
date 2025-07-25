import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'your-secret-key'
    # MySQL 연결 설정
    DB_HOST     = 'localhost'
    DB_USER     = 'root'
    DB_PASSWORD = '1234'
    DB_NAME     = 'traffic_db'
    DB_PORT     = 3307
    # 업로드 폴더(기존 그대로)
    UPLOAD_FOLDER    = os.path.join(BASE_DIR, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif','mp4','webm','ogg'}