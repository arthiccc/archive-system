from flask import render_template, request
from flask_login import login_required
from sqlalchemy import or_
from app.models import Document, Category, AcademicPeriod, Tag
from app.search.services import search_documents
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

    results = []
    total_count = 0
    search_performed = False
    highlights = {}

    if query or category_id or period_id or tag_id or date_from or date_to:
        search_performed = True

        # Build Meilisearch filters
        ms_filters = []
        if category_id:
            cat = Category.query.get(category_id)
            if cat:
                ms_filters.append(f"category = '{cat.name}'")
        if period_id:
            per = AcademicPeriod.query.get(period_id)
            if per:
                ms_filters.append(f"period = '{per.name}'")
        if tag_id:
            tag = Tag.query.get(tag_id)
            if tag:
                ms_filters.append(f"tags = '{tag.name}'")

        # Note: date filtering in Meilisearch would require timestamps
        # For now, let's focus on the main query

        filter_str = " AND ".join(ms_filters) if ms_filters else None

        ms_results = search_documents(query, filters=filter_str)

        if ms_results:
            total_count = ms_results.total_hits
            doc_ids = [hit["id"] for hit in ms_results.hits]

            # Fetch documents from DB to ensure they exist and get all data
            # Keep Meilisearch order
            if doc_ids:
                db_docs = Document.query.filter(
                    Document.id.in_(doc_ids), Document.is_deleted == False
                ).all()
                doc_map = {doc.id: doc for doc in db_docs}

                for hit in ms_results.hits:
                    doc_id = int(hit["id"])
                    if doc_id in doc_map:
                        results.append(doc_map[doc_id])
                        # Store highlights from _formatted
                        highlights[doc_id] = hit.get("_formatted", {})

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
        highlights=highlights,
    )
