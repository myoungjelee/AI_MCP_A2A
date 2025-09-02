# 🎯 무료 최선 방법

## 1️⃣ 사전 설정 (1회만)

### Vercel 배포

```bash
cd frontend
npx vercel --prod
```

- 결과: `https://ai-mcp-a2a.vercel.app` (고정 URL)

### 프론트엔드 코드 수정

```javascript
// frontend/app/page.tsx
// 하드코딩된 localhost:8000을 환경변수로 변경
const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
const response = await fetch(`${backendUrl}/analyze/stream`, {
```

---

## 2️⃣ 면접 당일

### 단계 1: 백엔드 실행

```bash
docker-compose up -d
ollama serve
```

### 단계 2: 백엔드 터널링

```bash
ngrok http 8000
```

- 결과: `https://abc123.ngrok.io` (매번 다름)

### 단계 3: 환경변수 설정

```bash
# Vercel에서 환경변수 설정
NEXT_PUBLIC_BACKEND_URL=https://abc123.ngrok.io
```

---

## 3️⃣ 완성!

- **프론트엔드**: `https://ai-mcp-a2a.vercel.app` (고정)
- **백엔드**: `https://abc123.ngrok.io` (동적)

## ✅ 장점

- 완전 무료
- 고정 프론트엔드 URL
- 전세계 접속 가능
- 설정 5분
