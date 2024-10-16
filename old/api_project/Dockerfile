FROM python:3.9

WORKDIR /app

COPY api_project/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api_project .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
