"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

# Portfolio-specific schemas

class Settings(BaseModel):
    """
    Site-wide settings and profile information
    Collection name: "settings"
    Only one document typically used
    """
    name: str = Field(..., description="Your full name")
    role: str = Field(..., description="Primary role or title, e.g., 'Full-Stack Developer'")
    headline: str = Field(..., description="Short headline for the hero section")
    about: str = Field(..., description="About you / bio section")
    location: Optional[str] = Field(None, description="City, Country")
    avatar_url: Optional[HttpUrl] = Field(None, description="Profile image URL")
    email: Optional[str] = Field(None, description="Public contact email")
    socials: Optional[dict] = Field(default_factory=dict, description="Map of social handles and URLs")

class Project(BaseModel):
    """
    Projects collection schema
    Collection name: "project"
    """
    title: str = Field(..., description="Project title")
    description: str = Field(..., description="Short description of the project")
    tags: List[str] = Field(default_factory=list, description="Tech tags")
    image_url: Optional[HttpUrl] = Field(None, description="Screenshot or cover image")
    live_url: Optional[HttpUrl] = Field(None, description="Live demo URL")
    repo_url: Optional[HttpUrl] = Field(None, description="Source repository URL")

# Example schemas left from template (kept for reference)
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
