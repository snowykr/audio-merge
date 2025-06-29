#!/bin/bash

# Audio Merge 개발 서버 시작 스크립트
# Next.js + FastAPI 동시 실행

echo "🚀 Audio Merge 개발 환경 시작 중..."
echo ""
echo "Next.js Frontend: http://localhost:3000"
echo "FastAPI Backend:  http://localhost:8000/docs"
echo ""
echo "종료하려면 Ctrl+C를 눌러주세요."
echo ""

# 현재 디렉토리가 frontend인지 확인
if [ ! -f "package.json" ]; then
    echo "❌ 오류: frontend 디렉토리에서 실행해주세요."
    exit 1
fi

# FastAPI 백엔드 디렉토리 확인
if [ ! -d "../backend" ]; then
    echo "❌ 오류: 백엔드 디렉토리를 찾을 수 없습니다."
    echo "   경로: ../backend 확인해주세요."
    exit 1
fi

# Python 가상환경 확인 (필수)
if [ -f "../.venv/bin/activate" ]; then
    echo "✅ Python 가상환경 발견: ../.venv"
    echo "   가상환경을 활성화합니다."
else
    echo "❌ 오류: Python 가상환경을 찾을 수 없습니다."
    echo "   경로: ../.venv/bin/activate"
    echo "   먼저 가상환경을 생성하고 의존성을 설치해주세요:"
    echo "   cd .. && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 개발 서버 시작
npm run dev:all