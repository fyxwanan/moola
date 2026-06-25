from bson import ObjectId

def serialize_doc(doc: dict) -> dict:
    """Recursively converts MongoDB BSON fields (like ObjectId) to string for JSON serialization."""
    if not doc:
        return doc
    serialized = {}
    for k, v in doc.items():
        if k == "_id":
            serialized["id"] = str(v)
        elif isinstance(v, ObjectId):
            serialized[k] = str(v)
        elif isinstance(v, list):
            serialized[k] = [str(x) if isinstance(x, ObjectId) else serialize_doc(x) if isinstance(x, dict) else x for x in v]
        elif isinstance(v, dict):
            serialized[k] = serialize_doc(v)
        else:
            serialized[k] = v
    return serialized

def serialize_list(docs: list) -> list:
    return [serialize_doc(doc) for doc in docs]
