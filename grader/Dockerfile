FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      curl \
      ffmpeg \
      openjdk-17-jdk-headless \
      maven \
      nodejs \
      npm \
      unzip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN npm install -g eslint@8

COPY app ./app
COPY starter ./starter
COPY assessment3 ./assessment3
COPY assessment4 ./assessment4

EXPOSE 9000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
