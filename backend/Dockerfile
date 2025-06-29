FROM python:3.11-slim

# 시스템 패키지 업데이트 및 FFmpeg 설치
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 전체 복사
COPY . .

# 업로드 디렉토리 생성
RUN mkdir -p /tmp/audio_merge/{uploads,converted,results}

# 포트 노출
EXPOSE 8000

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV FASTAPI_HOST=0.0.0.0
ENV FASTAPI_PORT=8000

# 시작 명령
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
