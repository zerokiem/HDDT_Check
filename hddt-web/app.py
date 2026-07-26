#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py — HDDT Web Application
Flask + SQLite + Playwright headless
"""

import os
import sys
import json
import shutil
import threading
import traceback
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   flash, jsonify, send_file, abort, session)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Job, LoginLog
from template import build_template_bytes
import notify

# ────────────────────────────────────────────────────────────
# App factory
# ────────────────────────────────────────────────────────────
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure data dirs
    for d in [app.config['UPLOAD_DIR'], app.config['OUTPUT_DIR'],
              app.config['SCREENSHOT_BASE'], app.config['LOG_DIR']]:
        os.makedirs(d, exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(uid):
        return User.query.get(int(uid))

    with app.app_context():
        db.create_all()
        _seed_admin(app)

    # ── Job thread pool (simple semaphore) ───────────────────
    app._job_semaphore = threading.Semaphore(app.config['MAX_CONCURRENT_JOBS'])
    app._stop_events   = {}  # job_id → threading.Event

    register_routes(app)
    return app


def _seed_admin(app):
    """Tạo tài khoản admin mặc định nếu chưa có."""
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@hddt.local',
                     is_admin=True, is_active=True)
        admin.set_password('Admin@2025!')
        db.session.add(admin)
        db.session.commit()
        print('[init] Tài khoản admin mặc định đã được tạo: admin / Admin@2025!')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS)


# ────────────────────────────────────────────────────────────
# Background worker
# ────────────────────────────────────────────────────────────
def run_checker_job(app, job_id):
    """Chạy checker trong background thread."""
    with app.app_context():
        job = Job.query.get(job_id)
        if not job:
            return

        job.status     = 'running'
        job.started_at = datetime.utcnow()
        db.session.commit()

        log_lines = []
        log_path  = str(app.config['LOG_DIR'] / f'job_{job_id}.log')
        job.log_path = log_path
        db.session.commit()

        def log_cb(msg):
            log_lines.append(msg)
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(msg + '\n')
            except Exception:
                pass

        def progress_cb(processed, total, yes, no, captcha_err, error):
            try:
                j = Job.query.get(job_id)
                if j:
                    j.total       = total
                    j.processed   = processed
                    j.yes_count   = yes
                    j.no_count    = no
                    j.captcha_err = captcha_err
                    j.error_count = error
                    db.session.commit()
            except Exception:
                pass

        stop_event = app._stop_events.get(job_id)

        # Thư mục lưu — dùng đường dẫn người dùng tự nhập lúc upload (nếu có
        # và tạo được), ngược lại dùng mặc định DATA_DIR/outputs,
        # DATA_DIR/screenshots.
        out_dir = str(app.config['OUTPUT_DIR'])
        scr_dir = str(app.config['SCREENSHOT_BASE'] / f'job_{job_id}')
        if job.custom_save_dir:
            try:
                os.makedirs(job.custom_save_dir, exist_ok=True)
                out_dir = job.custom_save_dir
                scr_dir = os.path.join(job.custom_save_dir, 'anh_chup')
                log_cb(f'[*] Lưu kết quả tại thư mục tự chọn: {job.custom_save_dir}')
            except Exception as e:
                log_cb(f'[!] Không dùng được thư mục "{job.custom_save_dir}" ({e}) '
                       f'— chuyển về thư mục mặc định.')

        # Headless — mặc định ẩn. Chỉ cho phép hiện cửa sổ Chromium khi thật
        # sự có màn hình (Windows chạy trực tiếp) — Docker/Linux luôn ép ẩn.
        headless = True if sys.platform != 'win32' else bool(job.headless)
        if not headless:
            log_cb('[*] Chạy HIỆN cửa sổ Chromium (chế độ debug/quan sát trực tiếp).')

        try:
            from checker_web import InvoiceCheckerWeb

            checker = InvoiceCheckerWeb(
                input_path     = job.input_path,
                output_dir     = out_dir,
                screenshot_dir = scr_dir,
                chromium_path  = app.config.get('CHROMIUM_PATH'),
                max_captcha    = app.config['MAX_CAPTCHA_AUTO'],
                page_wait      = app.config['PAGE_WAIT'],
                headless       = headless,
                progress_cb    = progress_cb,
                log_cb         = log_cb,
                stop_event     = stop_event,
            )

            results, stats, out_path = checker.run()

            # Zip ảnh — đặt tên trùng với file Excel kết quả, thêm hậu tố
            # "_anh" (vd 260726_KQ_check_hoa_don_01.xlsx -> ..._01_anh.zip).
            excel_stem = Path(out_path).stem
            zip_path   = os.path.join(out_dir, f'{excel_stem}_anh.zip')
            checker.zip_screenshots(zip_path)

            # Save to DB
            job = Job.query.get(job_id)
            job.status          = 'done'
            job.completed_at    = datetime.utcnow()
            job.output_path     = out_path
            job.output_filename = os.path.basename(out_path)
            job.screenshot_dir  = scr_dir
            job.screenshot_zip  = zip_path if os.path.exists(zip_path) else None
            job.total           = len(results)
            job.yes_count       = stats['yes']
            job.no_count        = stats['no']
            job.captcha_err     = stats['captcha_err']
            job.error_count     = stats['error']
            job.results_json    = json.dumps(results, ensure_ascii=False)
            db.session.commit()
            notify.notify_job_done(app.config, job)

        except Exception as e:
            tb = traceback.format_exc()
            log_cb(f'[ERROR] {e}\n{tb}')
            try:
                job = Job.query.get(job_id)
                job.status    = 'error'
                job.error_msg = str(e)
                job.completed_at = datetime.utcnow()
                db.session.commit()
                notify.notify_job_done(app.config, job)
            except Exception:
                pass
        finally:
            app._job_semaphore.release()
            app._stop_events.pop(job_id, None)


# ────────────────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────────────────
def register_routes(app):

    # ── Auth ─────────────────────────────────────────────────
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            remember = bool(request.form.get('remember'))

            user = User.query.filter_by(username=username).first()
            ip   = request.remote_addr
            ua   = request.user_agent.string[:512]

            if user and user.check_password(password) and user.is_active:
                login_user(user, remember=remember)
                user.last_login = datetime.utcnow()
                log = LoginLog(user_id=user.id, username=username,
                               ip_address=ip, action='login', user_agent=ua)
                db.session.add(log)
                db.session.commit()
                notify.notify_login(app.config, user.username, ip)
                flash(f'Chào mừng, {user.username}!', 'success')
                return redirect(request.args.get('next') or url_for('dashboard'))
            else:
                log = LoginLog(
                    user_id    = user.id if user else None,
                    username   = username,
                    ip_address = ip,
                    action     = 'failed',
                    user_agent = ua
                )
                db.session.add(log)
                db.session.commit()
                flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'danger')

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        log = LoginLog(user_id=current_user.id, username=current_user.username,
                       ip_address=request.remote_addr, action='logout',
                       user_agent=request.user_agent.string[:512])
        db.session.add(log)
        db.session.commit()
        logout_user()
        flash('Đã đăng xuất.', 'info')
        return redirect(url_for('login'))

    @app.route('/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        if request.method == 'POST':
            old_pw  = request.form.get('old_password', '')
            new_pw  = request.form.get('new_password', '')
            conf_pw = request.form.get('confirm_password', '')

            if not current_user.check_password(old_pw):
                flash('Mật khẩu cũ không đúng.', 'danger')
            elif len(new_pw) < 8:
                flash('Mật khẩu mới phải có ít nhất 8 ký tự.', 'danger')
            elif new_pw != conf_pw:
                flash('Mật khẩu xác nhận không khớp.', 'danger')
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash('Đổi mật khẩu thành công!', 'success')
                return redirect(url_for('dashboard'))
        return render_template('change_password.html')

    # ── Dashboard ─────────────────────────────────────────────
    @app.route('/')
    @login_required
    def dashboard():
        recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(10).all()
        total_jobs  = Job.query.count()
        total_yes   = db.session.query(db.func.sum(Job.yes_count)).scalar() or 0
        total_no    = db.session.query(db.func.sum(Job.no_count)).scalar() or 0
        running     = Job.query.filter_by(status='running').count()
        return render_template('dashboard.html',
                               recent_jobs=recent_jobs,
                               total_jobs=total_jobs,
                               total_yes=total_yes,
                               total_no=total_no,
                               running=running)

    # ── Upload & Run ─────────────────────────────────────────
    @app.route('/upload', methods=['GET', 'POST'])
    @login_required
    def upload():
        if request.method == 'POST':
            if 'excel_file' not in request.files:
                flash('Chưa chọn file.', 'danger')
                return redirect(request.url)

            f = request.files['excel_file']
            if f.filename == '':
                flash('Chưa chọn file.', 'danger')
                return redirect(request.url)

            if not allowed_file(f.filename):
                flash('Chỉ chấp nhận file .xlsx hoặc .xls', 'danger')
                return redirect(request.url)

            # Check concurrent limit
            running_count = Job.query.filter_by(status='running').count()
            if running_count >= app.config['MAX_CONCURRENT_JOBS']:
                flash(f'Đang có {running_count} job chạy. Vui lòng đợi.', 'warning')
                return redirect(url_for('history'))

            filename    = secure_filename(f.filename)
            ts          = datetime.now().strftime('%Y%m%d_%H%M%S')
            saved_name  = f'{ts}_{filename}'
            saved_path  = str(app.config['UPLOAD_DIR'] / saved_name)
            f.save(saved_path)

            save_dir     = request.form.get('save_dir', '').strip() or None
            show_browser = bool(request.form.get('show_browser'))

            job = Job(
                user_id         = current_user.id,
                input_filename  = filename,
                input_path      = saved_path,
                status          = 'pending',
                custom_save_dir = save_dir,
                headless        = not show_browser,
            )
            db.session.add(job)
            db.session.commit()

            stop_ev = threading.Event()
            app._stop_events[job.id] = stop_ev

            app._job_semaphore.acquire()
            t = threading.Thread(
                target=run_checker_job,
                args=(app, job.id),
                daemon=True
            )
            t.start()

            flash(f'Đã tạo job #{job.id}. Đang xử lý...', 'success')
            return redirect(url_for('job_detail', job_id=job.id))

        return render_template('upload.html', default_save_dir=str(app.config['OUTPUT_DIR']))

    @app.route('/template/download')
    @login_required
    def download_template():
        buf = build_template_bytes()
        return send_file(
            buf,
            as_attachment=True,
            download_name='Mau_input_check_hoa_don.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    # ── Job detail ───────────────────────────────────────────
    @app.route('/job/<int:job_id>')
    @login_required
    def job_detail(job_id):
        job = Job.query.get_or_404(job_id)
        if not current_user.is_admin and job.user_id != current_user.id:
            abort(403)
        results = json.loads(job.results_json) if job.results_json else []
        return render_template('job_detail.html', job=job, results=results)

    @app.route('/api/job/<int:job_id>/status')
    @login_required
    def job_status_api(job_id):
        job = Job.query.get_or_404(job_id)
        if not current_user.is_admin and job.user_id != current_user.id:
            abort(403)
        return jsonify({
            'status':      job.status,
            'total':       job.total,
            'processed':   job.processed,
            'yes':         job.yes_count,
            'no':          job.no_count,
            'captcha_err': job.captcha_err,
            'error':       job.error_count,
            'pct':         job.progress_pct(),
            'duration':    job.duration_str(),
            'error_msg':   job.error_msg or '',
        })

    @app.route('/api/job/<int:job_id>/log')
    @login_required
    def job_log_api(job_id):
        job = Job.query.get_or_404(job_id)
        if not current_user.is_admin and job.user_id != current_user.id:
            abort(403)
        lines = []
        if job.log_path and os.path.exists(job.log_path):
            with open(job.log_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()[-200:]  # last 200 lines
        return jsonify({'lines': lines})

    @app.route('/job/<int:job_id>/stop', methods=['POST'])
    @login_required
    def job_stop(job_id):
        job = Job.query.get_or_404(job_id)
        if not current_user.is_admin and job.user_id != current_user.id:
            abort(403)
        ev = app._stop_events.get(job_id)
        if ev:
            ev.set()
        job.status = 'cancelled'
        db.session.commit()
        flash(f'Đã gửi lệnh dừng job #{job_id}.', 'warning')
        return redirect(url_for('job_detail', job_id=job_id))

    # ── Downloads ─────────────────────────────────────────────
    @app.route('/job/<int:job_id>/download/excel')
    @login_required
    def download_excel(job_id):
        job = Job.query.get_or_404(job_id)
        if not current_user.is_admin and job.user_id != current_user.id:
            abort(403)
        if not job.output_path or not os.path.exists(job.output_path):
            flash('File Excel chưa có.', 'warning')
            return redirect(url_for('job_detail', job_id=job_id))
        return send_file(job.output_path,
                         as_attachment=True,
                         download_name=job.output_filename or f'job_{job_id}.xlsx')

    @app.route('/job/<int:job_id>/download/screenshots')
    @login_required
    def download_screenshots(job_id):
        job = Job.query.get_or_404(job_id)
        if not current_user.is_admin and job.user_id != current_user.id:
            abort(403)
        if not job.screenshot_zip or not os.path.exists(job.screenshot_zip):
            flash('File ảnh chưa có hoặc không có ảnh nào.', 'warning')
            return redirect(url_for('job_detail', job_id=job_id))
        return send_file(job.screenshot_zip,
                         as_attachment=True,
                         download_name=os.path.basename(job.screenshot_zip))

    @app.route('/job/<int:job_id>/download/log')
    @login_required
    def download_log(job_id):
        job = Job.query.get_or_404(job_id)
        if not current_user.is_admin and job.user_id != current_user.id:
            abort(403)
        if not job.log_path or not os.path.exists(job.log_path):
            flash('File log chưa có.', 'warning')
            return redirect(url_for('job_detail', job_id=job_id))
        return send_file(job.log_path,
                         as_attachment=True,
                         download_name=f'job_{job_id}.log')

    # ── History ──────────────────────────────────────────────
    @app.route('/history')
    @login_required
    def history():
        page = request.args.get('page', 1, type=int)
        q    = Job.query
        if not current_user.is_admin:
            q = q.filter_by(user_id=current_user.id)
        jobs = q.order_by(Job.created_at.desc()).paginate(page=page, per_page=20)
        return render_template('history.html', jobs=jobs)

    # ── Admin ─────────────────────────────────────────────────
    @app.route('/admin/users')
    @login_required
    @admin_required
    def admin_users():
        users = User.query.order_by(User.created_at.desc()).all()
        return render_template('admin/users.html', users=users)

    @app.route('/admin/users/add', methods=['POST'])
    @login_required
    @admin_required
    def admin_add_user():
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip() or None
        password = request.form.get('password', '')
        is_admin = bool(request.form.get('is_admin'))

        if not username or len(password) < 8:
            flash('Username không rỗng và password ≥ 8 ký tự.', 'danger')
            return redirect(url_for('admin_users'))

        if User.query.filter_by(username=username).first():
            flash(f'Username "{username}" đã tồn tại.', 'danger')
            return redirect(url_for('admin_users'))

        u = User(username=username, email=email, is_admin=is_admin, is_active=True)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash(f'Đã tạo user "{username}".', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:uid>/toggle', methods=['POST'])
    @login_required
    @admin_required
    def admin_toggle_user(uid):
        u = User.query.get_or_404(uid)
        if u.id == current_user.id:
            flash('Không thể vô hiệu hóa tài khoản đang dùng.', 'warning')
        else:
            u.is_active = not u.is_active
            db.session.commit()
            state = 'kích hoạt' if u.is_active else 'vô hiệu hóa'
            flash(f'Đã {state} user "{u.username}".', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:uid>/reset-password', methods=['POST'])
    @login_required
    @admin_required
    def admin_reset_password(uid):
        u       = User.query.get_or_404(uid)
        new_pw  = request.form.get('new_password', '')
        if len(new_pw) < 8:
            flash('Mật khẩu mới phải ≥ 8 ký tự.', 'danger')
        else:
            u.set_password(new_pw)
            db.session.commit()
            flash(f'Đã đặt lại mật khẩu cho "{u.username}".', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:uid>/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_user(uid):
        u = User.query.get_or_404(uid)
        if u.id == current_user.id:
            flash('Không thể xóa tài khoản đang dùng.', 'warning')
        else:
            db.session.delete(u)
            db.session.commit()
            flash(f'Đã xóa user "{u.username}".', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/logs')
    @login_required
    @admin_required
    def admin_logs():
        page = request.args.get('page', 1, type=int)
        logs = LoginLog.query.order_by(
            LoginLog.timestamp.desc()).paginate(page=page, per_page=50)
        return render_template('admin/logs.html', logs=logs)

    @app.route('/admin/jobs')
    @login_required
    @admin_required
    def admin_jobs():
        page = request.args.get('page', 1, type=int)
        jobs = Job.query.order_by(Job.created_at.desc()).paginate(page=page, per_page=20)
        return render_template('history.html', jobs=jobs, admin_view=True)

    # ── Error handlers ────────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('error.html', code=403,
                               msg='Bạn không có quyền truy cập trang này.'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html', code=404,
                               msg='Không tìm thấy trang yêu cầu.'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', code=500,
                               msg='Lỗi máy chủ nội bộ.'), 500

    # ── Context processors ────────────────────────────────────
    @app.context_processor
    def inject_globals():
        return dict(app_name='HDDT Checker', now=datetime.utcnow(),
                    copyright_owner=app.config.get('COPYRIGHT_OWNER'),
                    is_windows=(sys.platform == 'win32'))


# ────────────────────────────────────────────────────────────
# Entry point
# ────────────────────────────────────────────────────────────
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config['PORT'], threaded=True, debug=False)
