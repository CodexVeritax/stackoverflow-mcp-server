import pytest
from stackoverflow_mcp.formatter import format_response, clean_html
from stackoverflow_mcp.types import (
    SearchResult, 
    StackOverflowQuestion, 
    StackOverflowAnswer,
    StackOverflowComment,
    SearchResultComments
)

@pytest.fixture
def sample_result():
    """Create a sample search result for testing."""
    question = StackOverflowQuestion(
        question_id=12345,
        title="How to test Python code?",
        body="<p>I'm trying to test my <code>Python</code> code.</p><pre><code>def test():\n    pass</code></pre>",
        score=10,
        answer_count=2,
        is_answered=True,
        accepted_answer_id=54321,
        tags=["python", "testing"],
        link="https://stackoverflow.com/q/12345"
    )
    
    answers = [
        StackOverflowAnswer(
            answer_id=54321,
            question_id=12345,
            score=5,
            is_accepted=True,
            body="<p>You should use <code>pytest</code>.</p>",
            link="https://stackoverflow.com/a/54321"
        ),
        StackOverflowAnswer(
            answer_id=67890,
            question_id=12345,
            score=3,
            is_accepted=False,
            body="<p>Another option is <code>unittest</code>.</p>",
            link="https://stackoverflow.com/a/67890"
        )
    ]
    
    comments = SearchResultComments(
        question=[
            StackOverflowComment(
                comment_id=111,
                post_id=12345,
                score=2,
                body="Have you tried pytest?"
            )
        ],
        answers={
            54321: [
                StackOverflowComment(
                    comment_id=222,
                    post_id=54321,
                    score=1,
                    body="Great answer!"
                )
            ],
            67890: []
        }
    )
    
    return SearchResult(
        question=question,
        answers=answers,
        comments=comments
    )

def test_clean_html():
    """Test HTML cleaning."""
    html = "<p>This is <b>bold</b> and <i>italic</i>.</p><code>inline code</code><pre><code>def function():\n    return True</code></pre>"
    cleaned = clean_html(html)
    
    assert "<p>" not in cleaned
    assert "<b>" not in cleaned
    assert "<i>" not in cleaned
    assert "This is bold and italic." in cleaned
    assert "`inline code`" in cleaned
    assert "```\ndef function():\n    return True\n```" in cleaned

def test_format_response_markdown(sample_result):
    """Test formatting as Markdown."""
    markdown = format_response([sample_result], "markdown")
    
    assert "# How to test Python code?" in markdown
    assert "**Score:** 10" in markdown
    assert "## Question" in markdown
    assert "I'm trying to test my `Python` code." in markdown
    assert "```\ndef test():\n    pass\n```" in markdown
    assert "### Question Comments" in markdown
    assert "- Have you tried pytest?" in markdown
    assert "### ✓ Answer (Score: 5)" in markdown
    assert "You should use `pytest`." in markdown
    assert "### Answer (Score: 3)" in markdown
    assert "Another option is `unittest`." in markdown
    assert "[View on Stack Overflow](https://stackoverflow.com/q/12345)" in markdown

def test_format_response_json(sample_result):
    """Test formatting as JSON."""
    json_str = format_response([sample_result], "json")
    
    assert "How to test Python code?" in json_str
    assert "question_id" in json_str
    assert "answers" in json_str
    assert "comments" in json_str