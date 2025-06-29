# Audio Merge Tool

Python + Next.js로 구현된 고성능 WAV 파일 병합 도구입니다. 여러 오디오 파일을 무손실로 결합하고, 포맷 변환 및 크로스페이드 효과를 지원합니다.

## 📁 프로젝트 구조

```
audio-merge/
├── backend/              # Python 백엔드
│   ├── audio_merge/      # 핵심 오디오 처리 로직
│   │   ├── core/         # 핵심 기능 (검증, 변환, 병합, 쓰기)
│   │   ├── cli/          # CLI 인터페이스
│   │   └── utils/        # 유틸리티 및 예외 처리
│   ├── api/              # FastAPI 웹 서버
│   │   ├── api/          # API 라우트 및 모델
│   │   └── services/     # 비즈니스 로직 서비스
│   ├── main.py           # CLI 진입점
│   ├── tests/            # 단위 테스트
│   └── requirements.txt  # Python 의존성
├── frontend/             # Next.js 프론트엔드
│   ├── src/              # React 컴포넌트 및 페이지
│   │   ├── app/          # Next.js App Router
│   │   ├── components/   # React 컴포넌트
│   │   └── lib/          # 유틸리티 및 타입
│   ├── start-dev.sh      # 개발 서버 시작 스크립트
│   └── package.json      # Node.js 의존성
├── package.json          # 워크스페이스 설정
└── docker-compose.yml    # 컨테이너 오케스트레이션
```

## ✨ 주요 기능

- **무손실 병합**: PCM 데이터를 직접 처리하여 품질 손실 없이 병합
- **자동 포맷 변환**: 샘플레이트, 채널, 비트깊이가 다른 파일들을 자동으로 통일
- **크로스페이드**: 파일 간 자연스러운 전환을 위한 크로스페이드 효과 지원
- **스트리밍 처리**: 큰 파일도 메모리 효율적으로 처리
- **웹 인터페이스**: 직관적인 Next.js 기반 웹 UI (shadcn/ui + Tailwind CSS)
- **REST API**: FastAPI 기반의 완전한 백엔드 API
- **실시간 진행률**: Server-Sent Events를 통한 실시간 처리 상태 확인
- **비동기 처리**: Celery + Redis를 통한 백그라운드 작업 처리

## 🚀 빠른 시작

### 1. 전체 개발 환경 (권장)

```bash
# 저장소 클론
git clone <repository-url>
cd python-audio-merge

# Python 가상환경 설정
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 백엔드 의존성 설치
cd backend
pip install -r requirements.txt
cd ..

# 프론트엔드 의존성 설치
npm install

# 전체 개발 서버 실행 (프론트+백엔드 동시)
npm run dev:all
```

웹 브라우저에서 http://localhost:3000 접속

### 2. CLI 도구만 사용

```bash
# 백엔드 디렉토리로 이동
cd backend

# Interactive 모드
python main.py

# Command-line 모드
python main.py file1.wav file2.wav --output merged.wav --auto-convert
```

### 3. Docker로 실행

```bash
# 전체 스택 실행 (백엔드 + Redis + Worker)
docker compose up -d

# API 서버: http://localhost:8000
# API 문서: http://localhost:8000/docs
# Flower 모니터링: http://localhost:5555
```

## 📖 사용법

### 웹 인터페이스

1. http://localhost:3000 접속
2. 오디오 파일들을 드래그 앤 드롭 또는 클릭하여 업로드
3. 병합 옵션 설정 (크로스페이드, 버퍼 크기 등)
4. "병합 시작" 클릭
5. 실시간으로 진행률 확인
6. 완료 후 결과 파일 다운로드

### CLI 인터페이스

```bash
# 기본 병합
python main.py audio1.wav audio2.wav audio3.wav

# 옵션과 함께 병합
python main.py *.wav \
  --output final_mix.wav \
  --auto-convert \
  --fade 500 \
  --verbose

# Interactive 모드
python main.py
```

### REST API

