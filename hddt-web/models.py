from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80), unique=True, nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin     = db.Column(db.Boolean, default=False)
    is_active    = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    last_login   = db.Column(db.DateTime, nullable=True)

    jobs = db.relationship('Job', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def active(self):
        return self.is_active

    def __repr__(self):
        return f'<User {self.username}>'


class Job(db.Model):
    __tablename__ = 'jobs'

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    input_filename  = db.Column(db.String(255), nullable=False)
    input_path      = db.Column(db.String(512), nullable=True)
    output_filename = db.Column(db.String(255), nullable=True)
    output_path     = db.Column(db.String(512), nullable=True)
    screenshot_dir  = db.Column(db.String(512), nullable=True)
    screenshot_zip  = db.Column(db.String(512), nullable=True)
    status          = db.Column(db.String(20), default='pending')
    # pending | running | done | error | cancelled
    total           = db.Column(db.Integer, default=0)
    processed       = db.Column(db.Integer, default=0)
    yes_count       = db.Column(db.Integer, default=0)
    no_count        = db.Column(db.Integer, default=0)
    captcha_err     = db.Column(db.Integer, default=0)
    error_count     = db.Column(db.Integer, default=0)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    started_at      = db.Column(db.DateTime, nullable=True)
    completed_at    = db.Column(db.DateTime, nullable=True)
    log_path        = db.Column(db.String(512), nullable=True)
    # Results stored as JSON string
    results_json    = db.Column(db.Text, nullable=True)
    error_msg       = db.Column(db.Text, nullable=True)
    # Thư mục lưu Excel+ảnh do người dùng tự nhập lúc upload — trống = dùng
    # mặc định (DATA_DIR/outputs, DATA_DIR/screenshots).
    custom_save_dir = db.Column(db.String(512), nullable=True)
    # True = chạy Chromium ẩn (headless). False = hiện cửa sổ trình duyệt —
    # chỉ có tác dụng khi chạy trực tiếp trên Windows có màn hình (bị ép về
    # True khi chạy trong Docker/Linux không có display).
    headless        = db.Column(db.Boolean, default=True)

    def duration_str(self):
        if not self.started_at:
            return '—'
        end = self.completed_at or datetime.utcnow()
        secs = int((end - self.started_at).total_seconds())
        m, s = divmod(secs, 60)
        return f'{m}m {s}s'

    def progress_pct(self):
        if not self.total:
            return 0
        return int(self.processed / self.total * 100)

    def __repr__(self):
        return f'<Job {self.id} {self.status}>'


class LoginLog(db.Model):
    __tablename__ = 'login_logs'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username   = db.Column(db.String(80), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    action     = db.Column(db.String(20), nullable=False)  # login|logout|failed
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.String(512), nullable=True)

    user = db.relationship('User', backref='login_logs', foreign_keys=[user_id])

    def __repr__(self):
        return f'<LoginLog {self.username} {self.action} {self.timestamp}>'


class Setting(db.Model):
    """Cấu hình chỉnh được từ web (chỉ admin) — có hiệu lực ngay, không cần
    sửa file .env / restart. Trống (không có row) = dùng giá trị mặc định từ
    .env (xem app.get_setting)."""
    __tablename__ = 'settings'

    key   = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.Text, nullable=True)
