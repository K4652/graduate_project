from flask import Blueprint, render_template, request
import mysql.connector
from config import Config

list_bp = Blueprint('list', __name__, url_prefix='/list')

def get_db_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT
    )

# 예시 데이터 (실제로는 DB에서 가져오시면 됩니다)
SAMPLE_REPORTS = [
    {
      'id': '#05061130',
      'violation': '중앙선 침범',
      'date': '2025.04.03',
      'plate': '98지 3246',
      'starred': False
    },
    {
      'id': '#05061257',
      'violation': '안전모 미착용',
      'date': '2025.04.04',
      'plate': '22오 7534',
      'starred': True
    },
    {
      'id': '#05061130',
      'violation': '중앙선 침범',
      'date': '2025.04.03',
      'plate': '98지 3246',
      'starred': False
    },
    {
      'id': '#05061257',
      'violation': '안전모 미착용',
      'date': '2025.04.04',
      'plate': '22오 7534',
      'starred': True
    },{
      'id': '#05061130',
      'violation': '중앙선 침범',
      'date': '2025.04.03',
      'plate': '98지 3246',
      'starred': False
    },
    {
      'id': '#05061257',
      'violation': '안전모 미착용',
      'date': '2025.04.04',
      'plate': '22오 7534',
      'starred': True
    },
    {
      'id': '#05061130',
      'violation': '중앙선 침범',
      'date': '2025.04.03',
      'plate': '98지 3246',
      'starred': False
    },
    {
      'id': '#05061257',
      'violation': '안전모 미착용',
      'date': '2025.04.04',
      'plate': '22오 7534',
      'starred': True
    },
    {
      'id': '#05061130',
      'violation': '중앙선 침범',
      'date': '2025.04.03',
      'plate': '98지 3246',
      'starred': False
    },
    {
      'id': '#05061257',
      'violation': '안전모 미착용',
      'date': '2025.04.04',
      'plate': '22오 7534',
      'starred': True
    },
    {
      'id': '#05061130',
      'violation': '중앙선 침범',
      'date': '2025.04.03',
      'plate': '98지 3246',
      'starred': False
    },
    {
      'id': '#05061257',
      'violation': '안전모 미착용',
      'date': '2025.04.04',
      'plate': '22오 7534',
      'starred': True
    },
    {
      'id': '#05061130',
      'violation': '중앙선 침범',
      'date': '2025.04.03',
      'plate': '98지 3246',
      'starred': False
    },
    {
      'id': '#05061257',
      'violation': '안전모 미착용',
      'date': '2025.04.04',
      'plate': '22오 7534',
      'starred': True
    },
    {
      'id': '#05061130',
      'violation': '중앙선 침범',
      'date': '2025.04.03',
      'plate': '98지 3246',
      'starred': False
    },
    {
      'id': '#05061257',
      'violation': '안전모 미착용',
      'date': '2025.04.04',
      'plate': '22오 7534',
      'starred': True
    },
    {
      'id': '#05061130',
      'violation': '중앙선 침범',
      'date': '2025.04.03',
      'plate': '98지 3246',
      'starred': False
    },
    {
      'id': '#05061257',
      'violation': '안전모 미착용',
      'date': '2025.04.04',
      'plate': '22오 7534',
      'starred': True
    },
    {
      'id': '#05061130',
      'violation': '중앙선 침범',
      'date': '2025.04.03',
      'plate': '98지 3246',
      'starred': False
    },
    {
      'id': '#05061257',
      'violation': '안전모 미착용',
      'date': '2025.04.04',
      'plate': '22오 7534',
      'starred': True
    },
    # … 등등
]

