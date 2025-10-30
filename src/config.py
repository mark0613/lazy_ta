import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Path
BASE_DIR = Path(__file__).resolve().parent.parent

RESULTS_DIR = BASE_DIR / 'results'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

PROGRESS_LOG_PATH = RESULTS_DIR / 'grading_progress.jsonl'
if not PROGRESS_LOG_PATH.exists():
    PROGRESS_LOG_PATH.touch()

TEST_CASES_DIR = BASE_DIR / 'test_cases'

# LLM settings
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-2.5-flash')


# Compiler settings
GCC_PATH = os.getenv('GCC_PATH', 'gcc')
GPP_PATH = os.getenv('GPP_PATH', 'g++')
COMPILE_TIMEOUT = int(os.getenv('COMPILE_TIMEOUT', '5'))


# Testing settings
TEST_TIMEOUT = int(os.getenv('TEST_TIMEOUT', '5'))
MEMORY_LIMIT_MB = int(os.getenv('MEMORY_LIMIT_MB', '256'))
