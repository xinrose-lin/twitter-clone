import uuid
import pytest
from pydantic import ValidationError

from app.validation import CreatePostRequest
from app.validation import FollowRequest

def test_rejects_empty_content():
    with pytest.raises(ValidationError):
        CreatePostRequest(
            author_id=uuid.uuid4(),
            content=""
        )

def test_rejects_self_follow(): 
    same_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        FollowRequest(
            follower_id=same_id,
            followee_id=same_id
        )   
        