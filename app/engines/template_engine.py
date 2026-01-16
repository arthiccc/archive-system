import os
import json
from docxtpl import DocxTemplate
from flask import current_app
from app.models import LetterTemplate


def get_template_variables(file_path):
    """
    Extracts Jinja2 variables from a docx template.
    """
    try:
        doc = DocxTemplate(file_path)
        # Force a dummy render to get variables
        variables = doc.get_undeclared_template_variables()
        return list(variables)
    except Exception as e:
        current_app.logger.error(f"Failed to extract variables from {file_path}: {e}")
        return []


def generate_document(template_id, context, output_filename):
    """
    Generates a docx file from a template and context.
    """
    template = LetterTemplate.query.get(template_id)
    if not template:
        raise ValueError("Template not found")

    try:
        doc = DocxTemplate(template.file_path)
        doc.render(context)

        output_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"], "generated", output_filename
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        doc.save(output_path)
        return output_path
    except Exception as e:
        current_app.logger.error(f"Failed to generate document: {e}")
        raise
