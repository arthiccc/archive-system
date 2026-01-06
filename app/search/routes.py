from flask import render_template, request
from flask_login import login_required
from sqlalchemy import or_, func
from app.extensions import db
from app.models import Document, Category, AcademicPeriod, Tag
from . import search


@search.route("/")
@login_required
def index():
    query = request.args.get("q", "")
    category_id = request.args.get("category", type=int)
    period_id = request.args.get("period", type=int)
    tag_id = request.args.get("tag", type=int)
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    results = None
    total_count = 0
    search_performed = False

    if query or category_id or period_id or tag_id or date_from or date_to:
        search_performed = True

        base_query = Document.query.filter_by(is_deleted=False)

        if query:
            search_term = f"%{query}%"
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

        if date_from:
            from datetime import datetime

            try:
                date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
                base_query = base_query.filter(Document.uploaded_at >= date_from_dt)
            except:
                pass

        if date_to:
            from datetime import datetime

            try:
                date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
                base_to = date_to_dt.replace(hour=23, minute=59, second=59)
                base_query = base_query.filter(Document.uploaded_at <= date_to_dt)
            except:
                pass

        results = base_query.order_by(Document.uploaded_at.desc()).all()
        total_count = len(results)

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
        "search/index.html",
        results=results,
        total_count=total_count,
        search_performed=search_performed,
        query=query,
        categories=categories,
        periods=periods,
        tags=tags,
    )
