FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY libs/common-python /libs/common-python
RUN pip install --no-cache-dir /libs/common-python

COPY services/apps/irrigation-mqtt/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/apps/irrigation-mqtt/src/ ./src

CMD ["python", "src/main.py"]

