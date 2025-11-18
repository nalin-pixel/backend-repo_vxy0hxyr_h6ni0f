import os
import hashlib
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Artifact, UserAccount


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class SigninRequest(BaseModel):
    email: EmailStr
    password: str


class PublicArtifact(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    period: Optional[str] = None
    collection: Optional[str] = None
    tags: Optional[List[str]] = None


app = FastAPI(title="NEUST Museum API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "NEUST Museum API Running"}


@app.get("/api/about")
def get_about():
    return {
        "name": "NEUST Museum",
        "tagline": "Preserving history, inspiring discovery.",
        "history": "The NEUST Museum curates a diverse collection of artifacts spanning culture, technology, and the environment. Our mission is to educate and inspire through immersive exhibits and community programs.",
        "mission": "To conserve, research, and share artifacts that connect people with the past and future.",
        "vision": "A world where learning from history shapes a sustainable and innovative future.",
        "contact": {
            "email": "info@neustmuseum.edu",
            "phone": "+1 (555) 123-4567",
            "address": "123 University Ave, Science City",
        },
    }


@app.get("/api/visit")
def get_visit():
    return {
        "hours": [
            {"days": "Mon-Fri", "time": "9:00 AM - 6:00 PM"},
            {"days": "Sat", "time": "10:00 AM - 5:00 PM"},
            {"days": "Sun", "time": "Closed"},
        ],
        "location": {
            "address": "123 University Ave, Science City",
            "map": "https://maps.google.com/?q=NEUST+Museum",
        },
        "contact": {
            "email": "visit@neustmuseum.edu",
            "phone": "+1 (555) 987-6543",
        },
        "tickets": {
            "general": 10,
            "students": 5,
            "children": 0,
        },
    }


@app.get("/api/artifacts", response_model=List[PublicArtifact])
def list_artifacts(q: Optional[str] = None, featured: Optional[bool] = None, limit: int = 50):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filter_query = {}
    if q:
        filter_query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}},
        ]
    if featured is not None:
        filter_query["featured"] = bool(featured)
    docs = get_documents("artifact", filter_query, limit)
    results: List[PublicArtifact] = []
    for d in docs:
        results.append(
            PublicArtifact(
                id=str(d.get("_id")),
                title=d.get("title"),
                description=d.get("description"),
                image_url=d.get("image_url"),
                period=d.get("period"),
                collection=d.get("collection"),
                tags=d.get("tags"),
            )
        )
    return results


@app.get("/api/artifacts/{artifact_id}", response_model=PublicArtifact)
def get_artifact(artifact_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        oid = ObjectId(artifact_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid artifact id")
    doc = db["artifact"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return PublicArtifact(
        id=str(doc["_id"]),
        title=doc.get("title"),
        description=doc.get("description"),
        image_url=doc.get("image_url"),
        period=doc.get("period"),
        collection=doc.get("collection"),
        tags=doc.get("tags"),
    )


def hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@app.post("/api/auth/signup")
def signup(payload: SignupRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    existing = db["useraccount"].find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    ua = UserAccount(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    new_id = create_document("useraccount", ua)
    return {"id": new_id, "name": ua.name, "email": ua.email}


@app.post("/api/auth/signin")
def signin(payload: SigninRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    user = db["useraccount"].find_one({"email": payload.email})
    if not user or user.get("password_hash") != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"id": str(user.get("_id")), "name": user.get("name"), "email": user.get("email")}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
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

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
