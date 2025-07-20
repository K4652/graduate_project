from flask import Flask, redirect, url_for, request
from config import Config

from controllers.auth_controller      import login, signup, logout
from controllers.dashboard_controller import dashboard_bp
from controllers.upload_controller    import upload_bp
from controllers.list_controller      import list_bp

import subprocess, threading, os

app = Flask(__name__)
app.config.from_object(Config)

# main.py를 별도 프로세스로 실행 (AI 처리)
def run_main_py():
    main_py_path = os.path.join(os.path.dirname(file), 'ai_models', 'main.py')
    subprocess.run(['python', main_py_path])

# 백그라운드 스레드로 main.py 실행 (AI 처리) - debug 모드에서 중복 실행 방지
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    main_thread = threading.Thread(target=run_main_py, daemon=True)
    main_thread.start()
    print("AI 모델 백그라운드 프로세스 시작")
elif not app.debug:
    main_thread = threading.Thread(target=run_main_py, daemon=True)
    main_thread.start()
    print("AI 모델 백그라운드 프로세스 시작")

# ① 루트('/') → 로그인 페이지로
@app.route('/')
def index():
    return redirect(url_for('login'))

# 기존 로그인/회원가입/대시보드 라우트
app.add_url_rule('/login',     'login',     login,   methods=['GET','POST'])
app.add_url_rule('/signup',    'signup',    signup,  methods=['GET','POST'])
app.add_url_rule('/logout', 'logout', logout)


# 블루프린트 등록
app.register_blueprint(upload_bp)  # /upload
app.register_blueprint(list_bp)    # /list
app.register_blueprint(dashboard_bp)

@app.after_request
def add_no_cache_headers(response):
    # 로그인, 회원가입, 정적리소스만 예외로 둡니다.
    exempt_paths = ['/login', '/signup']
    if (
        # request.path 가 None 이 아니고
        request.path and
        # /login, /signup 으로 정확히 시작하지 않고
        not any(request.path.startswith(ep) for ep in exempt_paths) and
        # /static/ 은 제외
        not request.path.startswith('/static/')
    ):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        response.headers['Pragma']        = 'no-cache'
        response.headers['Expires']       = '0'
    return response


# ── 커스텀 필터 등록 ──
@app.template_filter('comma')
def comma_filter(value):
    try:
        return "{:,}".format(value)
    except Exception:
        return value

if __name__ == '__main__':
    app.run(debug=True)