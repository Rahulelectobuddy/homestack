FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/src

WORKDIR /app

COPY libs/common-python /libs/common-python
RUN pip install --no-cache-dir /libs/common-python

COPY services/apps/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/apps/backend/src/ ./src

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

