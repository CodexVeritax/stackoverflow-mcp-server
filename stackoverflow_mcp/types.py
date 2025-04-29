from dataclasses import dataclass
from typing import List , Dict , Optional , Union , Literal

@dataclass
class SearchByQueryInput:
    query: str
    tags: Optional[List[str]] = None
    min_score: Optional[int] = None
    include_comments: Optional[bool] = False
    response_format: Optional[Literal["json","markdown"]] = "markdown"
    limit: Optional[int] = 5

@dataclass
class SearchByErrorInput:
    error_message: str
    language: Optional[str] = None
    technologies: Optional[List[str]] = None
    min_score: Optional[int] = None
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
    tags: List[str] = None
    link: str = ""

@dataclass
class StackOverflowAnswer:
    answer_id: int
    question_id: int
    score: int
    is_accepted: bool
    body: str
    creation_date: int = 0
    link: str = ""

@dataclass
class StackOverflowComment:
    comment_id: int
    post_id: int
    score: int
    body: str
    creation_date: int = 0

@dataclass
class SearchResultComments:
    question: List[StackOverflowComment]
    answers: Dict[int, List[StackOverflowComment]]
    
@dataclass
class SearchResult:
    question: StackOverflowQuestion
    answers: List[StackOverflowAnswer]
    comments: Optional[SearchResultComments] = None