import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, List, Optional, Dict, Any
from datetime import datetime

from mcp.server.fastmcp import FastMCP, Context
# Instead of importing Error from mcp.server.fastmcp.tools, we'll define our own Error class
# or we can use standard exceptions for now

from .api import StackExchangeAPI
from .types import (
    SearchByQueryInput,
    SearchByErrorInput,
    GetQuestionInput,
    AdvancedSearchInput,
    SearchResult
)

from .formatter import format_response
from .env import STACK_EXCHANGE_API_KEY

@dataclass
class AppContext:
    api: StackExchangeAPI

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with the Stack Exchange API client.

    Args:
        server (FastMCP): The FastMCP server instance

    Returns:
        AsyncIterator[AppContext]: Context containing the API client
    """
    
    api = StackExchangeAPI(
        api_key=STACK_EXCHANGE_API_KEY,
    )
    try:
        yield AppContext(api=api)
    finally:
        await api.close()
        
mcp = FastMCP(
    "Stack Overflow MCP",
    lifespan=app_lifespan,
    dependencies=["httpx", "python-dotenv"]
)

@mcp.tool()
async def advanced_search(
    query: Optional[str] = None,
    tags: Optional[List[str]] = None,
    excluded_tags: Optional[List[str]] = None,
    min_score: Optional[int] = None,
    title: Optional[str] = None,
    body: Optional[str] = None,
    answers: Optional[int] = None,
    has_accepted_answer: Optional[bool] = None,
    views: Optional[int] = None,
    url: Optional[str] = None,
    user_id: Optional[int] = None,
    is_closed: Optional[bool] = None,
    is_wiki: Optional[bool] = None,
    is_migrated: Optional[bool] = None,
    has_notice: Optional[bool] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    sort_by: Optional[str] = "votes",
    include_comments: Optional[bool] = False,
    response_format: Optional[str] = "markdown",
    limit: Optional[int] = 5,
    ctx: Context = None
) -> str:
    """Advanced search for Stack Overflow questions with many filter options.
    
    Args:
        query (Optional[str]): Free-form search query
        tags (Optional[List[str]]): List of tags to filter by
        excluded_tags (Optional[List[str]]): List of tags to exclude
        min_score (Optional[int]): Minimum score threshold
        title (Optional[str]): Text that must appear in the title
        body (Optional[str]): Text that must appear in the body
        answers (Optional[int]): Minimum number of answers
        has_accepted_answer (Optional[bool]): Whether questions must have an accepted answer
        views (Optional[int]): Minimum number of views
        url (Optional[str]): URL that must be contained in the post
        user_id (Optional[int]): ID of the user who must own the questions
        is_closed (Optional[bool]): Whether to return only closed or open questions
        is_wiki (Optional[bool]): Whether to return only community wiki questions
        is_migrated (Optional[bool]): Whether to return only migrated questions
        has_notice (Optional[bool]): Whether to return only questions with post notices
        from_date (Optional[datetime]): Earliest creation date
        to_date (Optional[datetime]): Latest creation date
        sort_by (Optional[str]): Field to sort by (activity, creation, votes, relevance)
        include_comments (Optional[bool]): Whether to include comments in results
        response_format (Optional[str]): Format of response ("json" or "markdown")
        limit (Optional[int]): Maximum number of results to return
        ctx (Context): The context is passed automatically by the MCP
        
    Returns:
        str: Formatted search results
    """
    try:
        api = ctx.request_context.lifespan_context.api
        
        ctx.debug(f"Performing advanced search on Stack Overflow")
        if query:
            ctx.debug(f"Query: {query}")
        if body:
            ctx.debug(f"Body: {body}")
        if tags:
            ctx.debug(f"Tags: {', '.join(tags)}")
        if excluded_tags:
            ctx.debug(f"Excluded tags: {', '.join(excluded_tags)}")
        
        results = await api.advanced_search(
            query=query,
            tags=tags,
            excluded_tags=excluded_tags,
            min_score=min_score,
            title=title,
            body=body,
            answers=answers,
            has_accepted_answer=has_accepted_answer,
            views=views,
            url=url,
            user_id=user_id,
            is_closed=is_closed,
            is_wiki=is_wiki,
            is_migrated=is_migrated,
            has_notice=has_notice,
            from_date=from_date,
            to_date=to_date,
            sort_by=sort_by,
            limit=limit,
            include_comments=include_comments
        )
        
        ctx.debug(f"Found {len(results)} results")
        
        return format_response(results, response_format)
    
    except Exception as e:
        ctx.error(f"Error performing advanced search on Stack Overflow: {str(e)}")
        raise RuntimeError(f"Failed to search Stack Overflow: {str(e)}")

@mcp.tool()
async def search_by_query(
    query: str,
    tags: Optional[List[str]] = None,
    excluded_tags: Optional[List[str]] = None,
    min_score: Optional[int] = None,
    title: Optional[str] = None,
    body: Optional[str] = None,
    has_accepted_answer: Optional[bool] = None,
    answers: Optional[int] = None,
    sort_by: Optional[str] = "votes",
    include_comments: Optional[bool] = False,
    response_format: Optional[str] = "markdown",
    limit: Optional[int] = 5,
    ctx: Context = None 
) -> str:
    """Search Stack Overflow for questions matching a query.

    Args:
        query (str): The search query
        tags (Optional[List[str]]): Optional list of tags to filter by (e.g., ["python", "pandas"])
        excluded_tags (Optional[List[str]]): Optional list of tags to exclude
        min_score (Optional[int]): Minimum score threshold for questions
        title (Optional[str]): Text that must appear in the title
        body (Optional[str]): Text that must appear in the body
        has_accepted_answer (Optional[bool]): Whether questions must have an accepted answer
        answers (Optional[int]): Minimum number of answers
        sort_by (Optional[str]): Field to sort by (activity, creation, votes, relevance)
        include_comments (Optional[bool]): Whether to include comments in results
        response_format (Optional[str]): Format of response ("json" or "markdown")
        limit (Optional[int]): Maximum number of results to return
        ctx (Context): The context is passed automatically by the MCP

    Returns:
        str: Formatted search results
    """
    try:
        api = ctx.request_context.lifespan_context.api
        
        ctx.debug(f"Searching Stack Overflow for: {query}")
        
        if tags: 
            ctx.debug(f"Filtering by tags: {', '.join(tags)}")
        if excluded_tags:
            ctx.debug(f"Excluding tags: {', '.join(excluded_tags)}")
        
        results = await api.search_by_query(
            query=query,
            tags=tags,
            excluded_tags=excluded_tags,
            min_score=min_score,
            title=title,
            body=body,
            has_accepted_answer=has_accepted_answer,
            answers=answers,
            sort_by=sort_by,
            limit=limit,
            include_comments=include_comments
        )
        
        ctx.debug(f"Found {len(results)} results")
        
        return format_response(results, response_format)
    
    except Exception as e:
        ctx.error(f"Error searching Stack Overflow: {str(e)}")
        raise RuntimeError(f"Failed to search Stack Overflow: {str(e)}")


@mcp.tool()
async def search_by_error(
    error_message: str,
    language: Optional[str] = None,
    technologies: Optional[List[str]] = None,
    excluded_tags: Optional[List[str]] = None,
    min_score: Optional[int] = None,
    has_accepted_answer: Optional[bool] = None,
    answers: Optional[int] = None,
    include_comments: Optional[bool] = False,
    response_format: Optional[str] = "markdown",
    limit: Optional[int] = 5,
    ctx: Context = None
) -> str:
    """Search Stack Overflow for solutions to an error message

    Args:
        error_message (str): The error message to search for
        language (Optional[str]): Programming language (e.g., "python", "javascript")
        technologies (Optional[List[str]]): Related technologies (e.g., ["react", "django"])
        excluded_tags (Optional[List[str]]): Optional list of tags to exclude
        min_score (Optional[int]): Minimum score threshold for questions
        has_accepted_answer (Optional[bool]): Whether questions must have an accepted answer
        answers (Optional[int]): Minimum number of answers
        include_comments (Optional[bool]): Whether to include comments in results
        response_format (Optional[str]): Format of response ("json" or "markdown")
        limit (Optional[int]): Maximum number of results to return
        ctx (Context): The context is passed automatically by the MCP

    Returns:
        str: Formatted search results
    """
    try:
        api = ctx.request_context.lifespan_context.api
        
        tags = []
        if language:
            tags.append(language.lower())
        if technologies:
            tags.extend([t.lower() for t in technologies])
            
        ctx.debug(f"Searching Stack Overflow for error: {error_message}")
        
        if tags:
            ctx.debug(f"Using tags: {', '.join(tags)}")
        if excluded_tags:
            ctx.debug(f"Excluding tags: {', '.join(excluded_tags)}")
        
        results = await api.search_by_query(
            query=error_message,
            tags=tags if tags else None,
            excluded_tags=excluded_tags,
            min_score=min_score,
            has_accepted_answer=has_accepted_answer,
            answers=answers,
            limit=limit,
            include_comments=include_comments
        )
        ctx.debug(f"Found {len(results)} results")
        
        return format_response(results, response_format)
    except Exception as e: 
        ctx.error(f"Error searching Stack Overflow: {str(e)}")
        raise RuntimeError(f"Failed to search Stack Overflow: {str(e)}")
    
@mcp.tool()
async def get_question(
    question_id: int,
    include_comments: Optional[bool] = True,
    response_format: Optional[str] = "markdown",
    ctx: Context = None
) -> str:
    """Get a specific Stack Overflow question by ID.

    Args:
        question_id (int): The Stack Overflow question ID
        include_comments (Optional[bool]): Whether to include comments in results
        response_format (Optional[str]): Format of response ("json" or "markdown")
        ctx (Context): The context is passed automatically by the MCP

    Returns:
        str: Formatted question details
    """
    try:
        api = ctx.request_context.lifespan_context.api 
        
        ctx.debug(f"Fetching Stack Overflow question: {question_id}")
        
        result = await api.get_question(
            question_id=question_id,
            include_comments=include_comments
        )
        
        return format_response([result], response_format)
    
    except Exception as e:
        ctx.error(f"Error fetching Stack Overflow question: {str(e)}")
        raise RuntimeError(f"Failed to fetch Stack Overflow question: {str(e)}")

@mcp.tool()
async def analyze_stack_trace(
    stack_trace: str,
    language: str,
    excluded_tags: Optional[List[str]] = None,
    min_score: Optional[int] = None,
    has_accepted_answer: Optional[bool] = None,
    answers: Optional[int] = None,
    include_comments: Optional[bool] = True,
    response_format: Optional[str] = "markdown",
    limit: Optional[int] = 3,
    ctx: Context = None
) -> str:
    """Analyze a stack trace and find relevant solutions on Stack Overflow.
    
    Args:
        stack_trace (str): The stack trace to analyze
        language (str): Programming language of the stack trace
        excluded_tags (Optional[List[str]]): Optional list of tags to exclude
        min_score (Optional[int]): Minimum score threshold for questions
        has_accepted_answer (Optional[bool]): Whether questions must have an accepted answer
        answers (Optional[int]): Minimum number of answers
        include_comments (Optional[bool]): Whether to include comments in results
        response_format (Optional[str]): Format of response ("json" or "markdown")
        limit (Optional[int]): Maximum number of results to return
        ctx (Context): The context is passed automatically by the MCP
        
    Returns:
        str: Formatted search results
    """
    try:
        api = ctx.request_context.lifespan_context.api
        
        error_lines = stack_trace.split("\n")
        error_message = error_lines[0]
        
        ctx.debug(f"Analyzing stack trace: {error_message}")
        ctx.debug(f"Language: {language}")
        
        results = await api.search_by_query(
            query=error_message,
            tags=[language.lower()],
            excluded_tags=excluded_tags,
            min_score=min_score,
            has_accepted_answer=has_accepted_answer,
            answers=answers,
            limit=limit,
            include_comments=include_comments
        )
        
        ctx.debug(f"Found {len(results)} results")
        
        return format_response(results, response_format)
    except Exception as e:
        ctx.error(f"Error analyzing stack trace: {str(e)}")
        raise RuntimeError(f"Failed to analyze stack trace: {str(e)}")

if __name__ == "__main__":
    mcp.run()