import os
import pymysql
from flask import (
    Blueprint, render_template, abort, current_app,
    request, jsonify
)
from config import Config

# Analytics 전용 블루프린트
analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

def get_db_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

@analytics_bp.route('/<int:report_id>')
def view(report_id):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT pr.*, vr.violation_type
              FROM public_reports pr
         LEFT JOIN violation_result vr
                ON pr.media_path = vr.video_name
             WHERE pr.report_id = %s
            """, (report_id,)
        )
        report = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if not report:
        abort(404, f"Report {report_id} not found")

    static_root = current_app.static_folder

    # uploads 폴더에서 파일 스캔
    upload_dir = os.path.join(static_root, 'uploads', str(report_id))
    upload_files, video_path = [], None
    if os.path.isdir(upload_dir):
        for f in sorted(os.listdir(upload_dir)):
            ext = f.rsplit('.', 1)[-1].lower()
            if ext in ('mp4', 'webm', 'ogg', 'png', 'jpg', 'jpeg', 'gif'):
                rel = f"uploads/{report_id}/{f}"
                upload_files.append(rel)
                if video_path is None and ext in ('mp4', 'webm', 'ogg'):
                    video_path = rel

    # imgshots 폴더에서 스냅샷 스캔
    shot_dir = os.path.join(static_root, 'imgshots', str(report_id))
    shot_files = []
    if os.path.isdir(shot_dir):
        for f in sorted(os.listdir(shot_dir)):
            ext = f.rsplit('.', 1)[-1].lower()
            if ext in ('png', 'jpg', 'jpeg', 'gif'):
                shot_files.append(f"imgshots/{report_id}/{f}")

    files = shot_files if shot_files else upload_files
    return render_template(
        'analytics.html', report=report,
        video_path=video_path, files=files
    )

@analytics_bp.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    data = request.get_json() or {}
    report_id = data.get('id')
    fav = data.get('fav', False)
    if report_id is None:
        return jsonify(success=False, message='id 누락'), 400

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

@analytics_bp.route('/update', methods=['POST'])
def update_report():
    data = request.get_json() or {}
    row_id = data.get('row_id')
    if not row_id:
        return jsonify(status='error', message='row_id 누락'), 400

    violation_type = data.get('violation_type')
    incident_date  = data.get('incident_date')
    vehicle_number = data.get('vehicle_number')
    location       = data.get('location')

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. public_reports 업데이트
            col_map = {
                'incident_date':  'incident_date',
                'vehicle_number': 'vehicle_number',
                'location':       'location',
            }
            updates, params = [], []
            for key, col in col_map.items():
                val = data.get(key)
                if val is not None:
                    updates.append(f"`{col}`=%s")
                    params.append(val)
            if updates:
                params.append(row_id)
                sql = "UPDATE public_reports SET " + ", ".join(updates) + " WHERE report_id=%s"
                cur.execute(sql, params)

            # 2. violation_result(violation_type) UPDATE or INSERT
            if violation_type is not None:
                cur.execute("SELECT media_path FROM public_reports WHERE report_id=%s", (row_id,))
                row = cur.fetchone()
                video_name = row['media_path'] if row else None
                if video_name:
                    cur.execute("SELECT * FROM violation_result WHERE video_name=%s", (video_name,))
                    if cur.fetchone():
                        # 이미 있으면 UPDATE
                        cur.execute(
                            "UPDATE violation_result SET violation_type=%s WHERE video_name=%s",
                            (violation_type, video_name)
                        )
                    else:
                        # 없으면 INSERT
                        cur.execute(
                            "INSERT INTO violation_result (video_name, violation_type) VALUES (%s, %s)",
                            (video_name, violation_type)
                        )
        conn.commit()
        return jsonify(status='ok')
    except Exception as e:
        conn.rollback()
        return jsonify(status='error', message=str(e)), 500
    finally:
        conn.close()

@analytics_bp.route('/delete', methods=['POST'])
def delete_report():
    data = request.get_json() or {}
    row_id = data.get('row_id')
    if not row_id:
        return jsonify(status='error', message='row_id 누락'), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM public_reports WHERE report_id=%s",
                (row_id,)
            )
        conn.commit()
        return jsonify(status='ok')
    except Exception as e:
        conn.rollback()
        return jsonify(status='error', message=str(e)), 500
    finally:
        conn.close()