```bash
# 파일 업로드
curl -X POST "http://localhost:8000/api/upload" \
  -F "files=@audio1.wav" \
  -F "files=@audio2.wav"

# 병합 시작
curl -X POST "http://localhost:8000/api/merge" \
  -H "Content-Type: application/json" \
  -d '{"upload_id": "uuid", "options": {}}'

# 진행률 확인
curl "http://localhost:8000/api/status/{task_id}"

# 실시간 진행률 (Server-Sent Events)
curl "http://localhost:8000/api/events/{task_id}"

# 결과 다운로드
curl "http://localhost:8000/api/download/{task_id}"

# 정리
curl -X DELETE "http://localhost:8000/api/cleanup/{task_id}"

# 헬스 체크
curl "http://localhost:8000/api/health"
```

## 🔧 개발

### 전체 개발 환경

```bash
# 루트에서 전체 실행
npm run dev:all

# 또는 개별 실행
npm run frontend    # Next.js만
npm run backend     # FastAPI만
```

### 백엔드 개발

```bash
cd backend

# 개발 서버 실행
PYTHONPATH=. python -m uvicorn api.main:app --reload --port 8000

# 테스트 실행
pytest

# 코드 포맷팅
black .
flake8 .
```

### 프론트엔드 개발

```bash
cd frontend

# 개발 서버 실행
npm run dev

# 빌드
npm run build

# 린팅
npm run lint
```

### Celery Worker

```bash
cd backend

# Worker 실행
celery -A api.celery_app:celery worker --loglevel=info

# Flower 모니터링
celery -A api.celery_app:celery flower
```

## 🛠 기술 스택

### 백엔드
- **Python 3.11+**
- **FastAPI**: 고성능 웹 프레임워크
- **Celery**: 비동기 작업 큐
- **Redis**: 메시지 브로커 및 결과 저장소
- **Pydub**: 오디오 파일 처리
- **FFmpeg**: 오디오 코덱 지원

### 프론트엔드
- **Next.js 15.3.4**: React 기반 풀스택 프레임워크
- **React 19**: 최신 React
- **TypeScript**: 타입 안전성
- **Tailwind CSS**: 유틸리티 기반 스타일링
- **shadcn/ui**: 현대적인 UI 컴포넌트
- **Zustand**: 경량 상태 관리
- **next-themes**: 다크모드 지원

### DevOps
- **Docker**: 컨테이너화
- **Docker Compose**: 멀티 컨테이너 관리
- **concurrently**: 동시 개발 서버 실행

## 📋 시스템 요구사항

- Python 3.11 이상
- Node.js 18 이상
- FFmpeg (시스템 설치 필요)
- Redis (Docker 사용 시 자동 설치)

### FFmpeg 설치

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# https://ffmpeg.org/download.html 에서 다운로드
```

## 🎯 지원 포맷

- **입력**: WAV, MP3 (FFmpeg 지원 포맷)
- **출력**: WAV (PCM)
- **자동 변환**: 샘플레이트, 채널, 비트깊이 통일

## 📊 성능

- **메모리 효율**: 스트리밍 처리로 큰 파일도 안정적 처리
- **속도**: 네이티브 바이너리 조작으로 고속 병합
- **확장성**: Celery를 통한 분산 처리 지원
- **실시간 피드백**: SSE를 통한 진행률 스트리밍

## 📡 API 엔드포인트

- `POST /api/upload` - 파일 업로드 및 검증
- `POST /api/merge` - 병합 작업 시작
- `GET /api/status/{task_id}` - 작업 상태 조회
- `GET /api/events/{task_id}` - 실시간 진행률 (SSE)
- `GET /api/download/{task_id}` - 결과 파일 다운로드
- `DELETE /api/cleanup/{task_id}` - 임시 파일 정리
- `GET /api/health` - 시스템 상태 확인
- `GET /` - API 정보 및 헬스체크

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 감사의 말

- [Pydub](https://github.com/jiaaro/pydub) - 오디오 처리 라이브러리
- [FastAPI](https://fastapi.tiangolo.com/) - 현대적인 웹 프레임워크
- [Next.js](https://nextjs.org/) - React 프레임워크
- [shadcn/ui](https://ui.shadcn.com/) - 아름다운 UI 컴포넌트 