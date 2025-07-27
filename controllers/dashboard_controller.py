from flask import Blueprint, render_template, jsonify
import pymysql, calendar, datetime
from config import Config

# ← Blueprint 정의
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def get_db_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

# ← @dashboard_bp.route 로 라우팅
@dashboard_bp.route('/', methods=['GET'])
def dashboard():
    conn = get_db_connection()
    cur_month = datetime.date.today().month
    cur_year  = datetime.date.today().year
    today_day = datetime.date.today().day

    # 미리 [0,0,…]으로 초기화 (1일부터 이달 마지막일까지)
    days_in_month = calendar.monthrange(cur_year, cur_month)[1]
    daily = [0]*days_in_month
    try:
        with conn.cursor() as cur:
            # 1) 올해 신고 건수
            cur.execute("""
                SELECT COUNT(*) AS cnt
                  FROM public_reports
                 WHERE YEAR(incident_date) = YEAR(CURDATE())
            """)
            total_year = cur.fetchone()['cnt']

            # 2) 이번달 신고 건수
            cur.execute("""
                SELECT COUNT(*) AS cnt
                  FROM public_reports
                 WHERE DATE_FORMAT(incident_date, '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m')
            """)
            total_month = cur.fetchone()['cnt']

            cur.execute("""
                SELECT DAY(incident_date) AS d, COUNT(*) AS cnt
                FROM public_reports
                WHERE YEAR(incident_date)=YEAR(CURDATE())
                AND MONTH(incident_date)=MONTH(CURDATE())
                GROUP BY DAY(incident_date)
            """)
            for r in cur.fetchall():
                daily[r['d']-1] = r['cnt']

            

            # 3) 월별 신고 건수 (1월~12월)
            cur.execute("""
                SELECT MONTH(incident_date) AS mon, COUNT(*) AS cnt
                  FROM public_reports
                 WHERE YEAR(incident_date) = YEAR(CURDATE())
                 GROUP BY MONTH(incident_date)
                 ORDER BY MONTH(incident_date)
            """)
            rows = cur.fetchall()
            sparklineYear = [0] * 12
            for r in rows:
                sparklineYear[r['mon'] - 1] = r['cnt']

            # 4) 위반 유형 비율 (violation_result 테이블과 조인)
            cur.execute("""
                SELECT vr.violation_type, COUNT(*) AS cnt
                  FROM public_reports pr
                  JOIN violation_result vr
                    ON vr.video_name = pr.media_path
                 GROUP BY vr.violation_type
            """)
            rows = cur.fetchall()
            type_labels = [r['violation_type'] for r in rows]
            type_data   = [r['cnt']            for r in rows]
            # ── ➋ Top 신고 유형 ──
            # helmet_violation 컬럼에 '위반' 으로 표시된 걸 처벌 횟수라고 가정
            cur.execute("""
                SELECT
                  vr.violation_type,
                  COUNT(*)                        AS report_count,
                  SUM(vr.helmet_violation = '위반') AS punishment_count
                FROM public_reports pr
                JOIN violation_result vr
                  ON vr.video_name = pr.media_path
                GROUP BY vr.violation_type
                ORDER BY report_count DESC
                LIMIT 5
            """)
            top_rows = cur.fetchall()

    finally:
        conn.close()

    return render_template(
        'dashboard.html',
        total_year=total_year,
        total_month=total_month,
        sparklineYear=sparklineYear,
        sparklineMonth=daily,
        type_labels=type_labels,
        type_data=type_data,
        top_rows=top_rows 
    )

@dashboard_bp.route('/top_violation')   # ← 여기를 추가!
def top_violation():
    """
    '위반 사항별 신고 건수' 데이터를 JSON 으로 반환하는 예시.
    템플릿에서 fetch(url_for('dashboard.top_violation')) 로 
    호출하실 수 있습니다.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT vr.violation_type,
                       COUNT(*)      AS report_count,
                       SUM(pr.punishment_times) AS punishment_count
                  FROM public_reports pr
                  JOIN violation_result vr
                    ON vr.video_name = pr.media_path
                 GROUP BY vr.violation_type
                 ORDER BY report_count DESC
                 LIMIT 5
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    # JSON 형태로 반환
    return jsonify(rows)