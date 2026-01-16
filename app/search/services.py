import meilisearch_python_sdk
from flask import current_app
from app.models import Document


def get_meili_client():
    return meilisearch_python_sdk.Client(
        current_app.config["MEILI_HTTP_ADDR"], current_app.config["MEILI_MASTER_KEY"]
    )


def get_meili_index():
    client = get_meili_client()
    return client.index(current_app.config["MEILI_INDEX_NAME"])


def index_document(document):
    """
    Indexes a single document in Meilisearch.
    """
    try:
        index = get_meili_index()

        # Prepare document for indexing
        doc_data = {
            "id": document.id,
            "title": document.title,
            "content": document.content_text,
            "description": document.description,
            "original_filename": document.original_filename,
            "category": document.category.name if document.category else None,
            "period": document.academic_period.name
            if document.academic_period
            else None,
            "year": document.year,
            "month": document.month,
            "tags": [tag.name for tag in document.tags],
            "uploaded_at": int(document.uploaded_at.timestamp()),
            "mime_type": document.mime_type,
        }

        index.add_documents([doc_data])
    except Exception as e:
        current_app.logger.error(f"Failed to index document {document.id}: {str(e)}")


def delete_document_from_index(document_id):
    """
    Removes a document from the Meilisearch index.
    """
    try:
        index = get_meili_index()
        index.delete_document(str(document_id))
    except Exception as e:
        current_app.logger.error(
            f"Failed to delete document {document_id} from index: {str(e)}"
        )


def search_documents(query, filters=None, limit=20, offset=0):
    """
    Searches documents in Meilisearch.
    """
    try:
        index = get_meili_index()

        search_params = {
            "limit": limit,
            "offset": offset,
            "attributesToHighlight": ["content", "title", "description"],
            "attributesToSnippet": ["content:50"],
            "highlightPreTag": "<mark>",
            "highlightPostTag": "</mark>",
        }

        if filters:
            search_params["filter"] = filters

        return index.search(query, search_params)
    except Exception as e:
        current_app.logger.error(f"Search failed: {str(e)}")
        return None
