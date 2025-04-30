import json
from typing import List
from dataclasses import asdict
import re

from .types import SearchResult , StackOverflowAnswer , StackOverflowComment


def format_response(results: List[SearchResult] , format_type: str = "markdown") -> str:
    """Format search results as either JSON or Markdown.

    Args:
        results (List[SearchResult]): _description_
        format_type (str, optional): _description_. Defaults to "markdown".

    Returns:
        str: _description_
    """
    
    if format_type == "json":
        def _convert_to_dict(obj):
            if hasattr(obj , "__dataclass_fields__"):
                return asdict(obj)
            return obj
        
        class DataClassJSONEncoder(json.JSONEncoder):
            def default(self , obj):
                if hasattr(obj , "dataclass_fields__"):
                    return asdict(obj)
                return super().default(obj)
            
        return json.dumps(results , cls=DataClassJSONEncoder , indent=2)
    
    if not results:
        return "No results found."
    
    markdown = ""
    
    for result in results:
        markdown += f"# {result.question.title}\n\n"
        markdown += f"**Score:** {result.question.score} | **Answers:** {result.question.answer_count}\n\n"
        
        question_body = clean_html(result.question.body)
        markdown += f"## Question\n\n{question_body}\n\n"
        
        if result.comments and result.comments.question:
            markdown += "### Question Comments\n\n"
            for comment in result.comments.question:
                markdown += f"- {clean_html(comment.body)} *(Score: {comment.score})*\n"
            markdown += "\n"
            
        markdown += "## Answers\n\n"
        for answer in result.answers:
            markdown += f"### {'✓ ' if answer.is_accepted else ''}Answer (Score: {answer.score})\n\n"
            answer_body = clean_html(answer.body)
            markdown += f"{answer_body}\n\n"
            
            if (result.comments and 
                result.comments.answers and
                answer.answer_id in result.comments.answers and
                result.comments.answers[answer.answer_id]
                ):
                markdown += "#### Answer Comments\n\n"
                for comment in result.comments.answers[answer.answer_id]:
                    markdown += f"- {clean_html(comment.body)} *(Score: {comment.score})*\n"
                
                markdown += "/n"
                
        markdown += f"---\n\n[View on Stack Overflow]({result.question.link})\n\n"
        
    return markdown