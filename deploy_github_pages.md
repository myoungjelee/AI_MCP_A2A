# 🌐 GitHub Pages 배포 가이드

## 🎯 목표

- 고정 URL로 프론트엔드 배포
- 백엔드는 로컬에서 ngrok으로 터널링
- 면접용 안정적인 접속 환경

---

## 📋 배포 방법 선택

### 방법 1: Vercel (추천)

```bash
cd frontend
npx vercel --prod
```

- URL 예시: `https://ai-mcp-a2a.vercel.app`
- 자동 배포 + 커스텀 도메인 가능

### 방법 2: GitHub Pages

```bash
cd frontend
npm run build
npm install -g gh-pages
npx gh-pages -d out
```

- URL 예시: `https://username.github.io/ai-mcp-a2a`

### 방법 3: Netlify

```bash
cd frontend
npm run build
npx netlify deploy --prod --dir=out
```

- URL 예시: `https://ai-mcp-a2a.netlify.app`

---

## 🔧 프론트엔드 수정사항

### 백엔드 URL 환경변수 설정

```javascript
// frontend/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    BACKEND_URL: process.env.BACKEND_URL || "http://localhost:8000",
  },
  output: "export", // 정적 사이트 생성
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
```

### API 호출 수정

```javascript
// frontend/app/page.tsx
const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
const response = await fetch(`${backendUrl}/analyze/stream`, {
```

---

## 🎯 면접 시연 시나리오

### 1. 사전 준비 (1회)

1. GitHub Pages 배포: `https://username.github.io/ai-mcp-a2a`
2. 백엔드 ngrok 스크립트 준비

### 2. 면접 당일

1. 로컬에서 백엔드 실행
2. ngrok으로 백엔드만 터널링: `ngrok http 8000`
3. 환경변수로 백엔드 URL 설정
4. 고정 프론트엔드 URL로 접속

### 3. 장점

- ✅ 고정 URL (면접관에게 미리 전달 가능)
- ✅ 전세계 접속 가능
- ✅ HTTPS 자동 제공
- ✅ 무료
- ✅ 전문적 어필
