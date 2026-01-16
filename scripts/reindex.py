from app import create_app
from app.models import Document
from app.search.services import index_document, get_meili_index


def reindex_all():
    app = create_app("default")
    with app.app_context():
        # Clear existing index
        try:
            index = get_meili_index()
            index.delete_all_documents()
            print("Cleared existing index.")
        except Exception as e:
            print(f"Could not clear index: {e}")

        documents = Document.query.filter_by(is_deleted=False).all()
        total = len(documents)
        print(f"Reindexing {total} documents...")

        for i, doc in enumerate(documents):
            index_document(doc)
            if (i + 1) % 10 == 0:
                print(f"Indexed {i + 1}/{total}...")

        print("Reindexing complete!")


if __name__ == "__main__":
    reindex_all()
