import os
import pymysql
from flask import (Blueprint, render_template,
request, jsonify, abort, current_app)
from config import Config

list_bp = Blueprint('list', __name__, url_prefix='/list')

def get_db_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT,                    # 포트도 Config 에 정의하셨으니 DB_PORT 로
        cursorclass=pymysql.cursors.DictCursor
    )

@list_bp.route('/')
def list_view():
    # 정렬 파라미터
    sort_by = request.args.get('sort_by', 'report_id')
    order   = request.args.get('order',   'asc').upper()
    if order not in ('ASC', 'DESC'):
        order = 'ASC'

    # 허용된 컬럼만
    allowed_cols = {'report_id','incident_date','violation_type','reporter_name'}
    if sort_by not in allowed_cols:
        sort_by = 'report_id'

    # 데이터 조회
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            sql = f"""
                SELECT
                    pr.report_id,
                    vr.violation_type,
                    pr.incident_date,
                    pr.vehicle_number,
                    pr.location,
                    pr.media_path,
                    pr.reporter_name,
                    pr.is_starred  /* 즐겨찾기 여부 */
                FROM public_reports AS pr
                LEFT JOIN violation_result AS vr
                    ON vr.video_name = pr.media_path
                ORDER BY {sort_by} {order}
                LIMIT 100
            """
            cur.execute(sql)
            reports = cur.fetchall()
    finally:
        conn.close()

    return render_template(
        'list.html',
        reports=reports,
        sort_by=sort_by,
        order=order.lower()
    )


@list_bp.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    data = request.get_json() or {}
    report_id = data.get('id')
    fav       = data.get('fav', False)

    # 실제 DB 업데이트
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
              "UPDATE public_reports SET is_starred=%s WHERE report_id=%s",
              (1 if fav else 0, report_id)
            )
        conn.commit()
        return jsonify(success=True)
    except Exception as e:
        conn.rollback()
        return jsonify(success=False, message=str(e)), 500
    finally:
        conn.close()

@list_bp.route('/update', methods=['POST'])
def update_report():
    data = request.get_json() or {}
    row_id = data.get('row_id')
    if not row_id:
        return jsonify(status='error', message='row_id 누락'), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # (A) violation_type → violation_result 테이블 업데이트
            if '2' in data:
                cur.execute(
                    "UPDATE violation_result vr "
                    "JOIN public_reports pr ON vr.video_name=pr.media_path "
                    "SET vr.violation_type=%s "
                    "WHERE pr.report_id=%s",
                    (data['2'], row_id)
                )
            # (B) incident_date, vehicle_number, location → public_reports 업데이트
            col_map = {'3':'incident_date','4':'vehicle_number','5':'location'}
            updates, params = [], []
            for key, col in col_map.items():
                if key in data:
                    updates.append(f"`{col}`=%s")
                    params.append(data[key])
            if updates:
                params.append(row_id)
                sql = "UPDATE public_reports SET " + ", ".join(updates) + " WHERE report_id=%s"
                cur.execute(sql, params)

        conn.commit()
        return jsonify(status='ok')
    except Exception as e:
        conn.rollback()
        return jsonify(status='error', message=str(e)), 500
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
            cur.execute("DELETE FROM public_reports WHERE report_id=%s", (row_id,))
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
        return jsonify(success=False, message="선택된 아이디가 없습니다."), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            placeholder = ",".join(["%s"] * len(ids))
            sql = f"DELETE FROM public_reports WHERE report_id IN ({placeholder})"
            cur.execute(sql, ids)
        conn.commit()
        return jsonify(success=True)
    except Exception as e:
        conn.rollback()
        return jsonify(success=False, message=str(e)), 500
    finally:
        conn.close()

@list_bp.route('/analytics/<int:report_id>')
def analytics(report_id):
    # --- 1) DB에서 report 한 건 조회 ---
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT pr.*, vr.violation_type
            FROM public_reports pr
            LEFT JOIN violation_result vr
              ON pr.media_path = vr.video_name
            WHERE pr.report_id = %s
        """, (report_id,))
        report = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if not report:
        abort(404, f"Report {report_id} not found")

    static_root = current_app.static_folder

    # ③ uploads 폴더 스캔 → 모든 미디어 목록 + 첫 비디오 선택
    upload_dir = os.path.join(static_root, 'uploads', str(report_id))
    upload_files = []
    video_path   = None
    if os.path.isdir(upload_dir):
        for fname in sorted(os.listdir(upload_dir)):
            ext = fname.rsplit('.', 1)[-1].lower()
            if ext in ('mp4','webm','ogg','png','jpg','jpeg','gif'):
                rel = f"uploads/{report_id}/{fname}"
                upload_files.append(rel)
                if video_path is None and ext in ('mp4','webm','ogg'):
                    video_path = rel

    # ④ imgshots 폴더 스캔 → 스냅샷 목록
    shot_dir = os.path.join(static_root, 'imgshots', str(report_id))
    shot_files = []
    if os.path.isdir(shot_dir):
        for fname in sorted(os.listdir(shot_dir)):
            ext = fname.rsplit('.', 1)[-1].lower()
            if ext in ('png','jpg','jpeg','gif'):
                shot_files.append(f"imgshots/{report_id}/{fname}")

    # ⑤ 썸네일용 리스트 결정: imgshots 있으면 shot_files, 없으면 upload_files
    files = shot_files if shot_files else upload_files

    return render_template(
        'analytics.html',
        report=report,
        files=files,
        video_path=video_path
    )