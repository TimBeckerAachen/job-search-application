import os
from dotenv import load_dotenv

os.environ['RUN_TIMEZONE_CHECK'] = '0'

from job_search_application.db import init_db

load_dotenv()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
