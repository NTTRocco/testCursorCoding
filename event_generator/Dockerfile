FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY event_generator /app/event_generator

EXPOSE 5001

CMD ["python", "-m", "event_generator.api.app"] 