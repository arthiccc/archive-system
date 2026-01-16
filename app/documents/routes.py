import os
import uuid
import json
import magic
from datetime import datetime
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    send_file,
    abort,
    current_app,
)
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models import Document, Category, AcademicPeriod, Tag, AuditLog, Correspondent
from app.documents.forms import DocumentUploadForm, DocumentEditForm
from app.documents.services import (
    extract_text_content,
    get_file_preview,
    log_audit_action,
    run_auto_matching,
)
from app.search.services import index_document, delete_document_from_index
from . import documents


@documents.route("/")
@login_required
def list():
    page = request.args.get("page", 1, type=int)
    per_page = 20

    category_filter = request.args.get("category", type=int)
    period_filter = request.args.get("period", type=int)
    tag_filter = request.args.get("tag", type=int)
    search_query = request.args.get("q", "")

    query = Document.query.filter_by(is_deleted=False)

    if category_filter:
        query = query.filter_by(category_id=category_filter)
    if period_filter:
        query = query.filter_by(academic_period_id=period_filter)
    if tag_filter:
        query = query.filter(Document.tags.any(id=tag_filter))
    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
            or_(
                Document.title.ilike(search),
                Document.original_filename.ilike(search),
                Document.description.ilike(search),
            )
        )

    pagination = query.order_by(Document.uploaded_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    categories = (
        Category.query.filter_by(is_active=True)
        .order_by(Category.sort_order, Category.name)
        .all()
    )
    periods = (
        AcademicPeriod.query.filter_by(is_active=True)
        .order_by(AcademicPeriod.year_start.desc(), AcademicPeriod.semester)
        .all()
    )
    tags = Tag.query.order_by(Tag.name).all()

    return render_template(
        "documents/list.html",
        documents=pagination.items,
        pagination=pagination,
        categories=categories,
        periods=periods,
        tags=tags,
    )


@documents.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    form = DocumentUploadForm()

    categories = (
        Category.query.filter_by(is_active=True)
        .order_by(Category.sort_order, Category.name)
        .all()
    )
    periods = (
        AcademicPeriod.query.filter_by(is_active=True)
        .order_by(AcademicPeriod.year_start.desc(), AcademicPeriod.semester)
        .all()
    )
    correspondents = Correspondent.query.order_by(Correspondent.name).all()

    form.category.choices = [(c.id, c.name) for c in categories]
    form.academic_period.choices = [
        (p.id, f"{p.year_start}-{p.year_end} {p.semester}") for p in periods
    ]
    form.correspondent.choices = [(0, "None")] + [
        (c.id, c.name) for c in correspondents
    ]

    current_period = (
        AcademicPeriod.query.filter_by(is_active=True)
        .order_by(AcademicPeriod.year_start.desc(), AcademicPeriod.semester)
        .first()
    )

    if form.validate_on_submit():
        file = form.file.data
        if file:
            original_filename = file.filename
            stored_filename = f"{uuid.uuid4()}{os.path.splitext(original_filename)[1]}"
            mime_type = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0)
            file_size = len(file.read())
            file.seek(0)

            title = os.path.splitext(original_filename)[0]
            category = Category.query.get(form.category.data)
            period = AcademicPeriod.query.get(form.academic_period.data)

            folder_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], period.folder_name, category.slug
            )
            os.makedirs(folder_path, exist_ok=True)

            file_path = os.path.join(folder_path, stored_filename)
            file.save(file_path)

            content_text = extract_text_content(file_path, mime_type)

            tags = []
            if form.tags.data:
                for tag_name in form.tags.data.split(","):
                    tag_name = tag_name.strip()
                    if tag_name:
                        tag = Tag.query.filter_by(name=tag_name).first()
                        if not tag:
                            tag = Tag(name=tag_name)
                            db.session.add(tag)
                        tags.append(tag)

            metadata = {
                "original_filename": original_filename,
                "mime_type": mime_type,
            }

            doc = Document(
                title=title,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
                content_text=content_text,
                category_id=category.id,
                academic_period_id=period.id,
                correspondent_id=form.correspondent.data
                if form.correspondent.data > 0
                else None,
                uploaded_by=current_user.id,
                metadata_json=json.dumps(metadata),
            )

            for tag in tags:
                doc.tags.append(tag)

            # Auto-matching
            run_auto_matching(doc)

            db.session.add(doc)
            db.session.commit()

            # Index in Meilisearch
            index_document(doc)

            log_audit_action("upload", doc.id, {"filename": original_filename})

            flash(f'Document "{doc.title}" uploaded successfully!', "success")
            return redirect(url_for("documents.list"))

    if current_period:
        form.academic_period.data = current_period.id

    return render_template(
        "documents/upload.html", form=form, categories=categories, periods=periods
    )


