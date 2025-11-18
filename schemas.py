"""
Database Schemas for NEUST Museum

Each Pydantic model corresponds to a MongoDB collection. The collection name
is the lowercase of the class name (e.g., Artifact -> "artifact").
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


class Artifact(BaseModel):
    """
    Museum artifacts and collections
    Collection name: "artifact"
    """
    title: str = Field(..., description="Artifact title")
    description: Optional[str] = Field(None, description="Detailed description")
    image_url: Optional[str] = Field(None, description="Public image URL")
    period: Optional[str] = Field(None, description="Historical period or year")
    collection: Optional[str] = Field(None, description="Collection name")
    tags: Optional[List[str]] = Field(default=None, description="Search tags")
    featured: bool = Field(default=False, description="Whether to show on homepage")


class UserAccount(BaseModel):
    """
    Registered users for sign-in/up
    Collection name: "useraccount"
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Unique email address")
    password_hash: str = Field(..., description="Password hash (SHA256 for demo)")
    role: str = Field(default="user", description="Role: user/admin")
    is_active: bool = Field(default=True)
