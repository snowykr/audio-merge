# Audio Merge - Next.js Frontend

Next.js 15 + shadcn/ui로 구현된 오디오 파일 병합 도구의 프론트엔드입니다.

## 🚀 빠른 시작

### 방법 1: 루트에서 실행 (권장)
```bash
# 1. 프로젝트 루트 디렉토리로 이동
cd python-audio-merge

# 2. 전체 개발 서버 시작 (Next.js + FastAPI 동시 실행)
npm run dev:all
```

### 방법 2: 자동 스크립트
```bash
# 1. frontend 디렉토리로 이동
cd frontend

# 2. 개발 서버 시작 (Next.js + FastAPI 동시 실행)
./start-dev.sh
```

### 방법 3: npm 명령어
```bash
# frontend 디렉토리에서
# Next.js + FastAPI 동시 실행
npm run dev:all

# 또는 개별 실행
npm run dev        # Next.js만
npm run backend    # FastAPI만
```

### 방법 4: 수동 실행
```bash
# 터미널 1: Next.js
cd frontend
npm run dev

# 터미널 2: FastAPI
cd backend
source ../.venv/bin/activate
PYTHONPATH=. python -m uvicorn api.main:app --reload --port 8000
```

## 📱 접속 URL

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

## 🛠 기술 스택

- **Framework**: Next.js 15.3.4 with Turbopack
- **React**: React 19
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: Zustand
- **Theme**: next-themes (다크모드 지원)
- **Toast**: Sonner
- **Icons**: Lucide React
- **Form**: React Hook Form
- **UI Components**: Radix UI 기반 shadcn/ui

## 📁 프로젝트 구조

```
src/
├── app/                 # Next.js App Router
│   ├── layout.tsx      # 루트 레이아웃
│   ├── page.tsx        # 홈페이지
│   └── globals.css     # 전역 스타일
├── components/         # React 컴포넌트
│   ├── ui/            # shadcn/ui 컴포넌트
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── progress.tsx
│   │   └── ...
│   ├── header.tsx     # 헤더 컴포넌트
│   ├── file-upload.tsx    # 파일 업로드
│   ├── merge-options.tsx  # 병합 옵션
│   ├── merge-control.tsx  # 병합 제어
│   ├── progress-tracker.tsx # 진행률 추적
│   ├── theme-toggle.tsx   # 테마 토글
│   └── footer.tsx     # 푸터
└── lib/               # 유틸리티 및 설정
    ├── types.ts       # TypeScript 타입 정의
    ├── store.ts       # Zustand 상태 관리
    ├── api.ts         # API 클라이언트
    └── utils.ts       # 공통 유틸리티
```

## 🎯 주요 기능

### ✅ 파일 업로드
- 드래그 앤 드롭 지원
- 실시간 파일 검증
- WAV, MP3 파일 지원
- 파일 크기 및 개수 제한
- 파일 유효성 실시간 피드백

### ✅ 병합 옵션
- Cross-fade 길이 조절 (0-5000ms)
- 버퍼 크기 선택 (32KB/64KB/128KB)
- 자동 포맷 변환 옵션
- 실시간 옵션 미리보기

### ✅ 실시간 진행률
- Server-Sent Events (SSE) 연결
- 실시간 진행률 바
- 상세 상태 메시지
- 오류 처리 및 재시도

### ✅ 다크모드
- 시스템 테마 자동 감지
- 부드러운 전환 애니메이션
- 모든 컴포넌트 완전 지원
- next-themes 기반 구현

### ✅ 반응형 디자인
- 모바일/태블릿/데스크톱 지원
- 터치 친화적 인터페이스
- Tailwind CSS 브레이크포인트

## 🔧 개발 명령어

```bash
# 의존성 설치
npm install

# 개발 서버 (Turbopack 사용)
npm run dev

# 프로덕션 빌드
npm run build

# 프로덕션 실행
npm run start

# 린팅
npm run lint

# 백엔드 + 프론트엔드 동시 실행
npm run dev:all

# 백엔드만 실행
npm run backend
```

## 🌍 환경 변수

`.env.local` 파일을 생성하여 설정하세요:

```env
# FastAPI 백엔드 URL
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## 🔗 API 연동

FastAPI 백엔드와 완전 호환되는 TypeScript 타입과 API 클라이언트를 제공합니다:

### API 엔드포인트
- **파일 업로드**: `POST /api/upload`
- **병합 시작**: `POST /api/merge`
- **실시간 진행률**: `GET /api/events/{task_id}` (SSE)
- **상태 조회**: `GET /api/status/{task_id}`
- **결과 다운로드**: `GET /api/download/{task_id}`
- **정리**: `DELETE /api/cleanup/{task_id}`
- **헬스체크**: `GET /api/health`

### TypeScript 타입 정의
```typescript
interface UploadResponse {
  upload_id: string
  files: FileInfo[]
  validation_results: string[]
}

interface TaskStatus {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  current_step: string
  message: string
}
```

## 🔄 Alpine.js에서 마이그레이션

기존 Alpine.js 버전에서 다음과 같이 개선되었습니다:

| 기능 | Alpine.js | Next.js + shadcn/ui |
|------|-----------|---------------------|
| 타입 안전성 | ❌ | ✅ TypeScript |
| 컴포넌트화 | ❌ | ✅ 재사용 가능한 컴포넌트 |
| 상태 관리 | 기본적 | ✅ Zustand 전역 상태 |
| 다크모드 | 수동 구현 | ✅ next-themes 시스템 |
| 빌드 최적화 | ❌ | ✅ Next.js + Turbopack |
| 개발 경험 | 기본적 | ✅ 핫 리로드, 타입 체크 |
| UI 컴포넌트 | 수동 | ✅ shadcn/ui 시스템 |

## 📦 주요 의존성

### 프로덕션 의존성
- `next`: 15.3.4 - Next.js 프레임워크
- `react`: 19.0.0 - React 라이브러리
- `@radix-ui/*`: UI 컴포넌트 기반
- `zustand`: 상태 관리
- `next-themes`: 테마 관리
- `sonner`: 토스트 알림
- `lucide-react`: 아이콘

### 개발 의존성
- `typescript`: TypeScript 지원
- `tailwindcss`: CSS 프레임워크
- `eslint`: 코드 린팅
- `concurrently`: 동시 프로세스 실행

## 🚀 배포

```bash
# 프로덕션 빌드
npm run build

# 정적 파일 확인
npm run start

# Docker 빌드 (루트에서)
docker compose build

# Docker 실행
docker compose up -d
```

## 📄 라이센스

이 프로젝트는 부모 프로젝트와 동일한 라이센스를 따릅니다.