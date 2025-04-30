import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator , List , Optional, Dict , Any

from mcp.server.fastmcp import FastMCP , Context
from mcp.server.fastmcp.tools import Error

from .api import StackExchangeAPI
from .types import (
    SearchByQueryInput,
    SearchByErrorInput,
    GetQuestionInput,
    SearchResult
)

from .formatter import format_response
from .env import STACK_EXCHANGE_API_KEY , STACK_EXCHANGE_ACCESS_TOKEN

@dataclass
class AppContext:
    api:StackExchangeAPI

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with the Slack Exchange API client.

    Args:
        server (FastMCP): _description_

    Returns:
        AsyncIterator[AppContext]: _description_
    """
    
    api = StackExchangeAPI(
        api_key=STACK_EXCHANGE_API_KEY,
        access_token=STACK_EXCHANGE_ACCESS_TOKEN
    )
    try:
        yield AppContext(api=api)
    finally:
        await api.close()
        
mcp = FastMCP(
    "Stack Overflow MCP",
    lifespan=app_lifespan,
    dependencies=["httpx" , "python-dotenv"]
)

@mcp.tool()
async def search_by_query(
    query: str,
    tags: Optional[List[str]] = None,
    min_score: Optional[int] = None,
    include_comments: Optional[bool] = False,
    response_format : Optional[str] = "markdown",
    limit: Optional[int] = 5,
    ctx: Context = None 
) -> str:
    """Search Stack Overflow for questions matching a query.

    Args:
        query (str): The search query
        tags (Optional[List[str]], optional): Optional list of tags to filter by (e.g., ["python", "pandas"]). Defaults to None.
        min_score (Optional[int], optional): Minimum score threshold for questions. Defaults to None.
        include_comments (Optional[bool], optional): Whether to include comments in results. Defaults to False.
        response_format (Optional[str], optional): Format of response ("json" or "markdown"). Defaults to "markdown".
        limit (Optional[int], optional): Maximum number of results to return. Defaults to 5.
        ctx (Context, optional): The context is passed automatically by the MCP. Defaults to None.

    Returns:
        str: _description_
    """
    try:
        api = ctx.request_context.lifespan_context.api
        
        ctx.debug(f"Searching Stack Overflow for: {query}")
        
        if tags: 
            ctx.debug(f"Filtering by tags: {', '.join(tags)}")
        
        results = await api.search_by_query(
            query=query,
            tags=tags,
            min_score=min_score,
            limit=limit,
            include_comments=include_comments
        )
        
        ctx.debug(f"Found {len(results)} results")
        
        return format_response(results, response_format)
    
    except Exception as e:
        ctx.error(f"Error searching Stack Overflow: {str(e)}")
        raise Error(f"Failed to search Stack Overflow: {str(e)}")
    

@mcp.tool()
async def search_by_error(
    error_message: str,
    language: Optional[str] = None,
    technologies: Optional[List[str]] = None,
    min_score: Optional[int] = None,
    include_comments: Optional[bool] = False,
    response_format: Optional[str] = "markdown",
    limit: Optional[int] = 5,
    ctx: Context = None
) -> str:
    """Search Stack Overflow for solutions to an error message

    Args:
        error_message (str): The error message to search for
        language (Optional[str], optional): Programming language (e.g., "python", "javascript")
 . Defaults to None.
        technologies (Optional[List[str]], optional): Related technologies (e.g., ["react", "django"]). Defaults to None.
        min_score (Optional[int], optional): Minimum score threshold for questions. Defaults to None.
        include_comments (Optional[bool], optional): Whether to include comments in results. Defaults to False.
        response_format (Optional[str], optional): Format of response ("json" or "markdown")
 . Defaults to "markdown".
        limit (Optional[int], optional): Maximum number of results to return. Defaults to 5.
        ctx (Context, optional): _description_. Defaults to None.

    Returns:
        str: _description_
    """
    
    try:
        
        api = ctx.request_context.lifespan_context.api
        
        tags= []
        if language:
            tags.append(language.lower())
        if technologies:
            tags.extend([t.lower() for t in technologies])
            
        ctx.debug(f"Searching Stack Overflow for error: {error_message}")
        
        if tags:
            ctx.debug(f"Using tags: {', '.join(tags)}")
        
        results = await api.search_by_query(
            query=error_message,
            tags=tags if tags else None,
            min_score=min_score,
            limit=limit,
            include_comments=include_comments
        )
        ctx.debug(f"Found {len(results)} results")
        
        return format_response(results , response_format)
    except Exception as e : 
        ctx.error(f"Error searching Stack Overflow: {str(e)}")
        raise Error(f"Failed to search Stack Overflow: {str(e)}")
    
@mcp.tool()
async def get_question(
    question_id: int,
    include_comments: Optional[bool] = True,
    respose_format: Optional[str] = "markdown",
    ctx: Context = None
) -> str:
    """Get a specific Stack Overflow question by ID.

    Args:
        question_id (int): The Stack Overflow question ID
        include_comments (Optional[bool], optional): Whether to include comments in results. Defaults to True.
        respose_format (Optional[str], optional): Format of response ("json" or "markdown"). Defaults to "markdown".
        ctx (Context, optional): _description_. Defaults to None.

    Returns:
        str: _description_
    """
    
    try:
        
        api = ctx.request_context.lifespan_context.api 
        
        ctx.debug(f"Fetching Stack Overflow question: {question_id}")
        
        result = await api.get_question(
            question_id=question_id,
            include_comments=include_comments
        )
        
        return format_response([result] , respose_format)
    
    except Exception as e :
        ctx.error(f"Error fetching Stack Overflow qquestion: {str(e)}")
        raise Error(f"Failed to fetch Stack Overflow question: {str(e)}")

@mcp.tool()
async def analyze_stack_trace(
    stack_trace: str,
    language: str,
    include_comments: Optional[bool] = True,
    response_format: Optional[str] = "markdown",
    limit: Optional[int] = 3,
    ctx: Context = None
) -> str:
    """Analyze a stack trace and find relevant solutions on Stack Overflow.
    
    Args:
        stack_trace: The stack trace to analyze
        language: Programming language of the stack trace
        include_comments: Whether to include comments in results
        response_format: Format of response ("json" or "markdown")
        limit: Maximum number of results to return
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
            min_score=0,
            limit=limit,
            include_comments=include_comments
        )
        
        ctx.debug(f"Found {len(results)} results")
        
        return format_response(results, response_format)
    except Exception as e:
        ctx.error(f"Error analyzing stack trace: {str(e)}")
        raise Error(f"Failed to analyze stack trace: {str(e)}")

if __name__ == "__main__":
    mcp.run()
        