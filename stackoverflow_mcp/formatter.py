import json
from typing import List
from dataclasses import asdict
import re

from .types import SearchResult, StackOverflowAnswer, StackOverflowComment


def format_response(results: List[SearchResult], format_type: str = "markdown") -> str:
    """Format search results as either JSON or Markdown.

    Args:
        results (List[SearchResult]): List of search results to format
        format_type (str, optional): Output format type - either "json" or "markdown". Defaults to "markdown".

    Returns:
        str: Formatted string representation of the search results
    """
    
    if format_type == "json":
        def _convert_to_dict(obj):
            if hasattr(obj, "__dataclass_fields__"):
                return asdict(obj)
            return obj
        
        class DataClassJSONEncoder(json.JSONEncoder):
            def default(self, obj):
                if hasattr(obj, "__dataclass_fields__"):
                    return asdict(obj)
                return super().default(obj)
            
        return json.dumps(results, cls=DataClassJSONEncoder, indent=2)
    
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

def clean_html(html_text: str) -> str:
    """Clean HTML tags from text while preserving code blocks.

    Args:
        html_text (str): HTML text to be cleaned

    Returns:
        str: Cleaned text with HTML tags removed and code blocks preserved
    """
    
    code_blocks = []
    
    def replace_code_block(match):
        code = match.group(1) or match.group(2)
        code_blocks.append(code)
        return f"CODE_BLOCK_{len(code_blocks)-1}"
    
    html_without_code = re.sub(r'<pre><code>(.*?)</code></pre>|<code>(.*?)</code>', replace_code_block, html_text, flags=re.DOTALL)
    
    text_without_html = re.sub(r'<[^>]+>', '', html_without_code)
    
    for i, code in enumerate(code_blocks):
        if '\n' in code or len(code) > 80:
            text_without_html = text_without_html.replace(f"CODE_BLOCK_{i}", f"```\n{code}\n```")
        else:
            text_without_html = text_without_html.replace(f"CODE_BLOCK_{i}", f"`{code}`")
            
    
    text_without_html = text_without_html.replace("&lt;", "<")
    text_without_html = text_without_html.replace("&gt;", ">")
    text_without_html = text_without_html.replace("&amp;", "&")
    text_without_html = text_without_html.replace("&quot;", "\"")
    
    return text_without_html