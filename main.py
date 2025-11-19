import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Settings, Project

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class ObjectIdStr(str):
    pass


def to_serializable(doc: dict):
    if not doc:
        return doc
    doc = dict(doc)
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["id"] = str(doc.pop("_id"))
    return doc


# Public endpoints
@app.get("/")
def read_root():
    return {"message": "Portfolio API running"}


@app.get("/api/public/settings")
def get_public_settings():
    try:
        docs = get_documents("settings", {}, limit=1)
        return to_serializable(docs[0]) if docs else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/public/projects")
def list_public_projects():
    try:
        docs = get_documents("project", {})
        return [to_serializable(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Admin models
class SettingsIn(Settings):
    pass


class ProjectIn(Project):
    pass


# Admin endpoints
@app.post("/api/admin/settings")
def upsert_settings(payload: SettingsIn):
    try:
        # For simplicity, keep a single settings doc: delete others, insert new
        if db is None:
            raise Exception("Database not available")
        db["settings"].delete_many({})
        inserted_id = create_document("settings", payload)
        doc = db["settings"].find_one({"_id": ObjectId(inserted_id)})
        return to_serializable(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/projects")
def create_project(payload: ProjectIn):
    try:
        inserted_id = create_document("project", payload)
        doc = db["project"].find_one({"_id": ObjectId(inserted_id)})
        return to_serializable(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/projects")
def list_projects_admin():
    try:
        docs = get_documents("project", {})
        return [to_serializable(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    image_url: Optional[str] = None
    live_url: Optional[str] = None
    repo_url: Optional[str] = None


@app.put("/api/admin/projects/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate):
    try:
        if not ObjectId.is_valid(project_id):
            raise HTTPException(status_code=400, detail="Invalid project id")
        data = {k: v for k, v in payload.model_dump().items() if v is not None}
        if not data:
            return {"updated": False}
        data["updated_at"] = db["project"].find_one({"_id": ObjectId(project_id)}).get("updated_at")
        db["project"].update_one({"_id": ObjectId(project_id)}, {"$set": data})
        doc = db["project"].find_one({"_id": ObjectId(project_id)})
        return to_serializable(doc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/admin/projects/{project_id}")
def delete_project(project_id: str):
    try:
        if not ObjectId.is_valid(project_id):
            raise HTTPException(status_code=400, detail="Invalid project id")
        res = db["project"].delete_one({"_id": ObjectId(project_id)})
        return {"deleted": res.deleted_count == 1}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