@list_bp.route('/')
def list_view():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # AI 분석 결과와 사용자 신고를 모두 가져오기
        # 1. AI 분석 결과 (violation_result 테이블)
        cursor.execute("""
            SELECT 
                id,
                video_name,
                violation_type,
                helmet_violation
            FROM violation_result 
            ORDER BY id DESC
        """)
        ai_results = cursor.fetchall()
        
        # 2. 사용자 신고 (public_reports 테이블)
        cursor.execute("""
            SELECT 
                report_id as id,
                title,
                location,
                incident_date,
                vehicle_number,
                media_path
            FROM public_reports 
            ORDER BY report_id DESC
        """)
        user_reports = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 기존 템플릿 구조에 맞는 데이터 포맷팅
        reports = []
        
        # AI 결과 처리
        for result in ai_results:
            violation_text = ""
            if result['violation_type'] and result['violation_type'] != "위법 없음":
                violation_text += result['violation_type']
            if result['helmet_violation'] == '안전모미착용':
                if violation_text:
                    violation_text += ", "
                violation_text += "안전모 미착용"
            
            reports.append({
                'id': f"#{result['id']:08d}",
                'violation': violation_text or "위법 없음",
                'date': "2025.01.01",  # 실제로는 분석 날짜 필드가 필요
                'plate': "AI 분석",
                'location': "AI 분석",
                'video_url': f"/static/uploads/{result['video_name']}" if result['video_name'] else "#",
                'starred': False
            })
        
        # 사용자 신고 처리
        for report in user_reports:
            reports.append({
                'id': f"#{report['id']:08d}",
                'violation': report['title'],
                'date': report['incident_date'].strftime('%Y.%m.%d') if report['incident_date'] else "날짜 없음",
                'plate': report['vehicle_number'] or "번호판 없음",
                'location': report['location'],
                'video_url': report['media_path'] if report['media_path'] else "#",
                'starred': False
            })
        
        # 정렬 처리 (기존 템플릿의 JavaScript 정렬 사용)
        sort_by = request.args.get('sort_by', 'id')
        order = request.args.get('order', 'desc')
        
        return render_template('list.html',
                               reports=reports,
                               sort_by=sort_by,
                               order=order)
                               
    except Exception as e:
        print(f"데이터베이스 오류: {e}")
        # 오류 시 기존 샘플 데이터 반환
        return render_template('list.html',
                               reports=SAMPLE_REPORTS,
                               sort_by='id',
                               order='desc')

@list_bp.route('/detail/<report_id>')
def detail_view(report_id):
    # 기존 템플릿 구조에 맞게 간단한 상세 페이지
    try:
        # ID에서 # 제거하고 숫자 추출
        if report_id.startswith('#'):
            actual_id = int(report_id[1:])
        else:
            actual_id = int(report_id)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # AI 분석 결과 먼저 확인
        cursor.execute("""
            SELECT 
                id,
                video_name,
                violation_type,
                helmet_violation
            FROM violation_result 
            WHERE id = %s
        """, (actual_id,))
        ai_result = cursor.fetchone()
        
        if ai_result:
            # AI 분석 결과
            violation_text = ""
            if ai_result['violation_type'] and ai_result['violation_type'] != "위법 없음":
                violation_text += ai_result['violation_type']
            if ai_result['helmet_violation'] == '안전모미착용':
                if violation_text:
                    violation_text += ", "
                violation_text += "안전모 미착용"
            
            detail_data = {
                'id': f"#{ai_result['id']:08d}",
                'violation': violation_text or "위법 없음",
                'date': "2025.01.01",
                'plate': "AI 분석",
                'location': "AI 분석",
                'video_url': f"/static/uploads/{ai_result['video_name']}" if ai_result['video_name'] else "#"
            }
        else:
            # 사용자 신고 확인
            cursor.execute("""
                SELECT 
                    report_id,
                    title,
                    location,
                    incident_date,
                    vehicle_number,
                    media_path
                FROM public_reports 
                WHERE report_id = %s
            """, (actual_id,))
            user_result = cursor.fetchone()
            
            if user_result:
                detail_data = {
                    'id': f"#{user_result['report_id']:08d}",
                    'violation': user_result['title'],
                    'date': user_result['incident_date'].strftime('%Y.%m.%d') if user_result['incident_date'] else "날짜 없음",
                    'plate': user_result['vehicle_number'] or "번호판 없음",
                    'location': user_result['location'],
                    'video_url': user_result['media_path'] if user_result['media_path'] else "#"
                }
            else:
                return "존재하지 않는 신고입니다.", 404
        
        cursor.close()
        conn.close()
        
        # 기존 템플릿 구조에 맞는 간단한 상세 페이지 반환
        return f"""
        <html>
        <head><title>상세 정보</title></head>
        <body>
            <h2>신고 상세 정보</h2>
            <p><strong>신고 번호:</strong> {detail_data['id']}</p>
            <p><strong>위반 사항:</strong> {detail_data['violation']}</p>
            <p><strong>발생 날짜:</strong> {detail_data['date']}</p>
            <p><strong>차량 번호:</strong> {detail_data['plate']}</p>
            <p><strong>발생 장소:</strong> {detail_data['location']}</p>
            <p><strong>파일:</strong> <a href="{detail_data['video_url']}" download>다운로드</a></p>
            <br>
            <a href="/list">← 리스트로 돌아가기</a>
        </body>
        </html>
        """
        
    except Exception as e:
        print(f"상세 페이지 오류: {e}")
        return "데이터를 불러오는 중 오류가 발생했습니다.", 500

@list_bp.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    data = request.get_json()
    report_id = data.get('id')
    fav       = data.get('fav')

    # TODO: 실제 DB 업데이트 로직
    # 예시: save_favorite_status(report_id, fav)
    # db = get_db_connection()
    # db.execute("UPDATE reports SET is_favorite=%s WHERE id=%s", (fav, report_id))
    # db.commit()

    return {'success': True}