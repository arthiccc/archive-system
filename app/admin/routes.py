from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models import Document, Category, AcademicPeriod, Tag, AuditLog, AdminUser
from . import admin


@admin.route("/")
@login_required
def dashboard():
    total_docs = Document.query.filter_by(is_deleted=False).count()
    total_categories = Category.query.count()
    total_periods = AcademicPeriod.query.count()
    total_tags = Tag.query.count()

    recent_uploads = (
        Document.query.filter_by(is_deleted=False)
        .order_by(Document.uploaded_at.desc())
        .limit(5)
        .all()
    )

    recent_activity = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()

    docs_this_month = Document.query.filter(
        Document.is_deleted == False,
        func.date_trunc("month", Document.uploaded_at)
        == func.date_trunc("month", func.current_timestamp()),
    ).count()

    docs_by_category = (
        db.session.query(Category.name, func.count(Document.id))
        .join(Document)
        .filter(Document.is_deleted == False)
        .group_by(Category.name)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        total_docs=total_docs,
        total_categories=total_categories,
        total_periods=total_periods,
        total_tags=total_tags,
        recent_uploads=recent_uploads,
        recent_activity=recent_activity,
        docs_this_month=docs_this_month,
        docs_by_category=docs_by_category,
    )


@admin.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    from app.admin.forms import CategoryForm

    if request.method == "POST":
        name = request.form.get("name")
        parent_id = request.form.get("parent_id") or None
        description = request.form.get("description", "")

        slug = name.lower().replace(" ", "-").replace("_", "-")

        existing = Category.query.filter_by(slug=slug).first()
        if existing:
            flash("Category with similar name exists.", "danger")
        else:
            category = Category(
                name=name, slug=slug, description=description, parent_id=parent_id
            )
            db.session.add(category)
            db.session.commit()
            flash(f'Category "{name}" created.', "success")

    categories = Category.query.order_by(Category.sort_order, Category.name).all()
    root_categories = (
        Category.query.filter_by(parent_id=None).order_by(Category.sort_order).all()
    )

    return render_template(
        "admin/categories.html", categories=categories, root_categories=root_categories
    )


@admin.route("/categories/<int:id>/edit", methods=["POST"])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    category.name = request.form.get("name", category.name)
    category.description = request.form.get("description", category.description)
    parent_id = request.form.get("parent_id")
    category.parent_id = parent_id if parent_id else None

    db.session.commit()
    flash("Category updated.", "success")
    return redirect(url_for("admin.categories"))


@admin.route("/categories/<int:id>/delete")
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    if category.documents:
        flash("Cannot delete category with documents.", "danger")
    else:
        db.session.delete(category)
        db.session.commit()
        flash("Category deleted.", "success")
    return redirect(url_for("admin.categories"))


@admin.route("/periods", methods=["GET", "POST"])
@login_required
def periods():
    if request.method == "POST":
        year_start = request.form.get("year_start", type=int)
        year_end = request.form.get("year_end", type=int)
        semester = request.form.get("semester")

        if year_start and year_end and semester:
            existing = AcademicPeriod.query.filter_by(
                year_start=year_start, year_end=year_end, semester=semester
            ).first()

            if existing:
                flash("Academic period already exists.", "danger")
            else:
                period = AcademicPeriod(
                    year_start=year_start, year_end=year_end, semester=semester
                )
                db.session.add(period)
                db.session.commit()
                flash("Academic period created.", "success")

    periods = AcademicPeriod.query.order_by(
        AcademicPeriod.year_start.desc(), AcademicPeriod.semester
    ).all()

    return render_template("admin/periods.html", periods=periods)


@admin.route("/periods/<int:id>/toggle")
@login_required
def toggle_period(id):
    period = AcademicPeriod.query.get_or_404(id)
    period.is_active = not period.is_active
    db.session.commit()
    flash(f"Period {'activated' if period.is_active else 'deactivated'}.", "success")
    return redirect(url_for("admin.periods"))


@admin.route("/periods/<int:id>/delete")
@login_required
def delete_period(id):
    period = AcademicPeriod.query.get_or_404(id)
    if period.documents:
        flash("Cannot delete period with documents.", "danger")
    else:
        db.session.delete(period)
        db.session.commit()
        flash("Period deleted.", "success")
    return redirect(url_for("admin.periods"))


@admin.route("/tags", methods=["GET", "POST"])
@login_required
def tags():
    if request.method == "POST":
        name = request.form.get("name")
        color = request.form.get("color", "#6c757d")

        if name:
            existing = Tag.query.filter_by(name=name).first()
            if existing:
                flash("Tag already exists.", "danger")
            else:
                tag = Tag(name=name, color=color)
                db.session.add(tag)
                db.session.commit()
                flash(f'Tag "{name}" created.', "success")

    tags = Tag.query.order_by(Tag.name).all()

    return render_template("admin/tags.html", tags=tags)


@admin.route("/tags/<int:id>/edit", methods=["POST"])
@login_required
def edit_tag(id):
    tag = Tag.query.get_or_404(id)
    tag.name = request.form.get("name", tag.name)
    tag.color = request.form.get("color", tag.color)
    db.session.commit()
    flash("Tag updated.", "success")
    return redirect(url_for("admin.tags"))


@admin.route("/tags/<int:id>/delete")
@login_required
def delete_tag(id):
    tag = Tag.query.get_or_404(id)
    db.session.delete(tag)
    db.session.commit()
    flash("Tag deleted.", "success")
    return redirect(url_for("admin.tags"))


@admin.route("/logs")
@login_required
def logs():
    page = request.args.get("page", 1, type=int)
    per_page = 50

    action_filter = request.args.get("action")
    user_filter = request.args.get("user", type=int)
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    query = AuditLog.query

    if action_filter:
        query = query.filter_by(action=action_filter)
    if user_filter:
        query = query.filter_by(admin_user_id=user_filter)
    if date_from:
        from datetime import datetime

        try:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(AuditLog.timestamp >= date_from_dt)
        except:
            pass
    if date_to:
        from datetime import datetime

        try:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            query = query.filter(AuditLog.timestamp <= date_to_dt)
        except:
            pass

    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    users = AdminUser.query.all()

    return render_template(
        "admin/logs.html", logs=pagination.items, pagination=pagination, users=users
    )


@admin.route("/stats")
@login_required
def stats():
    docs_by_month = (
        db.session.query(
            func.date_trunc("month", Document.uploaded_at).label("month"),
            func.count(Document.id),
        )
        .filter(Document.is_deleted == False)
        .group_by("month")
        .order_by("month")
        .all()
    )

    period_name = func.concat(
        AcademicPeriod.year_start,
        "-",
        AcademicPeriod.year_end,
        " ",
        AcademicPeriod.semester,
    ).label("name")

    docs_by_period = (
        db.session.query(period_name, func.count(Document.id))
        .join(Document)
        .filter(Document.is_deleted == False)
        .group_by(
            AcademicPeriod.year_start, AcademicPeriod.year_end, AcademicPeriod.semester
        )
        .all()
    )

    top_categories = (
        db.session.query(Category.name, func.count(Document.id))
        .join(Document)
        .filter(Document.is_deleted == False)
        .group_by(Category.name)
        .order_by(func.count(Document.id).desc())
        .limit(10)
        .all()
    )

    return render_template(
        "admin/stats.html",
        docs_by_month=docs_by_month,
        docs_by_period=docs_by_period,
        top_categories=top_categories,
    )
