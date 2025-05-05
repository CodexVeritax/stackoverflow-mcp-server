import os
import pytest
import asyncio
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from dotenv import load_dotenv

from stackoverflow_mcp.api import StackExchangeAPI
from stackoverflow_mcp.types import SearchResult

# Load test environment variables
load_dotenv(".env.test")


@pytest.fixture
def api_key():
    """Return API key from environment or None."""
    return os.getenv("STACK_EXCHANGE_API_KEY")


@pytest.fixture
def api(api_key):
    """Create a StackExchangeAPI instance for testing."""
    api = StackExchangeAPI(api_key=api_key)
    yield api
    # Clean up
    asyncio.run(api.close())


@pytest.fixture
def mock_search_response():
    """Create a mock search response."""
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json = MagicMock(return_value={
        "items": [
            {
                "question_id": 12345,
                "title": "How to unittest a Flask application?",
                "body": "<p>I'm trying to test my Flask application with unittest.</p>",
                "score": 25,
                "answer_count": 3,
                "is_answered": True,
                "accepted_answer_id": 54321,
                "creation_date": 1609459200,
                "last_activity_date": 1609459200,
                "view_count": 1000,
                "tags": ["python", "flask", "testing", "unittest"],
                "link": "https://stackoverflow.com/q/12345",
                "closed_date": None,
                "owner": {
                    "user_id": 101,
                    "display_name": "Test User",
                    "reputation": 1000
                }
            }
        ],
        "has_more": False,
        "quota_max": 300,
        "quota_remaining": 299
    })
    return response


# REAL API TESTS

@pytest.mark.asyncio
@pytest.mark.real_api
async def test_search_by_query_real(api):
    """Test searching by query using real API."""
    # Skip if no API key
    if not os.getenv("STACK_EXCHANGE_API_KEY"):
        pytest.skip("API key required for real API tests")
    
    results = await api.search_by_query(
        query="python unittest flask",
        tags=["python", "flask"],
        limit=3
    )
    
    # Basic validation
    assert isinstance(results, list)
    if results:  # May be empty if no results match
        assert isinstance(results[0], SearchResult)
        assert results[0].question.title is not None
        assert "python" in [tag.lower() for tag in results[0].question.tags]


@pytest.mark.asyncio
@pytest.mark.real_api
async def test_advanced_search_real(api):
    """Test advanced search using real API."""
    # Skip if no API key
    if not os.getenv("STACK_EXCHANGE_API_KEY"):
        pytest.skip("API key required for real API tests")
    
    results = await api.advanced_search(
        query="database connection",
        tags=["python"],
        min_score=10,
        has_accepted_answer=True,
        limit=2
    )
    
    # Basic validation
    assert isinstance(results, list)
    if results:  # May be empty if no results match
        assert isinstance(results[0], SearchResult)
        assert results[0].question.score >= 10
        assert "python" in [tag.lower() for tag in results[0].question.tags]


# MOCK TESTS

@pytest.mark.asyncio
async def test_search_by_query_mock(api, mock_search_response):
    """Test searching by query with mocked response."""
    with patch.object(httpx.AsyncClient, 'get', return_value=mock_search_response):
        results = await api.search_by_query(
            query="flask unittest",
            tags=["python", "flask"],
            min_score=10,
            limit=5
        )
        
        assert len(results) == 1
        assert results[0].question.question_id == 12345
        assert results[0].question.title == "How to unittest a Flask application?"
        assert "python" in results[0].question.tags
        assert "flask" in results[0].question.tags


@pytest.mark.asyncio
async def test_empty_search_results(api):
    """Test empty search results handling."""
    empty_response = MagicMock()
    empty_response.raise_for_status = MagicMock()
    empty_response.json = MagicMock(return_value={"items": []})
    
    with patch.object(httpx.AsyncClient, 'get', return_value=empty_response):
        results = await api.search_by_query(
            query="definitely will not find anything 89797979",
            limit=1
        )
        
        assert isinstance(results, list)
        assert len(results) == 0


@pytest.mark.asyncio
async def test_search_with_min_score_filtering(api, mock_search_response):
    """Test that min_score parameter properly filters results."""
    with patch.object(httpx.AsyncClient, 'get', return_value=mock_search_response):
        # Should return results (mock score is 25)
        results_included = await api.search_by_query(
            query="flask unittest",
            min_score=20,
            limit=5
        )
        assert len(results_included) == 1
        
        # Should filter out results
        results_filtered = await api.search_by_query(
            query="flask unittest",
            min_score=30,
            limit=5
        )
        assert len(results_filtered) == 0


@pytest.mark.asyncio
async def test_search_with_multiple_tags(api, mock_search_response):
    """Test searching with multiple tags."""
    with patch.object(httpx.AsyncClient, 'get', return_value=mock_search_response):
        results = await api.search_by_query(
            query="test",
            tags=["python", "flask", "django"],
            limit=5
        )
        
        # Verify the tags were properly passed to the request
        call_args = httpx.AsyncClient.get.call_args
        params = call_args[1]['params']
        assert 'tagged' in params
        assert params['tagged'] == "python;flask;django"


@pytest.mark.asyncio
async def test_search_with_excluded_tags(api, mock_search_response):
    """Test searching with excluded tags."""
    with patch.object(httpx.AsyncClient, 'get', return_value=mock_search_response):
        results = await api.search_by_query(
            query="test",
            excluded_tags=["javascript", "c#"],
            limit=5
        )
        
        # Verify the excluded tags were properly passed to the request
        call_args = httpx.AsyncClient.get.call_args
        params = call_args[1]['params']
        assert 'nottagged' in params
        assert params['nottagged'] == "javascript;c#"


@pytest.mark.asyncio
async def test_search_with_advanced_parameters(api, mock_search_response):
    """Test advanced search with multiple parameters."""
    with patch.object(httpx.AsyncClient, 'get', return_value=mock_search_response):
        results = await api.advanced_search(
            query="flask test",
            tags=["python"],
            title="unittest",
            has_accepted_answer=True,
            sort_by="relevance",
            limit=5
        )
        
        # Verify parameters were properly passed
        call_args = httpx.AsyncClient.get.call_args
        params = call_args[1]['params']
        assert params['q'] == "flask test"
        assert params['tagged'] == "python"
        assert params['title'] == "unittest"
        assert params['accepted'] == "true"
        assert params['sort'] == "relevance"
        assert params['pagesize'] == "5"


@pytest.mark.asyncio
async def test_search_api_error(api):
    """Test handling of API errors."""
    error_response = MagicMock()
    error_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=MagicMock(status_code=500)
        )
    )
    
    with patch.object(httpx.AsyncClient, 'get', return_value=error_response):
        with pytest.raises(httpx.HTTPStatusError):
            await api.search_by_query("test query")