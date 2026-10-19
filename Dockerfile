FROM python:3.11-slim
WORKDIR /athena
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 athena
COPY app ./app
COPY scripts ./scripts
COPY models ./models
RUN mkdir -p /athena/data && chown -R athena:athena /athena /home/athena
USER athena
ENV ATHENA_DATA_DIR=/athena/data PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-proxy-headers"]
