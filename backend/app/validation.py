from uuid import UUID
from pydantic import BaseModel, Field

class CreatePostRequest(BaseModel):
    author_id: UUID
    content: str = Field(..., min_length=1, max_length=500)

    