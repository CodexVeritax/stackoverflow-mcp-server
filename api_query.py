#!/usr/bin/env python3
"""
Stack Exchange API Query Tool

This script allows you to directly call the Stack Exchange API with various parameters
and see the results. It's useful for testing queries and seeing the raw results.

Usage:
    python api_query.py search "python pandas dataframe" --tags python,pandas --min-score 10
    python api_query.py question 12345
    python api_query.py error "TypeError: cannot use a string pattern" --language python
"""

import os
import sys
import json
import asyncio
import argparse
from dotenv import load_dotenv

from stackoverflow_mcp.api import StackExchangeAPI
from stackoverflow_mcp.formatter import format_response


def setup_environment():
    """Load environment variables from .env file"""
    if os.path.exists(".env"):
        load_dotenv(".env")
    elif os.path.exists(".env.test"):
        load_dotenv(".env.test")
    else:
        print("Warning: No .env or .env.test file found. Using default settings.")


async def run_search_query(api, args):
    """Run a search query with the given arguments"""
    tags = args.tags.split(',') if args.tags else None
    
    excluded_tags = args.excluded_tags.split(',') if args.excluded_tags else None
    
    print(f"\nRunning search query: '{args.query}'")
    if args.title:
        print(f"Running search with title containing: '{args.title}'")
    if args.body:
        print(f"Running search with body containing: '{args.body}'")
    print(f"Tags: {tags}")
    print(f"Excluded tags: {excluded_tags}")
    print(f"Min score: {args.min_score}")
    print(f"Limit: {args.limit}")
    print(f"Include comments: {args.comments}\n")
    
    try:
        results = await api.search_by_query(
            query=args.query,
            tags=tags,
            title=args.title,
            body=args.body,
            excluded_tags=excluded_tags,
            min_score=args.min_score,
            limit=args.limit,
            include_comments=args.comments
        )
        
        print(f"Found {len(results)} results")
        
        if args.raw:
            for i, result in enumerate(results):
                print(f"\n--- Result {i+1} ---")
                print(f"Question ID: {result.question.question_id}")
                print(f"Title: {result.question.title}")
                print(f"Score: {result.question.score}")
                print(f"Tags: {result.question.tags}")
                print(f"Link: {result.question.link}")
                print(f"Answers: {len(result.answers)}")
                if result.comments:
                    print(f"Question comments: {len(result.comments.question)}")
        else:
            formatted = format_response(results, args.format)
            print(formatted)
        
    except Exception as e:
        print(f"Error during search: {str(e)}")


async def run_question_query(api, args):
    """Get a specific question by ID"""
    try:
        print(f"\nFetching question ID: {args.question_id}")
        print(f"Include comments: {args.comments}\n")
        
        result = await api.get_question(
            question_id=args.question_id,
            include_comments=args.comments
        )
        
        if args.raw:
            print(f"Question ID: {result.question.question_id}")
            print(f"Title: {result.question.title}")
            print(f"Score: {result.question.score}")
            print(f"Tags: {result.question.tags}")
            print(f"Link: {result.question.link}")
            print(f"Answers: {len(result.answers)}")
            if result.comments:
                print(f"Question comments: {len(result.comments.question)}")
        else:
            formatted = format_response([result], args.format)
            print(formatted)
        
    except Exception as e:
        print(f"Error fetching question: {str(e)}")


async def run_error_query(api, args):
    """Search for an error message with optional language filter"""
    technologies = args.technologies.split(',') if args.technologies else None
    
    try:
        print(f"\nSearching for error: '{args.error}'")
        print(f"Language: {args.language}")
        print(f"Technologies: {technologies}")
        if args.title:
            print(f"Title containing: '{args.title}'")
        if args.body:
            print(f"Body containing: '{args.body}'")
        print(f"Min score: {args.min_score}")
        print(f"Limit: {args.limit}")
        print(f"Include comments: {args.comments}\n")
        
        tags = []
        if args.language:
            tags.append(args.language.lower())
        if technologies:
            tags.extend([t.lower() for t in technologies])
        
        results = await api.search_by_query(
            query=args.error,
            title=args.title,
            body=args.body,
            tags=tags if tags else None,
            min_score=args.min_score,
            limit=args.limit,
            include_comments=args.comments
        )
        
        print(f"Found {len(results)} results")
        
        if args.raw:
            for i, result in enumerate(results):
                print(f"\n--- Result {i+1} ---")
                print(f"Question ID: {result.question.question_id}")
                print(f"Title: {result.question.title}")
                print(f"Score: {result.question.score}")
                print(f"Tags: {result.question.tags}")
                print(f"Link: {result.question.link}")
                print(f"Answers: {len(result.answers)}")
                if result.comments:
                    print(f"Question comments: {len(result.comments.question)}")
        else:
            formatted = format_response(results, args.format)
            print(formatted)
        
    except Exception as e:
        print(f"Error searching for error: {str(e)}")


async def main():
    """Parse arguments and run the appropriate query"""
    parser = argparse.ArgumentParser(description="Stack Exchange API Query Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search Stack Overflow")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--tags", help="Comma-separated list of tags")
    search_parser.add_argument("--title", help="Word(s) that must appear in the question title")
    search_parser.add_argument("--body", help="Word(s) that must appear in the body of the question")
    search_parser.add_argument("--excluded-tags", help="Comma-separated list of tags to exclude")
    search_parser.add_argument("--min-score", type=int, default=0, help="Minimum score")
    search_parser.add_argument("--limit", type=int, default=5, help="Maximum number of results")
    search_parser.add_argument("--comments", action="store_true", help="Include comments")
    search_parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    search_parser.add_argument("--raw", action="store_true", help="Print raw data structure")
    
    # Question command
    question_parser = subparsers.add_parser("question", help="Get a specific question")
    question_parser.add_argument("question_id", type=int, help="Question ID")
    question_parser.add_argument("--comments", action="store_true", help="Include comments")
    question_parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    question_parser.add_argument("--raw", action="store_true", help="Print raw data structure")
    
    # Error command
    error_parser = subparsers.add_parser("error", help="Search for an error message")
    error_parser.add_argument("error", help="Error message")
    error_parser.add_argument("--title", help="Word(s) that must appear in the question title")
    error_parser.add_argument("--body", help="Word(s) that must appear in the body of the question")
    error_parser.add_argument("--language", help="Programming language")
    error_parser.add_argument("--technologies", help="Comma-separated list of technologies")
    error_parser.add_argument("--min-score", type=int, default=0, help="Minimum score")
    error_parser.add_argument("--limit", type=int, default=5, help="Maximum number of results")
    error_parser.add_argument("--comments", action="store_true", help="Include comments")
    error_parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    error_parser.add_argument("--raw", action="store_true", help="Print raw data structure")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    setup_environment()
    
    api_key = os.getenv("STACK_EXCHANGE_API_KEY")
    
    if not api_key:
        print("Warning: No API key found. Requests may be rate limited.")
    
    api = StackExchangeAPI(api_key=api_key)
    
    try:
        if args.command == "search":
            await run_search_query(api, args)
        elif args.command == "question":
            await run_question_query(api, args)
        elif args.command == "error":
            await run_error_query(api, args)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
        
    finally:
        await api.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))