from app.extensions import db
from app.models import AcademicPeriod, Category, Tag


def init_db(app):
    with app.app_context():
        db.create_all()

        if AcademicPeriod.query.count() == 0:
            periods = [
                AcademicPeriod(year_start=2024, year_end=2025, semester="Fall"),
                AcademicPeriod(year_start=2024, year_end=2025, semester="Spring"),
                AcademicPeriod(year_start=2024, year_end=2025, semester="Summer"),
                AcademicPeriod(year_start=2025, year_end=2026, semester="Fall"),
            ]
            for p in periods:
                db.session.add(p)
            db.session.commit()

        if Category.query.count() == 0:
            cats = [
                Category(
                    name="Admissions",
                    slug="admissions",
                    description="Student admissions documents",
                ),
                Category(
                    name="Student Applications",
                    slug="student-applications",
                    parent_id=1,
                ),
                Category(
                    name="Acceptance Letters", slug="acceptance-letters", parent_id=1
                ),
                Category(
                    name="Finance", slug="finance", description="Financial documents"
                ),
                Category(name="Fee Structures", slug="fee-structures", parent_id=4),
                Category(name="Scholarships", slug="scholarships", parent_id=4),
                Category(name="Payroll", slug="payroll", parent_id=4),
                Category(
                    name="Academics", slug="academics", description="Academic documents"
                ),
                Category(name="Curriculum", slug="curriculum", parent_id=8),
                Category(name="Exam Papers", slug="exam-papers", parent_id=8),
                Category(name="Transcripts", slug="transcripts", parent_id=8),
                Category(name="HR", slug="hr", description="Human Resources"),
                Category(name="Staff Records", slug="staff-records", parent_id=12),
                Category(name="Recruitment", slug="recruitment", parent_id=12),
                Category(name="Student Affairs", slug="student-affairs"),
                Category(name="Discipline", slug="discipline", parent_id=15),
                Category(name="Activities", slug="activities", parent_id=15),
            ]
            for c in cats:
                db.session.add(c)
            db.session.commit()

        if Tag.query.count() == 0:
            tags = [
                Tag(name="Urgent", color="#dc3545"),
                Tag(name="Confidential", color="#6f42c1"),
                Tag(name="Draft", color="#fd7e14"),
                Tag(name="Final", color="#28a745"),
                Tag(name="FY2024-2025", color="#17a2b8"),
                Tag(name="FY2025-2026", color="#20c997"),
                Tag(name="Audit Ready", color="#6610f2"),
            ]
            for t in tags:
                db.session.add(t)
            db.session.commit()

        print("Database initialized successfully!")


if __name__ == "__main__":
    from app import create_app

    app = create_app("default")
    init_db(app)
