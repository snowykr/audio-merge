# Audio Merge - Next.js Frontend

Next.js + shadcn/ui로 구현된 오디오 파일 병합 도구의 프론트엔드입니다.

## 🚀 빠른 시작

### 방법 1: 자동 스크립트 (권장)
```bash
# 1. web-nextjs 디렉토리로 이동
cd web-nextjs

# 2. 개발 서버 시작 (Next.js + FastAPI 동시 실행)
./start-dev.sh
```

### 방법 2: npm 명령어
```bash
# Next.js + FastAPI 동시 실행
npm run dev:all

# 또는 개별 실행
npm run dev        # Next.js만
npm run backend    # FastAPI만
```

### 방법 3: 수동 실행
```bash
# 터미널 1: Next.js
npm run dev

# 터미널 2: FastAPI
cd ../web
python -m uvicorn app.main:app --reload
```

## 📱 접속 URL

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

## 🛠 기술 스택

- **Framework**: Next.js 15.3.4 with Turbopack
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: Zustand
- **Theme**: next-themes (다크모드 지원)
- **Toast**: Sonner
- **Icons**: Lucide React

## 📁 프로젝트 구조

```
src/
├── app/                 # Next.js App Router
│   ├── layout.tsx      # 루트 레이아웃
│   ├── page.tsx        # 홈페이지
│   └── globals.css     # 전역 스타일
├── components/         # React 컴포넌트
│   ├── ui/            # shadcn/ui 컴포넌트
│   ├── header.tsx     # 헤더 컴포넌트
│   ├── file-upload.tsx    # 파일 업로드
│   ├── merge-options.tsx  # 병합 옵션
│   ├── merge-control.tsx  # 병합 제어
│   ├── progress-tracker.tsx # 진행률 추적
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

### ✅ 병합 옵션
- Cross-fade 길이 조절 (0-5000ms)
- 버퍼 크기 선택 (32KB/64KB/128KB)
- 자동 포맷 변환 옵션

### ✅ 실시간 진행률
- Server-Sent Events (SSE) 연결
- 실시간 진행률 바
- 상세 상태 메시지
- 오류 처리

### ✅ 다크모드
- 시스템 테마 자동 감지
- 부드러운 전환 애니메이션
- 모든 컴포넌트 완전 지원

### ✅ 반응형 디자인
- 모바일/태블릿/데스크톱 지원
- 터치 친화적 인터페이스

## 🔧 개발 명령어

```bash
# 의존성 설치
npm install

# 개발 서버
npm run dev

# 프로덕션 빌드
npm run build

# 프로덕션 실행
npm run start

# 린팅
npm run lint
```

## 🌍 환경 변수

`.env.local` 파일을 생성하여 설정하세요:

```env
# FastAPI 백엔드 URL
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## 🔗 API 연동

FastAPI 백엔드와 완전 호환되는 TypeScript 타입과 API 클라이언트를 제공합니다:

- **파일 업로드**: `POST /api/upload`
- **병합 시작**: `POST /api/merge`
- **진행률 스트림**: `GET /api/events/{task_id}` (SSE)
- **결과 다운로드**: `GET /api/download/{task_id}`
- **상태 조회**: `GET /api/status/{task_id}`
- **정리**: `DELETE /api/cleanup/{task_id}`

## 🔄 Alpine.js에서 마이그레이션

기존 Alpine.js 버전에서 다음과 같이 개선되었습니다:

| 기능 | Alpine.js | Next.js + shadcn/ui |
|------|-----------|---------------------|
| 타입 안전성 | ❌ | ✅ TypeScript |
| 컴포넌트화 | ❌ | ✅ 재사용 가능한 컴포넌트 |
| 상태 관리 | 기본적 | ✅ Zustand 전역 상태 |
| 다크모드 | 수동 구현 | ✅ next-themes 시스템 |
| 빌드 최적화 | ❌ | ✅ Next.js 최적화 |
| 개발 경험 | 기본적 | ✅ 핫 리로드, 타입 체크 |

## 📄 라이센스

이 프로젝트는 부모 프로젝트와 동일한 라이센스를 따릅니다.