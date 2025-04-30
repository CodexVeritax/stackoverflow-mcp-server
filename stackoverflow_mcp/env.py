import os
from dotenv import load_dotenv

load_dotenv()

STACK_EXCHANGE_API_KEY = os.getenv("STACK_EXCHANGE_API_KEY")
STACK_EXCHANGE_ACCESS_TOKEN = os.getenv("STACK_EXCHANGE_ACCESS_TOKEN")

MAX_REQUEST_PER_WINDOW = int(os.getenv("MAX_REQUESTS_PER_WINDOW" , "30"))
RATE_LIMIT_WINDOW_MS = int(os.getenv("RATE_LIMIT_WINDOW_MS" , "60000"))
RETRY_AFTER_MS = int(os.getenv("RETRY_AFTER_MS" , "2000"))
