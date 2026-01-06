import os
import random
import uuid
from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import Document, Category, AcademicPeriod, Tag


def random_date():
    start = datetime(2024, 1, 1)
    end = datetime(2025, 1, 5)
    return start + timedelta(days=random.randint(0, (end - start).days))


def generate_fake_documents(count=100):
    app = create_app("default")
    with app.app_context():
        categories = Category.query.all()
        periods = AcademicPeriod.query.all()
        tags = Tag.query.all()

        if not categories or not periods:
            print("Please run init-db.py first to create categories and periods.")
            return

        sample_titles = [
            "Student Enrollment Report",
            "Course Curriculum Outline",
            "Exam Schedule Spring 2024",
            "Financial Aid Application",
            "Faculty Meeting Minutes",
            "Budget Proposal FY2024",
            "Admission Guidelines",
            "Scholarship Award List",
            "Transcript Request Form",
            "Attendance Record",
            "Course Registration List",
            "Grade Distribution Analysis",
            "Staff Payroll Report",
            "Building Maintenance Request",
            "Library Book Inventory",
            "Research Grant Proposal",
            "Alumni Survey Results",
            "Internship Placement Report",
            "Event Planning Checklist",
            "Policy Revision Document",
            "Staff Evaluation Form",
            "Student Feedback Summary",
            "Academic Calendar Draft",
            "Graduation Ceremony Program",
            "Disciplinary Action Report",
            "IT Support Ticket Log",
            "Campus Safety Guidelines",
            "Sports Team Roster",
            "Club Registration Form",
            "Housing Allocation List",
        ]

        sample_descriptions = [
            "Important document for academic records.",
            "Required for annual audit.",
            "Reference material for faculty.",
            "Student request submitted.",
            "Administrative documentation.",
            "Confidential records.",
            "Annual report summary.",
            "Meeting notes and action items.",
            "Official college correspondence.",
            "Internal memorandum.",
        ]

        upload_folder = app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)

        for i in range(count):
            category = random.choice(categories)
            period = random.choice(periods)

            title = f"{random.choice(sample_titles)} - {random.randint(100, 999)}"

            original_filename = f"{title.replace(' ', '_')}.pdf"
            stored_filename = f"{uuid.uuid4()}.pdf"
            folder_path = os.path.join(upload_folder, period.folder_name, category.slug)
            os.makedirs(folder_path, exist_ok=True)
            file_path = os.path.join(folder_path, stored_filename)

            with open(file_path, "w") as f:
                f.write(f"Document: {title}\n")
                f.write(f"Category: {category.name}\n")
                f.write(f"Period: {period.name}\n")
                f.write(f"Description: {random.choice(sample_descriptions)}\n")
                f.write("\n" + "Lorem ipsum " * 100)

            file_size = os.path.getsize(file_path)

            doc = Document(
                title=title,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_size=file_size,
                mime_type="application/pdf",
                content_text=f"Document {title} content for search indexing.",
                description=random.choice(sample_descriptions),
                category_id=category.id,
                academic_period_id=period.id,
                uploaded_by=1,
                uploaded_at=random_date(),
            )

            if tags and random.random() > 0.3:
                selected_tags = random.sample(
                    tags, random.randint(1, min(3, len(tags)))
                )
                for tag in selected_tags:
                    doc.tags.append(tag)

            db.session.add(doc)

            if (i + 1) % 10 == 0:
                db.session.commit()
                print(f"Created {i + 1}/{count} documents...")

        db.session.commit()
        print(f"Successfully created {count} documents!")


if __name__ == "__main__":
    generate_fake_documents(100)
