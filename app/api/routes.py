from flask import request, jsonify
from sqlalchemy import or_, func
from app.extensions import db
from app.models import Document, Category, AcademicPeriod, Tag
from app.api import api


@api.route("/documents", methods=["GET"])
def list_documents():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
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

    return {
        "documents": [doc_to_dict(d) for d in pagination.items],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    }


@api.route("/documents/<int:doc_id>", methods=["GET"])
def get_document(doc_id):
    doc = Document.query.filter_by(id=doc_id, is_deleted=False).first_or_404()
    return jsonify(doc_to_dict(doc))


@api.route("/categories", methods=["GET"])
def list_categories():
    categories = (
        Category.query.filter_by(is_active=True)
        .order_by(Category.sort_order, Category.name)
        .all()
    )
    return jsonify([cat_to_dict(c) for c in categories])


@api.route("/periods", methods=["GET"])
def list_periods():
    periods = (
        AcademicPeriod.query.filter_by(is_active=True)
        .order_by(AcademicPeriod.year_start.desc(), AcademicPeriod.semester)
        .all()
    )
    return jsonify([period_to_dict(p) for p in periods])


@api.route("/tags", methods=["GET"])
def list_tags():
    tags = Tag.query.order_by(Tag.name).all()
    return jsonify([tag_to_dict(t) for t in tags])


@api.route("/admin/stats", methods=["GET"])
def admin_stats():
    total_docs = Document.query.filter_by(is_deleted=False).count()
    total_categories = Category.query.count()
    total_periods = AcademicPeriod.query.count()
    total_tags = Tag.query.count()

    this_month = func.date_trunc("month", Document.uploaded_at) == func.date_trunc(
        "month", func.current_timestamp()
    )
    docs_this_month = Document.query.filter(
        Document.is_deleted == False, this_month
    ).count()

    return {
        "doc_count": total_docs,
        "docs_this_month": docs_this_month,
        "total_categories": total_categories,
        "total_periods": total_periods,
        "total_tags": total_tags,
    }


@api.route("/search", methods=["GET"])
def search_documents():
    from flask import request

    query_str = request.args.get("q", "")
    category_id = request.args.get("category", type=int)
    period_id = request.args.get("period", type=int)
    tag_id = request.args.get("tag", type=int)

    base_query = Document.query.filter_by(is_deleted=False)

    if query_str:
        search_term = f"%{query_str}%"
        base_query = base_query.filter(
            or_(
                Document.title.ilike(search_term),
                Document.original_filename.ilike(search_term),
                Document.description.ilike(search_term),
                Document.content_text.ilike(search_term),
            )
        )

    if category_id:
        base_query = base_query.filter_by(category_id=category_id)
    if period_id:
        base_query = base_query.filter_by(academic_period_id=period_id)
    if tag_id:
        base_query = base_query.filter(Document.tags.any(id=tag_id))

    results = base_query.order_by(Document.uploaded_at.desc()).all()

    return {
        "results": [doc_to_dict(d) for d in results],
        "total_count": len(results),
        "query": query_str,
    }


def doc_to_dict(doc):
    return {
        "id": doc.id,
        "title": doc.title,
        "original_filename": doc.original_filename,
        "file_size": doc.file_size,
        "mime_type": doc.mime_type,
        "description": doc.description,
        "category_id": doc.category_id,
        "academic_period_id": doc.academic_period_id,
        "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        "tags": [t.name for t in doc.tags] if doc.tags else [],
    }


def cat_to_dict(cat):
    return {
        "id": cat.id,
        "name": cat.name,
        "slug": cat.slug,
        "parent_id": cat.parent_id,
        "full_path": cat.full_path() if hasattr(cat, "full_path") else cat.name,
    }


def period_to_dict(period):
    return {
        "id": period.id,
        "name": period.name,
        "year_start": period.year_start,
        "year_end": period.year_end,
        "semester": period.semester,
    }


def tag_to_dict(tag):
    return {
        "id": tag.id,
        "name": tag.name,
        "color": tag.color,
    }
