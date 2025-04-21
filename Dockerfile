FROM python:3.12.10-slim-bookworm

WORKDIR portal-backend

COPY . .

# pass the environment variables when you run the dockerfile
ENV JWT_SECRET_KEY=""
ENV DB_SERVICE_URL=""
ENV DB_SERVICE_TOKEN=""

RUN pip install --no-cache-dir -r ./app/requirements.txt

EXPOSE 8000

CMD ["sh", "-c", "cd app && uvicorn main:app --workers 10 --host 0.0.0.0"]
