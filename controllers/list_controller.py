import json
import pymysql
from flask import Blueprint, render_template, request, jsonify
from config import Config

list_bp = Blueprint('list', __name__, url_prefix='/list')

def get_db_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT,                    # ← 여기 DB_PORT 로 변경
        cursorclass=pymysql.cursors.DictCursor
    )

@list_bp.route('/')
def list_view():
    # 1) 쿼리스트링으로 정렬 컬럼/방향 받아오기
    sort_by = request.args.get('sort_by', 'report_id')
    order   = request.args.get('order',   'asc').upper()
    if order not in ('ASC', 'DESC'):
        order = 'ASC'

    # 2) 허용된 컬럼만 정렬에 사용 (SQL 인젝션 방지)
    allowed_cols = {'report_id','incident_date','violation_type','reporter_name'}
    if sort_by not in allowed_cols:
        sort_by = 'report_id'

    # 3) DB에서 실제 데이터 조회 (public_reports + violation_result JOIN)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            sql = f"""
                SELECT
                  pr.report_id,
                  vr.violation_type,        -- violation_result.violation_type
                  pr.incident_date,
                  pr.vehicle_number,
                  pr.location,
                  pr.media_path,
                  pr.reporter_name
                FROM public_reports AS pr
                LEFT JOIN violation_result AS vr
                  ON vr.video_name = pr.media_path
                ORDER BY {sort_by} {order}
                LIMIT 100
            """
            cur.execute(sql)
            reports = cur.fetchall()  # List[Dict]
    finally:
        conn.close()

    # 4) 템플릿에 데이터 전달
    return render_template(
        'list.html',
        reports=reports,
        sort_by=sort_by,
        order=order.lower()
    )

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


@list_bp.route('/update', methods=['POST'])
def update_report():
    data   = request.get_json()
    row_id = data.get('row_id')
    # 수정 가능한 칼럼 인덱스 → 실제 public_reports 컬럼 이름 매핑
    col_map = {
      2: 'violation_type',
      3: 'incident_date',
      4: 'vehicle_number',
      5: 'location',
    }

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 전송된 데이터 중에서, 수정하려는 칼럼만 골라서 UPDATE
            for idx, col in col_map.items():
                # 데이터 키가 숫자가 아닌 문자열일 수도 있으니 두 형태 확인
                if str(idx) in data or idx in data:
                    # JSON payload 의 키가 문자열로 넘어오므로 str(idx) 로 꺼냅니다
                    new_val = data.get(str(idx), data.get(idx))
                    sql = f"UPDATE public_reports SET `{col}` = %s WHERE report_id = %s"
                    cur.execute(sql, (new_val, row_id))
        conn.commit()
        return jsonify(status="ok")
    except Exception as e:
        conn.rollback()
        return jsonify(status="error", message=str(e)), 500
    finally:
        conn.close()

@list_bp.route('/delete', methods=['POST'])
def delete_report():
    data   = request.get_json() or {}
    row_id = data.get('row_id')
    if not row_id:
        return jsonify(status='error', message='row_id 누락'), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # public_reports 에서 삭제
            cur.execute("DELETE FROM public_reports WHERE report_id = %s", (row_id,))
            # (선택) violation_result / violation_frame 도 연관 삭제 필요 시 여기에 추가
        conn.commit()
        return jsonify(status='ok')
    except Exception as e:
        conn.rollback()
        return jsonify(status='error', message=str(e)), 500
    finally:
        conn.close()

@list_bp.route('/delete_selected', methods=['POST'])
def delete_selected():
    data = request.get_json() or {}
    ids  = data.get('ids', [])
    if not ids:
        return jsonify(success=False, message="선택된 아이디가 없습니다.")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 예시: public_reports 테이블에서 삭제
            format_ids = ','.join(['%s']*len(ids))
            sql = f"DELETE FROM public_reports WHERE report_id IN ({format_ids})"
            cur.execute(sql, ids)
            conn.commit()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))
    finally:
        conn.close()