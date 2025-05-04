from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Literal
from datetime import datetime

@dataclass
class AdvancedSearchInput:
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    excluded_tags: Optional[List[str]] = None
    min_score: Optional[int] = None
    title: Optional[str] = None
    body: Optional[str] = None
    answers: Optional[int] = None
    has_accepted_answer: Optional[bool] = None
    views: Optional[int] = None
    url: Optional[str] = None
    user_id: Optional[int] = None
    is_closed: Optional[bool] = None
    is_wiki: Optional[bool] = None
    is_migrated: Optional[bool] = None
    has_notice: Optional[bool] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    sort_by: Optional[Literal["activity", "creation", "votes", "relevance"]] = "activity"
    include_comments: Optional[bool] = False
    response_format: Optional[Literal["json", "markdown"]] = "markdown"
    limit: Optional[int] = 5

@dataclass
class SearchByQueryInput:
    query: str
    tags: Optional[List[str]] = None
    excluded_tags: Optional[List[str]] = None
    min_score: Optional[int] = None
    title: Optional[str] = None
    body: Optional[str] = None
    has_accepted_answer: Optional[bool] = None
    answers: Optional[int] = None
    sort_by: Optional[Literal["activity", "creation", "votes", "relevance"]] = "votes"
    include_comments: Optional[bool] = False
    response_format: Optional[Literal["json","markdown"]] = "markdown"
    limit: Optional[int] = 5

@dataclass
class SearchByErrorInput:
    error_message: str
    language: Optional[str] = None
    technologies: Optional[List[str]] = None
    excluded_tags: Optional[List[str]] = None
    min_score: Optional[int] = None
    has_accepted_answer: Optional[bool] = None
    answers: Optional[int] = None
    include_comments: Optional[bool] = False
    response_format: Optional[Literal["json", "markdown"]] = "markdown"
    limit: Optional[int] = 5

@dataclass
class GetQuestionInput:
    question_id: int
    include_comments: Optional[bool] = True
    response_format: Optional[Literal["json", "markdown"]] = "markdown"

@dataclass
class StackOverflowQuestion:
    question_id: int
    title: str
    body: str
    score: int
    answer_count: int
    is_answered: bool
    accepted_answer_id: Optional[int] = None
    creation_date: int = 0
    last_activity_date: int = 0
    view_count: int = 0
    tags: List[str] = None
    link: str = ""
    is_closed: bool = False
    owner: Optional[Dict] = None

@dataclass
class StackOverflowAnswer:
    answer_id: int
    question_id: int
    score: int
    is_accepted: bool
    body: str
    creation_date: int = 0
    last_activity_date: int = 0
    link: str = ""
    owner: Optional[Dict] = None

@dataclass
class StackOverflowComment:
    comment_id: int
    post_id: int
    score: int
    body: str
    creation_date: int = 0
    owner: Optional[Dict] = None

@dataclass
class SearchResultComments:
    question: List[StackOverflowComment]
    answers: Dict[int, List[StackOverflowComment]]
    
@dataclass
class SearchResult:
    question: StackOverflowQuestion
    answers: List[StackOverflowAnswer]
    comments: Optional[SearchResultComments] = None