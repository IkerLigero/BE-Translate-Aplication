import pytest
from unittest.mock import patch, AsyncMock
from app.models.translation import Translation

# Prefix for all translation endpoint tests
BASE_URL = "/api/v1/translations"


# Test for the GET /translations endpoint when there are no translations for the user
@pytest.mark.asyncio
async def test_get_translations_empty(client, auth_override, db_session):
    """Test: Get list when the user has no translations."""
    response = await client.get(f"{BASE_URL}")
    assert response.status_code == 200
    assert response.json() == []


# Test for the GET /translations endpoint when there are translations for the user.
# Ensure communication with the database is working and that the endpoint returns the expected data.
@pytest.mark.asyncio
async def test_get_translations_with_data(client, auth_override, db_session, mock_user):
    """Test: Get list with manually inserted data."""
    new_trans = Translation(
        user_id=mock_user.id,
        original_text="Hello world",
        source_lang="en",
        target_language="es",
        pdf_lang="es",
        status="pending",
        is_active=True
    )
    db_session.add(new_trans)
    # Flush sends the object to the DB so the GET can see it, but the subsequent rollback will remove it
    await db_session.flush()

    response = await client.get(f"{BASE_URL}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Look for our translation in the list in case there are leftovers from other tests
    assert any(t["original_text"] == "Hello world" for t in data)


# Test for the GET /search endpoint with an empty query
@pytest.mark.asyncio
async def test_search_history_validation(client, auth_override):
    """Test: Validate that an empty search returns 400."""
    response = await client.get(f"{BASE_URL}/search?q= ")
    assert response.status_code == 400
    assert response.json()["detail"] == "Search query cannot be empty"


# Test for the GET /search endpoint with a valid query but no results
@pytest.mark.asyncio
async def test_search_history_success(client, auth_override):
    """Test: Semantic search using Mocks to avoid OpenAI calls."""
    mock_results = [
        {
            "id": 1, 
            "user_id": 1,
            "original_text": "Hello", 
            "translated_text": "Hola",
            "source_lang": "en",
            "pdf_lang": "es",
            "target_language": "es",
            "status": "completed",
            "created_at": "2026-05-07T11:00:00",
            "file_path": None 
        }
    ]
    
    with patch("app.api.endpoints.translations.search_similar_translations", 
               new_callable=AsyncMock) as mock_search:
        
        mock_search.return_value = mock_results
        
        response = await client.get(f"{BASE_URL}/search?q=hola")
        
        assert response.status_code == 200
        # Now the comparison will be identical
        assert response.json() == mock_results
        
        mock_search.assert_called_once()
        _, kwargs = mock_search.call_args
        assert kwargs["user_id"] == 1