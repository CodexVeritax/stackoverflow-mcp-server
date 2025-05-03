import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock 

from stackoverflow_mcp.server import mcp, search_by_query, search_by_error, get_question, analyze_stack_trace
from stackoverflow_mcp.types import StackOverflowQuestion, StackOverflowAnswer, SearchResult
from mcp.server.fastmcp import Context

@pytest.fixture
def mock_context():
    """Create a mock context for testing"""
    context = MagicMock(spec=Context)
    
    context.debug = MagicMock()
    context.info = MagicMock()
    context.error = MagicMock()
    context.request_context.lifespan_context.api = AsyncMock()
   
    
    return context

@pytest.fixture
def mock_search_result():
    """Create a mock search result for testing"""
    question = StackOverflowQuestion(
        question_id=12345,
        title="Test Question",
        body="Test body",
        score=10,
        answer_count=2,
        is_answered=True,
        accepted_answer_id=54321,
        creation_date=1609459200,
        tags=["python", "testing"],
        link="https://stackoverflow.com/q/12345"
    )
    
    answer = StackOverflowAnswer(
        answer_id=54321,
        question_id=12345,
        score=5,
        is_accepted=True,
        body="Test answer",
        creation_date=1609459300,
        link="https://stackoverflow.com/a/54321"
    )
    
    return SearchResult(
        question=question,
        answers=[answer],
        comments=None
    )

@pytest.mark.asyncio
async def test_search_by_query(mock_context, mock_search_result):
    """Test search by query function"""
    mock_context.request_context.lifespan_context.api.search_by_query.return_value = [mock_search_result]
    
    
    result = await search_by_query(
        query="test query",
        tags=["python"],
        min_score=5,
        include_comments=False,
        response_format="markdown",
        limit=5,
        ctx=mock_context
    )
    
    mock_context.request_context.lifespan_context.api.search_by_query.assert_called_once_with(
        query="test query",
        tags=["python"],
        min_score=5,
        limit=5,
        include_comments=False
    )
    
    assert "Test Question" in result

@pytest.mark.asyncio
async def test_search_by_error(mock_context, mock_search_result):
    """Test search by error function"""
    mock_context.request_context.lifespan_context.api.search_by_query.return_value = [mock_search_result]
    
    result = await search_by_error(
        error_message="test error",
        language="python",
        technologies=["django"],
        min_score=5,
        include_comments=False,
        response_format="markdown",
        limit=5,
        ctx=mock_context
    )
    
    mock_context.request_context.lifespan_context.api.search_by_query.assert_called_once_with(
        query="test error",
        tags=["python", "django"],
        min_score=5,
        limit=5,
        include_comments=False
    )
    
    assert "Test Question" in result

@pytest.mark.asyncio
async def test_get_question(mock_context, mock_search_result):
    """Test get question function"""
    mock_context.request_context.lifespan_context.api.get_question.return_value = mock_search_result
    
    result = await get_question(
        question_id=12345,
        include_comments=True,
        response_format="markdown",
        ctx=mock_context
    )
    
    mock_context.request_context.lifespan_context.api.get_question.assert_called_once_with(
        question_id=12345,
        include_comments=True
    )
    
    assert "Test Question" in result

@pytest.mark.asyncio
async def test_analyze_stack_trace(mock_context, mock_search_result):
    """Test analyze stack trace function"""
    mock_context.request_context.lifespan_context.api.search_by_query.return_value = [mock_search_result]
    
    result = await analyze_stack_trace(
        stack_trace="Error: Something went wrong\n  at Function.Module._resolveFilename",
        language="javascript",
        include_comments=True,
        response_format="markdown",
        limit=3,
        ctx=mock_context
    )
    
    mock_context.request_context.lifespan_context.api.search_by_query.assert_called_once_with(
        query="Error: Something went wrong",
        tags=["javascript"],
        min_score=0,
        limit=3,
        include_comments=True
    )
    
    assert "Test Question" in result