@documents.route("/<int:doc_id>")
@login_required
def detail(doc_id):
    doc = Document.query.filter_by(id=doc_id, is_deleted=False).first_or_404()

    log_audit_action("view", doc.id)

    preview = get_file_preview(doc.file_path, doc.mime_type)

    return render_template("documents/detail.html", document=doc, preview=preview)


@documents.route("/<int:doc_id>/download")
@login_required
def download(doc_id):
    doc = Document.query.filter_by(id=doc_id, is_deleted=False).first_or_404()

    log_audit_action("download", doc.id)

    return send_file(
        doc.file_path, download_name=doc.original_filename, as_attachment=True
    )


@documents.route("/<int:doc_id>/edit", methods=["GET", "POST"])
@login_required
def edit(doc_id):
    doc = Document.query.filter_by(id=doc_id, is_deleted=False).first_or_404()

    form = DocumentEditForm(obj=doc)

    categories = (
        Category.query.filter_by(is_active=True)
        .order_by(Category.sort_order, Category.name)
        .all()
    )
    periods = (
        AcademicPeriod.query.filter_by(is_active=True)
        .order_by(AcademicPeriod.year_start.desc(), AcademicPeriod.semester)
        .all()
    )
    correspondents = Correspondent.query.order_by(Correspondent.name).all()

    form.category.choices = [(c.id, c.name) for c in categories]
    form.academic_period.choices = [
        (p.id, f"{p.year_start}-{p.year_end} {p.semester}") for p in periods
    ]
    form.correspondent.choices = [(0, "None")] + [
        (c.id, c.name) for c in correspondents
    ]

    if form.validate_on_submit():
        doc.title = form.title.data
        doc.description = form.description.data
        doc.correspondent_id = (
            form.correspondent.data if form.correspondent.data > 0 else None
        )

        new_category = Category.query.get(form.category.data)
        new_period = AcademicPeriod.query.get(form.academic_period.data)

        if (
            new_category.id != doc.category_id
            or new_period.id != doc.academic_period_id
        ):
            new_folder_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                new_period.folder_name,
                new_category.slug,
            )
            os.makedirs(new_folder_path, exist_ok=True)
            new_file_path = os.path.join(new_folder_path, doc.stored_filename)

            if os.path.exists(doc.file_path):
                os.rename(doc.file_path, new_file_path)

            doc.file_path = new_file_path
            doc.category_id = new_category.id
            doc.academic_period_id = new_period.id

        tag_names = [t.name for t in doc.tags]
        new_tags = []
        if form.tags.data:
            for tag_name in form.tags.data.split(","):
                tag_name = tag_name.strip()
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    new_tags.append(tag)

        doc.tags = new_tags
        doc.updated_at = datetime.utcnow()

        db.session.commit()

        # Update index in Meilisearch
        index_document(doc)

        log_audit_action("edit", doc.id, {"changes": form.data})

        flash(f'Document "{doc.title}" updated successfully!', "success")
        return redirect(url_for("documents.detail", doc_id=doc.id))

    form.category.data = doc.category_id
    form.academic_period.data = doc.academic_period_id
    form.correspondent.data = doc.correspondent_id or 0
    form.tags.data = ", ".join([t.name for t in doc.tags])

    return render_template(
        "documents/edit.html",
        form=form,
        document=doc,
        categories=categories,
        periods=periods,
    )


