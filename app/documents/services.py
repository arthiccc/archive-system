import os
import subprocess
from PyPDF2 import PdfReader
from docx import Document as DocxDocument


def extract_text_content(file_path, mime_type):
    text = ""

    try:
        if mime_type == "application/pdf":
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        elif mime_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]:
            doc = DocxDocument(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"

        elif mime_type == "text/plain":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        elif mime_type == "application/msword":
            try:
                result = subprocess.run(
                    ["antiword", file_path], capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    text = result.stdout
            except FileNotFoundError:
                pass

    except Exception as e:
        pass

    return text.strip()[:100000]


def get_file_preview(file_path, mime_type):
    preview = {"type": "unknown", "content": None}

    try:
        if mime_type == "application/pdf":
            preview["type"] = "pdf"
        elif mime_type.startswith("image/"):
            preview["type"] = "image"
        elif mime_type in ["text/plain", "text/csv", "text/html", "application/json"]:
            preview["type"] = "text"
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    preview["content"] = f.read(5000)
            except:
                pass
        elif mime_type.startswith("application/vnd.openxmlformats"):
            preview["type"] = "office"
    except Exception:
        pass

    return preview


def log_audit_action(action, document_id=None, details=None, user_id=None):
    from flask import current_app, request
    from app.extensions import db
    from app.models import AuditLog
    from flask_login import current_user

    if not current_app.config.get("AUDIT_LOG_ENABLED", True):
        return

    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id

    log = AuditLog(
        admin_user_id=user_id,
        action=action,
        document_id=document_id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        details=str(details) if details else None,
    )

    db.session.add(log)
    db.session.commit()
