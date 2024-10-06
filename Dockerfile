FROM python:3.12-slim

WORKDIR /app

COPY data/job_data.json data/job_data.json
COPY ["requirements.txt", "./"]

RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

COPY job_search_application job_search_application

EXPOSE 8000

WORKDIR /app/

CMD ["uvicorn", "job_search_application.app:app", "--host", "0.0.0.0", "--port", "8000"]
