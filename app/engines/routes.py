import os
import json
from datetime import datetime
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    send_file,
)
from flask_login import login_required, current_user
from app.extensions import db
from app.models import LetterTemplate, Document, Category, AcademicPeriod
from app.engines.template_engine import get_template_variables, generate_document
from app.search.services import index_document
from . import engines


@engines.route("/")
@login_required
def index():
    return redirect(url_for("engines.workbench"))


@engines.route("/workbench")
@login_required
def workbench():
    templates = LetterTemplate.query.all()
    selected_template_id = request.args.get("template_id", type=int)

    selected_template = None
    variables = []
    if selected_template_id:
        selected_template = LetterTemplate.query.get(selected_template_id)
        if selected_template:
            variables = json.loads(selected_template.variables_json)

    # Get recent letters for the sidebar
    recent_letters = (
        Document.query.filter(Document.template_id != None)
        .order_by(Document.uploaded_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "engines/workbench.html",
        templates=templates,
        selected_template=selected_template,
        variables=variables,
        recent_letters=recent_letters,
    )


@engines.route("/templates/upload", methods=["POST"])
@login_required
def upload_template():
    if "file" not in request.files:
        flash("No file part", "error")
        return redirect(url_for("engines.workbench"))

    file = request.files["file"]
    if file.filename == "":
        flash("No selected file", "error")
        return redirect(url_for("engines.workbench"))

    if file and file.filename.endswith(".docx"):
        filename = file.filename
        file_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"], "templates", filename
        )
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)

        # Extract variables
        variables = get_template_variables(file_path)

        template = LetterTemplate(
            name=os.path.splitext(filename)[0],
            file_path=file_path,
            variables_json=json.dumps(variables),
        )
        db.session.add(template)
        db.session.commit()

        flash(f"Template '{template.name}' uploaded successfully!", "success")
    else:
        flash("Only .docx files are supported for templates", "error")

    return redirect(url_for("engines.workbench"))


@engines.route("/generate", methods=["POST"])
@login_required
def generate():
    template_id = request.form.get("template_id", type=int)
    template = LetterTemplate.query.get_or_404(template_id)

    # Collect context from form
    context = {}
    variables = json.loads(template.variables_json)
    for var in variables:
        context[var] = request.form.get(var)

    # Output filename
    recipient = context.get("student_name", context.get("recipient", "document"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{recipient}_{timestamp}.docx"

    try:
        # Generate the docx
        file_path = generate_document(template_id, context, output_filename)

        # Create Document entry in registry
        # We need a default category and period if not specified
        category = Category.query.filter_by(slug="letters").first()
        if not category:
            category = Category(name="Letters", slug="letters")
            db.session.add(category)
            db.session.commit()

        period = AcademicPeriod.query.order_by(AcademicPeriod.year_start.desc()).first()

        now = datetime.now()
        doc = Document(
            title=os.path.splitext(output_filename)[0],
            original_filename=output_filename,
            stored_filename=output_filename,
            file_path=file_path,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            year=now.year,
            month=now.month,
            category_id=category.id,
            academic_period_id=period.id if period else None,
            template_id=template.id,
            uploaded_by=current_user.id,
        )

        db.session.add(doc)
        db.session.commit()

        # Index in Meilisearch
        index_document(doc)

        flash("Document generated and archived successfully!", "success")
        return redirect(url_for("engines.workbench", template_id=template.id))

    except Exception as e:
        flash(f"Generation failed: {str(e)}", "error")
        return redirect(url_for("engines.workbench", template_id=template.id))


@engines.route("/registry")
@login_required
def registry():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    query = Document.query.filter_by(is_deleted=False)
    if year:
        query = query.filter_by(year=year)
    if month:
        query = query.filter_by(month=month)

    documents = query.order_by(Document.uploaded_at.desc()).all()

    # Get available years and months for filters
    available_years = (
        db.session.query(Document.year).distinct().order_by(Document.year.desc()).all()
    )
    available_years = [y[0] for y in available_years if y[0]]

    return render_template(
        "engines/registry.html",
        documents=documents,
        years=available_years,
        selected_year=year,
        selected_month=month,
    )
