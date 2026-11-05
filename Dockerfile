FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir starlette uvicorn websockets httpx
COPY . .
EXPOSE 7860
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
