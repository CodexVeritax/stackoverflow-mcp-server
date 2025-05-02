import httpx
import time
from typing import Dict , List , Optional , Any , Union
import json
from dataclasses import asdict
import asyncio

from .types import (
    StackOverflowQuestion,
    StackOverflowAnswer,
    StackOverflowComment,
    SearchResult,
    SearchResultComments
)

STACKOVERFLOW_API = "https://api.stackexchange.com/2.3"
DEFAULT_FILTER = "!*MZqiDl8Y0c)yVzXS"
ANSWER_FILTER = "!*MZqiDl8Y0c)yVzXS"
COMMENT_FILTER = "!*Mg-gxeRLu"


MAX_REQUESTS_PER_WINDOW = 30
RATE_LIMIT_WINDOW_MS = 6000
RETRY_AFTER_MS = 2000

class StackExchangeAPI:
    def __init__(self , api_key : Optional[str] = None , access_token: Optional[str] = None):
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
        
        if len(self.request_timestamps) >= MAX_REQUESTS_PER_WINDOW:
            return False
        
        self.request_timestamps.append(now)
        return True
    
    async def _with_rate_limit(self , func , *args , retries=3 , **kwargs):
        """Execute a function with rate limiting.

        Args:
            func (_type_): _description_
            retries (int, optional): _description_. Defaults to 3.

        Raises:
            e: _description_

        Returns:
            _type_: _description_
        """
        if not self._check_rate_limit():
            print("Rate limit exceeded , waiting before retry")
            await asyncio.sleep(RETRY_AFTER_MS / 1000)
            return await self._with_rate_limit(func , *args , retries=retries , **kwargs)
        
        try: 
            return await func(*args , **kwargs)
        except httpx.HTTPStatusError as e :
            if retries > 0 and e.response.status_code == 429:
                print("Rate limit hit (429) , retrying after delay...")
                await asyncio.sleep(RETRY_AFTER_MS/1000)
                return await self._with_rate_limit(func , *args , retries=retries-1 , **kwargs)
            raise e
    
    async def search_by_query(
        self , 
        query: str,
        tags: Optional[List[str]] = None,
        min_score: Optional[int] = None,
        limit: Optional[int] = 5,
        include_comments: bool = False
    ) -> List[SearchResult]:
        """Search Stack Overflow for questions matching a query.
        Args:
            query (str): _description_
            tags (Optional[List[str]], optional): _description_. Defaults to None.
            min_score (Optional[int], optional): _description_. Defaults to None.
            limit (Optional[int], optional): _description_. Defaults to 5.
            include_comments (bool, optional): _description_. Defaults to False.

        Returns:
            List[SearchResult]: _description_
        """
        params = {
            "site": "stackoverflow",
            "sort": "votes",
            "order": "desc",
            "filter": DEFAULT_FILTER,
            "q": query
        }
        
        if tags:
            params["tagged"] = ";".join(tags)
        
        if limit:
            params["pagesize"] = str(limit)
        
        if self.api_key:
            params["key"] = self.api_key
            
        if self.access_token:
            params["access_token"] = self.access_token
        
        async def _do_search():
            response = await self.client.get(f"{STACKOVERFLOW_API}/search/advanced" , params=params)
            response.raise_for_status()
            return response.json()
        
        data = await self._with_rate_limit(_do_search)
        results = []
        
        for question_data in data.get("items" , []):
            if min_score is not None and question_data.get("score" , 0) < min_score:
                continue
            
            question = StackOverflowQuestion(
                question_id=question_data.get("question_id"),
                title=question_data.get("title" , ""),
                body=question_data.get("body", ""),
                score=question_data.get("score" , 0),
                answer_count=question_data.get("answer_count", 0),
                is_answered=question_data.get("is_answered", False),
                accepted_answer_id=question_data.get("accepted_answer_id"),
                creation_date=question_data.get("creation_date", 0),
                tags=question_data.get("tags" , []),
                link= question_data.get("link" , "")
            )
            
            answers = await self.fetch_answers(question.question_id)
            
            comments = None
            
            if include_comments:
                question_comments = await self.fetch_comments(question.question_id)
                
                answers_comments = {}
                
                for answer in answers:
                    answers_comments[answer.answer.id] = await self.fetch_comments(answer.answer_id)
                    
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
    
    
    async def fetch_answers(self , question_id : int ) -> List[StackOverflowAnswer]:
        """Fetch Answers for a specific question.

        Args:
            question_id (int): _description_

        Returns:
            List[StackOverflowAnswer]: _description_
        """
        params = {
            "site": "stackoverflow",
            "filter": ANSWER_FILTER,
            "sort": "votes",
            "order": "desc"
        }
        
        if self.api_key:
            params["key"] = self.api_key
        
        if self.access_token:
            params["access_token"] = self.access_token
        
        async def _do_fetch():
            response = await self.client.get(
                f"{STACKOVERFLOW_API}/questions/{question_id}/answers",
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        data = await self._with_rate_limit(_do_fetch)
        answers = []
        
        for answer_data in data.get("items" , []):
            answer = StackOverflowAnswer(
                answer_id=answer_data.get("answer_id"),
                question_id=answer_data.get("question_id"),
                score=answer_data.get("score", 0),
                is_accepted=answer_data.get("is_accepted", False),
                body=answer_data.get("body", ""),
                creation_date=answer_data.get("creation_date", 0),
                link=answer_data.get("link", "")
            )
            answers.append(answer)
        
        return answers
    
    async def fetch_comments(self, post_id: int) -> List[StackOverflowComment]:
        """Fetch comments for a specific post (question or answer)
        Args:
            post_id (int): _description_

        Returns:
            List[StackOverflowComment]: _description_
        """
        params = {
            "site": "stackoverflow",
            "filter": COMMENT_FILTER,
            "sort": "votes",
            "order": "desc"
        }
        
        if self.api_key:
            params["key"] = self.api_key
        
        if self.access_token:
            params["access_token"] = self.access_token
        
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
                creation_date=comment_data.get("creation_date", 0)
            )
            comments.append(comment)
        
        return comments
    
    async def get_question(self, question_id: int, include_comments: bool = True) -> SearchResult:
        """Get a specific question by ID.

        Args:
            question_id (int): _description_
            include_comments (bool, optional): _description_. Defaults to True.

        Raises:
            ValueError: _description_

        Returns:
            SearchResult: _description_
        """
        params = {
            "site": "stackoverflow",
            "filter": DEFAULT_FILTER
        }
        
        if self.api_key:
            params["key"] = self.api_key
        
        if self.access_token:
            params["access_token"] = self.access_token
        
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
            tags=question_data.get("tags", []),
            link=question_data.get("link", "")
        )
        
        # Fetch answers
        answers = await self.fetch_answers(question.question_id)
        
        # Fetch comments if needed
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