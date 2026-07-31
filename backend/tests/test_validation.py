import uuid
import pytest
from pydantic import ValidationError

from app.validation import CreatePostRequest

def test_rejects_empty_content():
    with pytest.raises(ValidationError):
        CreatePostRequest(
            author_id=uuid.uuid4(),
            content=""
        )

def 