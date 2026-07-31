from uuid import UUID
from typing import Optional 
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

class CreatePostRequest(BaseModel):
    author_id: UUID
    content: str = Field(..., min_length=1, max_length=500)

class FollowRequest(BaseModel): 
    follower_id: UUID
    following_id: UUID

    # logic across multiple fields; after they are parsed
    @model_validator(mode="after")
    def no_self_follow(self): 
        if self.follower_id == self.following_id: 
            raise ValueError("Cannot follow yourself")
        return self
