import httpx
import time
from typing import Dict, List, Optional, Any, Union
import json
from dataclasses import asdict
import asyncio
from datetime import datetime

from .types import (
    StackOverflowQuestion,
    StackOverflowAnswer,
    StackOverflowComment,
    SearchResult,
    SearchResultComments
)

from .env import (
    MAX_REQUEST_PER_WINDOW,
    RATE_LIMIT_WINDOW_MS,
    RETRY_AFTER_MS
)

STACKOVERFLOW_API = "https://api.stackexchange.com/2.3"

class StackExchangeAPI:
    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None):
        self.api_key = api_key
        self.access_token = access_token
        self.request_timestamps = []
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    def _check_rate_limit(self) -> bool:
        now = time.time() * 1000
                
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if now - ts < RATE_LIMIT_WINDOW_MS
        ]
        
        if len(self.request_timestamps) >= MAX_REQUEST_PER_WINDOW:
            return False
        
        self.request_timestamps.append(now)
        return True
    
    async def _with_rate_limit(self, func, *args, retries=3, attempts=10, **kwargs):
        """Execute a function with rate limiting.

        Args:
            func (_type_): Function to execute with rate limiting
            retries (int, optional): Number of retries after API rate limit error. Defaults to 3.
            attempts (int, optional): Number of times to retry after hitting local rate limit. Defaults to 10.

        Raises:
            Exception: When maximum rate limiting attempts are exceeded
            e: Original error if retries are exhausted

        Returns:
            Any: Result from the function
        """
        if retries is None:
            retries = self.default_retries
        
        if attempts <= 0:
            raise Exception("Maximum rate limiting attempts exceeded")
    
        if not self._check_rate_limit():
            print("Rate limit exceeded, waiting before retry")
            await asyncio.sleep(RETRY_AFTER_MS / 1000)
            return await self._with_rate_limit(func, *args, retries=retries, attempts=attempts-1, **kwargs)
        
        try: 
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            if retries > 0 and e.response.status_code == 429:
                print("Rate limit hit (429), retrying after delay...")
                await asyncio.sleep(RETRY_AFTER_MS/1000)
                return await self._with_rate_limit(func, *args, retries=retries-1, attempts=attempts, **kwargs)
            raise e
    
    async def advanced_search(
        self,
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
        limit: Optional[int] = 5,
        include_comments: bool = False,
        retries: Optional[int] = 3
    ) -> List[SearchResult]:
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
            limit (Optional[int]): Maximum number of results to return
            include_comments (bool): Whether to include comments in results
            retries (Optional[int]): Number of retries for API rate limit issues
            
        Returns:
            List[SearchResult]: List of search results
        """
        params = {
            "site": "stackoverflow",
            "sort": sort_by,
            "order": "desc",
        }
        
        if query:
            params["q"] = query
            
        if tags:
            params["tagged"] = ";".join(tags)
            
        if excluded_tags:
            params["nottagged"] = ";".join(excluded_tags)
            
        if title:
            params["title"] = title
            
        if body:
            params["body"] = body
            
        if answers is not None:
            params["answers"] = str(answers)
            
        if has_accepted_answer is not None:
            params["accepted"] = "true" if has_accepted_answer else "false"
            
        if views is not None:
            params["views"] = str(views)
            
        if url:
            params["url"] = url
            
        if user_id is not None:
            params["user"] = str(user_id)
            
        if is_closed is not None:
            params["closed"] = "true" if is_closed else "false"
            
        if is_wiki is not None:
            params["wiki"] = "true" if is_wiki else "false"
            
        if is_migrated is not None:
            params["migrated"] = "true" if is_migrated else "false"
            
        if has_notice is not None:
            params["notice"] = "true" if has_notice else "false"
            
        if from_date:
            params["fromdate"] = str(int(from_date.timestamp()))
            
        if to_date:
            params["todate"] = str(int(to_date.timestamp()))
            
        if limit:
            params["pagesize"] = str(limit)
        
        # if self.api_key:
        #     params["key"] = self.api_key
            
        # if self.access_token:
        #     params["access_token"] = self.access_token
        
        async def _do_search():
            response = await self.client.get(f"{STACKOVERFLOW_API}/search/advanced", params=params)
            response.raise_for_status()
            return response.json()
        
        data = await self._with_rate_limit(_do_search, retries=retries)
        results = []
        
        for question_data in data.get("items", []):
            if min_score is not None and question_data.get("score", 0) < min_score:
                continue
            
            question = StackOverflowQuestion(
                question_id=question_data.get("question_id"),
                title=question_data.get("title", ""),
                body=question_data.get("body", ""),
                score=question_data.get("score", 0),
                answer_count=question_data.get("answer_count", 0),
                is_answered=question_data.get("is_answered", False),
                accepted_answer_id=question_data.get("accepted_answer_id"),
                creation_date=question_data.get("creation_date", 0),
                last_activity_date=question_data.get("last_activity_date", 0),
                view_count=question_data.get("view_count", 0),
                tags=question_data.get("tags", []),
                link=question_data.get("link", ""),
                is_closed=question_data.get("closed_date") is not None,
                owner=question_data.get("owner")
            )
            
            answers = await self.fetch_answers(question.question_id)
            
            comments = None
            
            if include_comments:
                question_comments = await self.fetch_comments(question.question_id)
                
                answers_comments = {}
                
                for answer in answers:
                    answer_comments = await self.fetch_comments(answer.answer_id)
                    answers_comments[answer.answer_id] = answer_comments
                    
                comments = SearchResultComments(
                    question=question_comments,
                    answers=answers_comments
                )
                
            results.append(SearchResult(
                question=question,
                answers=answers,
                comments=comments
            ))
            
        return results
    
    async def search_by_query(
        self, 
        query: str,
        tags: Optional[List[str]] = None,
        excluded_tags: Optional[List[str]] = None,
        min_score: Optional[int] = None,
        title: Optional[str] = None,
        body: Optional[str] = None,
        has_accepted_answer: Optional[bool] = None,
        answers: Optional[int] = None,
        sort_by: Optional[str] = "votes",
        limit: Optional[int] = 5,
        include_comments: bool = False,
        retries: Optional[int] = 3
    ) -> List[SearchResult]:
        """Search Stack Overflow for questions matching a query with additional filters.
        
        This is a simplified wrapper around advanced_search that focuses on common search parameters.
        
        Args:
            query (str): The search query
            tags (Optional[List[str]]): List of tags to filter by
            excluded_tags (Optional[List[str]]): List of tags to exclude
            min_score (Optional[int]): Minimum score threshold
            title (Optional[str]): Text that must appear in the title
            has_accepted_answer (Optional[bool]): Whether questions must have an accepted answer
            answers (Optional[int]): Minimum number of answers
            sort_by (Optional[str]): Field to sort by (activity, creation, votes, relevance)
            limit (Optional[int]): Maximum number of results to return
            include_comments (bool): Whether to include comments in results
            retries (Optional[int]): Number of retries for API rate limit issues
            
        Returns:
            List[SearchResult]: List of search results
        """
        return await self.advanced_search(
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
            include_comments=include_comments,
            retries=retries
        )
    
    async def fetch_answers(self, question_id: int) -> List[StackOverflowAnswer]:
        """Fetch Answers for a specific question.

        Args:
            question_id (int): Stack Overflow question ID

        Returns:
            List[StackOverflowAnswer]: List of answers for the question
        """
        params = {
            "site": "stackoverflow",
            "sort": "votes",
            "order": "desc"
        }
        
        # if self.api_key:
        #     params["key"] = self.api_key
        
        # if self.access_token:
        #     params["access_token"] = self.access_token
        
        async def _do_fetch():
            response = await self.client.get(
                f"{STACKOVERFLOW_API}/questions/{question_id}/answers",
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        data = await self._with_rate_limit(_do_fetch)
        answers = []
        
        for answer_data in data.get("items", []):
            answer = StackOverflowAnswer(
                answer_id=answer_data.get("answer_id"),
                question_id=answer_data.get("question_id"),
                score=answer_data.get("score", 0),
                is_accepted=answer_data.get("is_accepted", False),
                body=answer_data.get("body", ""),
                creation_date=answer_data.get("creation_date", 0),
                last_activity_date=answer_data.get("last_activity_date", 0),
                link=answer_data.get("link", ""),
                owner=answer_data.get("owner")
            )
            answers.append(answer)
        
        return answers
    
    async def fetch_comments(self, post_id: int) -> List[StackOverflowComment]:
        """Fetch comments for a specific post (question or answer)
        
        Args:
            post_id (int): ID of the post (question or answer)

        Returns:
            List[StackOverflowComment]: List of comments on the post
        """
        params = {
            "site": "stackoverflow",
            "sort": "votes",
            "order": "desc"
        }
        
        # if self.api_key:
        #     params["key"] = self.api_key
        
        # if self.access_token:
        #     params["access_token"] = self.access_token
        
        async def _do_fetch():
            response = await self.client.get(
                f"{STACKOVERFLOW_API}/posts/{post_id}/comments", 
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        data = await self._with_rate_limit(_do_fetch)
        comments = []
        
        for comment_data in data.get("items", []):
            comment = StackOverflowComment(
                comment_id=comment_data.get("comment_id"),
                post_id=comment_data.get("post_id"),
                score=comment_data.get("score", 0),
                body=comment_data.get("body", ""),
                creation_date=comment_data.get("creation_date", 0),
                owner=comment_data.get("owner")
            )
            comments.append(comment)
        
        return comments
    
    async def get_question(self, question_id: int, include_comments: bool = True) -> SearchResult:
        """Get a specific question by ID.

        Args:
            question_id (int): Stack Overflow question ID
            include_comments (bool): Whether to include comments in results

        Raises:
            ValueError: When question is not found

        Returns:
            SearchResult: The question with its answers and comments
        """
        params = {
            "site": "stackoverflow",
        }
        
        # if self.api_key:
        #     params["key"] = self.api_key
        
        # if self.access_token:
        #     params["access_token"] = self.access_token
        
        async def _do_fetch():
            response = await self.client.get(
                f"{STACKOVERFLOW_API}/questions/{question_id}", 
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        data = await self._with_rate_limit(_do_fetch)
        
        if not data.get("items"):
            raise ValueError(f"Question with ID {question_id} not found")
        
        question_data = data["items"][0]
        question = StackOverflowQuestion(
            question_id=question_data.get("question_id"),
            title=question_data.get("title", ""),
            body=question_data.get("body", ""),
            score=question_data.get("score", 0),
            answer_count=question_data.get("answer_count", 0),
            is_answered=question_data.get("is_answered", False),
            accepted_answer_id=question_data.get("accepted_answer_id"),
            creation_date=question_data.get("creation_date", 0),
            last_activity_date=question_data.get("last_activity_date", 0),
            view_count=question_data.get("view_count", 0),
            tags=question_data.get("tags", []),
            link=question_data.get("link", ""),
            is_closed=question_data.get("closed_date") is not None,
            owner=question_data.get("owner")
        )
        
        answers = await self.fetch_answers(question.question_id)
        
        comments = None
        if include_comments:
            question_comments = await self.fetch_comments(question.question_id)
            answer_comments = {}
            
            for answer in answers:
                answer_comments[answer.answer_id] = await self.fetch_comments(answer.answer_id)
            
            comments = SearchResultComments(
                question=question_comments,
                answers=answer_comments
            )
        
        return SearchResult(
            question=question,
            answers=answers,
            comments=comments
        )