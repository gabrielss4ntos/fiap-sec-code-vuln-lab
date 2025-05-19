FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir flask

EXPOSE 8084

CMD ["python", "app.py"]