@documents.route("/<int:doc_id>/delete", methods=["POST"])
@login_required
def delete(doc_id):
    doc = Document.query.filter_by(id=doc_id, is_deleted=False).first_or_404()

    doc.is_deleted = True
    doc.deleted_at = datetime.utcnow()

    db.session.commit()

    # Remove from Meilisearch index
    delete_document_from_index(doc.id)

    log_audit_action("delete", doc.id)

    flash(f'Document "{doc.title}" moved to trash.', "info")
    return redirect(url_for("documents.list"))


@documents.route("/trash")
@login_required
def trash():
    documents = (
        Document.query.filter_by(is_deleted=True)
        .order_by(Document.deleted_at.desc())
        .all()
    )
    return render_template("documents/trash.html", documents=documents)


@documents.route("/<int:doc_id>/restore")
@login_required
def restore(doc_id):
    doc = Document.query.filter_by(id=doc_id, is_deleted=True).first_or_404()

    doc.is_deleted = False
    doc.deleted_at = None

    db.session.commit()

    # Re-index in Meilisearch
    index_document(doc)

    log_audit_action("restore", doc.id)

    flash(f'Document "{doc.title}" restored successfully!', "success")
    return redirect(url_for("documents.detail", doc_id=doc.id))


@documents.route("/<int:doc_id>/editor", methods=["GET", "POST"])
@login_required
def editor(doc_id):
    doc = Document.query.filter_by(id=doc_id, is_deleted=False).first_or_404()
    form = DocumentEditForm(obj=doc)

    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    periods = (
        AcademicPeriod.query.filter_by(is_active=True)
        .order_by(AcademicPeriod.year_start.desc())
        .all()
    )
    correspondents = Correspondent.query.order_by(Correspondent.name).all()

    form.category.choices = [(c.id, c.name) for c in categories]
    form.academic_period.choices = [(p.id, p.name) for p in periods]
    form.correspondent.choices = [(0, "None")] + [
        (c.id, c.name) for c in correspondents
    ]

    if form.validate_on_submit():
        doc.title = form.title.data
        doc.description = form.description.data
        doc.correspondent_id = (
            form.correspondent.data if form.correspondent.data > 0 else None
        )

        # ... logic for category/period change ...
        new_category = Category.query.get(form.category.data)
        new_period = AcademicPeriod.query.get(form.academic_period.data)

        if (
            new_category.id != doc.category_id
            or new_period.id != doc.academic_period_id
        ):
            new_folder_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                new_period.folder_name,
                new_category.slug,
            )
            os.makedirs(new_folder_path, exist_ok=True)
            new_file_path = os.path.join(new_folder_path, doc.stored_filename)
            if os.path.exists(doc.file_path):
                os.rename(doc.file_path, new_file_path)
            doc.file_path = new_file_path
            doc.category_id = new_category.id
            doc.academic_period_id = new_period.id

        # Update tags
        new_tags = []
        if form.tags.data:
            for tag_name in form.tags.data.split(","):
                tag_name = tag_name.strip()
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    new_tags.append(tag)
        doc.tags = new_tags

        db.session.commit()
        index_document(doc)
        flash(f'Document "{doc.title}" updated.', "success")
        return redirect(url_for("documents.editor", doc_id=doc.id))

    form.category.data = doc.category_id
    form.academic_period.data = doc.academic_period_id
    form.correspondent.data = doc.correspondent_id or 0
    form.tags.data = ", ".join([t.name for t in doc.tags])

    preview = get_file_preview(doc.file_path, doc.mime_type)
    return render_template(
        "documents/editor.html", form=form, document=doc, preview=preview
    )
