import pytest
from pydantic import ValidationError
from app.schemas.translation import DuplicateRequest

# This field contains tests for the Pydantic schemas used in the application,
# ensuring that they validate data correctly and enforce the expected constraints.


# We test that the DuplicateRequest schema correctly validates a valid input and raises an error for invalid input.
def test_duplicate_request_valid():
    """Test that a valid duplicate request passes validation"""
    data = {"new_target_lang": "fr"}
    request = DuplicateRequest(**data)
    # assert: we check that the new_target_lang field is set correctly in the request object.
    assert request.new_target_lang == "fr"

# We pass invalid data (empty string) to the DuplicateRequest schema and check that it raises a ValidationError
def test_duplicate_request_invalid():
    """Test that an empty or missing language fails validation"""
    # Raises: the test must raise a ValidationError or the test will fail if it doesn't.
    with pytest.raises(ValidationError):
        # This should raise a ValidationError because the new_target_lang is empty, which is not allowed by the schema.
        DuplicateRequest(new_target_lang="")