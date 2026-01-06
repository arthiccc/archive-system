from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))


class AdminUser(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<AdminUser {self.username}>"


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    parent = db.relationship("Category", remote_side=[id], backref="children")

    def full_path(self):
        if self.parent:
            return f"{self.parent.full_path()} / {self.name}"
        return self.name

    def __repr__(self):
        return f"<Category {self.name}>"


class AcademicPeriod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year_start = db.Column(db.Integer, nullable=False)
    year_end = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def name(self):
        return f"{self.year_start}-{self.year_end} {self.semester}"

    @property
    def folder_name(self):
        return f"{self.year_start}-{self.year_end}/{self.semester}"

    def __repr__(self):
        return f"<AcademicPeriod {self.name}>"


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger)
    mime_type = db.Column(db.String(100))
    content_text = db.Column(db.Text)
    description = db.Column(db.Text)
    metadata_json = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    academic_period_id = db.Column(db.Integer, db.ForeignKey("academic_period.id"))
    uploaded_by = db.Column(db.Integer, db.ForeignKey("admin_user.id"))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)

    category = db.relationship("Category", backref="documents")
    academic_period = db.relationship("AcademicPeriod", backref="documents")
    uploader = db.relationship("AdminUser", backref="documents")

    def __repr__(self):
        return f"<Document {self.title}>"


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7), default="#6c757d")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    documents = db.relationship("Document", secondary="document_tag", backref="tags")

    def __repr__(self):
        return f"<Tag {self.name}>"


document_tag = db.Table(
    "document_tag",
    db.Column(
        "document_id", db.Integer, db.ForeignKey("document.id"), primary_key=True
    ),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey("admin_user.id"))
    action = db.Column(db.String(50), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("document.id"))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("AdminUser", backref="audit_logs")
    document = db.relationship("Document", backref="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_id}>"
