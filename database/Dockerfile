FROM python:3.9-slim

RUN apt-get update && apt-get install -y libpq-dev gcc

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
