import os
import json
from app import create_app
from app.extensions import db
from app.models import LetterTemplate
from app.engines.template_engine import get_template_variables


def import_existing_templates():
    app = create_app("default")
    with app.app_context():
        # Directory where you can drop the docx files
        template_dir = os.path.join(app.config["UPLOAD_FOLDER"], "templates")
        os.makedirs(template_dir, exist_ok=True)

        files = [f for f in os.listdir(template_dir) if f.endswith(".docx")]

        if not files:
            print(
                f"No .docx files found in {template_dir}. Please place your letters there."
            )
            return

        print(f"Detected {len(files)} potential templates. Starting ingestion...")

        for filename in files:
            file_path = os.path.join(template_dir, filename)
            name = os.path.splitext(filename)[0]

            # Check if already registered
            existing = LetterTemplate.query.filter_by(name=name).first()
            if existing:
                print(f"Skipping '{name}': Already registered.")
                continue

            # Extract variables using docxtpl
            variables = get_template_variables(file_path)

            template = LetterTemplate(
                name=name, file_path=file_path, variables_json=json.dumps(variables)
            )
            db.session.add(template)
            print(
                f"Successfully ingested '{name}' with {len(variables)} variables: {variables}"
            )

        db.session.commit()
        print("Template registration complete!")


if __name__ == "__main__":
    import_existing_templates()
