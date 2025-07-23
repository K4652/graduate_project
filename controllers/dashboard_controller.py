from flask import render_template, redirect, url_for, session, make_response

def dashboard():
    # 1) 로그인 여부 체크 (session 키 통일)
    if 'user_name' not in session:
        return redirect(url_for('login'))

    # 2) 템플릿 렌더 → 응답 객체 생성
    resp = make_response(render_template('dashboard.html'))
    
    # 3) 캐시 방지 헤더 (이 뷰에만)
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    resp.headers['Pragma']        = 'no-cache'
    resp.headers['Expires']       = '0'

    return resp