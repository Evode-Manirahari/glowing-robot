FROM python:3.13-slim

WORKDIR /app

# Install backend deps first (layer cache)
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy backend source
COPY app/ app/

# sim/, robot_api/, evals/ are mounted as volumes in docker-compose for dev.
# For production builds they should be COPY'd here instead.

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
