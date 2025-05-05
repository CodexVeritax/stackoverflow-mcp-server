import time
import pytest
import asyncio
import httpx
from unittest.mock import patch, MagicMock
from stackoverflow_mcp.api import StackExchangeAPI
from stackoverflow_mcp.types import StackOverflowQuestion, StackOverflowAnswer, SearchResult


@pytest.fixture
def api():
    """Create A StackExchangeAPI instance for testing
    """
    return StackExchangeAPI(api_key="test_key")

@pytest.fixture
def mock_response():
    """Create a mock response for httpx."""
    
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json = MagicMock(return_value={
        "items" : [
                        {
                "question_id": 12345,
                "title": "Test Question",
                "body": "Test body",
                "score": 10,
                "answer_count": 2,
                "is_answered": True,
                "accepted_answer_id": 54321,
                "creation_date": 1609459200,
                "tags": ["python", "testing"],
                "link": "https://stackoverflow.com/q/12345"
            }
        ]
    })
    return response

@pytest.mark.asyncio
async def test_search_by_query(api, mock_response):
    """Test searching by query."""
    with patch.object(httpx.AsyncClient, 'get', return_value=mock_response):
        results = await api.search_by_query("test query")
        
        assert len(results) == 1
        assert results[0].question.question_id == 12345
        assert results[0].question.title == "Test Question"
        assert isinstance(results[0], SearchResult)

@pytest.mark.asyncio
async def test_get_question(api, mock_response):
    """Test getting a specific question."""
    with patch.object(httpx.AsyncClient, 'get', return_value=mock_response):
        result = await api.get_question(12345)
        
        assert result.question.question_id == 12345
        assert result.question.title == "Test Question"
        assert isinstance(result, SearchResult)

@pytest.mark.asyncio
async def test_rate_limiting(api):
    """Test rate limiting mechanism."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value={"items": []})
    
    with patch.object(httpx.AsyncClient, 'get', return_value=mock_resp):
        api.request_timestamps = [time.time() * 1000  * 1000 for _ in range(30)]
                
        with patch('asyncio.sleep') as mock_sleep:
            try:
                await api.search_by_query("test")
            except Exception as e:
                assert str(e) == "Maximum rate limiting attempts exceeded"
            mock_sleep.assert_called()

@pytest.mark.asyncio
async def test_retry_after_429(api):
    """Test retry behavior after hitting rate limit."""
    error_resp = MagicMock()
    error_resp.raise_for_status.side_effect = httpx.HTTPStatusError("Rate limited", request=MagicMock(), response=MagicMock(status_code=429))
    
    success_resp = MagicMock()
    success_resp.raise_for_status = MagicMock()
    success_resp.json = MagicMock(return_value={"items": []})
    
    with patch.object(httpx.AsyncClient, 'get', side_effect=[error_resp, success_resp]):
        with patch('asyncio.sleep') as mock_sleep:
            await api.search_by_query("test", retries=1)
            mock_sleep.assert_called_once()