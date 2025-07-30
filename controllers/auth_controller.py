from flask import (
    render_template, request, redirect, url_for,
    session, flash, make_response
)
from models.user_model import save_user, verify_user, get_user_by_email
from models.join_code_model import is_valid_join_code


def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        join_code = request.form.get('access_code')

        print(f"[DEBUG] 입력된 가입코드: {join_code!r}")

        if not (name and email and password and join_code):
            flash('모든 항목을 입력해주세요.', 'warning')
            return render_template('signup.html'), 400

        if not is_valid_join_code(join_code):
            flash('유효하지 않은 가입 코드입니다.', 'warning')
            return render_template('signup.html'), 400

        save_user(name, email, password, join_code)

        # — 여기서 세션에 사용자 이름을 저장
        session['user_name'] = name

        return redirect(url_for('login'))

    return render_template('signup.html')


def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if verify_user(email, password):
            user = get_user_by_email(email)
            # 세션에 사용자 이름 저장
            session['user_name'] = user['name']
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('이메일 또는 비밀번호가 틀렸습니다.', 'danger')
            return render_template('login.html'), 401
    return render_template('login.html')

def logout():
    # 1) 세션에서 사용자 정보 제거
    session.pop('user_name', None)
    # 2) 플래시 메시지
    flash('로그아웃되었습니다.', 'info')
    # 3) 로그인 페이지로 리다이렉트할 응답 객체 생성
    resp = make_response(redirect(url_for('login')))
    # 4) 이 응답에만 캐시 방지 헤더 추가
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    resp.headers['Pragma']        = 'no-cache'
    resp.headers['Expires']       = '0'
    return resp