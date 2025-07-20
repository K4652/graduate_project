import os
from flask import (
    Blueprint, current_app, render_template,
    request, redirect, url_for, flash
)
from werkzeug.utils import secure_filename

upload_bp = Blueprint('upload', __name__)

def allowed_file(fn):
    return (
      '.' in fn and
      fn.rsplit('.',1)[1].lower() in
      current_app.config['ALLOWED_EXTENSIONS']
    )

@upload_bp.route('/upload', methods=['GET','POST'])
def upload():
    UP = current_app.config['UPLOAD_FOLDER']
    os.makedirs(UP, exist_ok=True)

    if request.method == 'POST':
        for f in request.files.getlist('files'):
            if f and allowed_file(f.filename):
                fname = secure_filename(f.filename)
                f.save(os.path.join(UP, fname))
            else:
                flash(f"{f.filename} 은(는) 허용되지 않는 형식입니다.", 'warning')
        return redirect(url_for('upload.upload'))

    files = sorted(os.listdir(UP))
    return render_template('upload.html', files=files)