# Cloudflare Tunnel 설정 가이드

## 🚀 **설정 순서**

### 1. **Cloudflared 설치**

```bash
# Windows (PowerShell)
winget install --id Cloudflare.cloudflared

# 또는 수동 다운로드
# https://github.com/cloudflare/cloudflared/releases
```

### 2. **Cloudflare 로그인**

```bash
cloudflared tunnel login
```

### 3. **터널 생성**

```bash
cloudflared tunnel create ai-mcp-a2a-tunnel
```

### 4. **DNS 설정**

```bash
# 자동 DNS 설정 (권장)
cloudflared tunnel route dns ai-mcp-a2a-tunnel [YOUR_DOMAIN.eu.org]

# 또는 수동 설정
# Cloudflare 대시보드에서 CNAME 레코드 추가:
# Name: [YOUR_DOMAIN.eu.org]
# Target: [TUNNEL_ID].cfargotunnel.com
```

### 5. **설정 파일 수정**

`.cloudflared/config.yml` 파일에서 `[YOUR_DOMAIN.eu.org]`를 실제 도메인으로 변경

### 6. **터널 실행**

```bash
# 수동 실행
cloudflared tunnel run ai-mcp-a2a-tunnel

# 또는 startup.bat 사용
startup.bat
```

## 📋 **설정 파일 구조**

```
.cloudflared/
├── config.yml                    # 터널 설정
├── ai-mcp-a2a-tunnel.json       # 터널 인증서 (자동 생성)
└── cloudflared.log              # 로그 파일
```

## 🔧 **환경 변수 설정**

### Frontend (Vercel)

```bash
NEXT_PUBLIC_API_URL=https://[YOUR_DOMAIN.eu.org]
NEXT_PUBLIC_WS_URL=wss://[YOUR_DOMAIN.eu.org]
```

### Backend

```bash
CORS_ORIGINS=https://ai-mcp-a2a.vercel.app,https://[YOUR_DOMAIN.eu.org]
```

## 🧪 **테스트**

### 1. **Health Check**

```bash
curl https://[YOUR_DOMAIN.eu.org]/health
```

### 2. **API 테스트**

```bash
curl https://[YOUR_DOMAIN.eu.org]/api/status
```

### 3. **MCP 서버 테스트**

```bash
curl https://[YOUR_DOMAIN.eu.org]/mcp/health
```

## 🚨 **문제 해결**

### 터널이 시작되지 않는 경우

```bash
# 터널 상태 확인
cloudflared tunnel list

# 로그 확인
tail -f .cloudflared/cloudflared.log

# 터널 재생성
cloudflared tunnel delete ai-mcp-a2a-tunnel
cloudflared tunnel create ai-mcp-a2a-tunnel
```

### DNS 전파 확인

```bash
# DNS 확인
nslookup [YOUR_DOMAIN.eu.org]

# 터널 상태 확인
cloudflared tunnel info ai-mcp-a2a-tunnel
```

## 📊 **모니터링**

### Cloudflare 대시보드

- https://dash.cloudflare.com/
- Zero Trust > Access > Tunnels

### 로그 모니터링

```bash
# 실시간 로그
tail -f .cloudflared/cloudflared.log

# 에러만 필터링
grep -i error .cloudflared/cloudflared.log
```

## 🔒 **보안 설정**

### 1. **Access Policy 설정** (선택사항)

```bash
# Cloudflare 대시보드에서 Access Policy 생성
# 특정 사용자만 접근 가능하도록 설정
```

### 2. **Rate Limiting**

```bash
# Cloudflare 대시보드에서 Rate Limiting 설정
# API 남용 방지
```

## 📈 **성능 최적화**

### 1. **캐싱 설정**

- Cloudflare 대시보드에서 Page Rules 설정
- 정적 리소스 캐싱

### 2. **압축 설정**

- Gzip/Brotli 압축 활성화
- 대역폭 절약

## 🎯 **완료 체크리스트**

- [ ] Cloudflared 설치 완료
- [ ] Cloudflare 로그인 완료
- [ ] 터널 생성 완료
- [ ] DNS 설정 완료
- [ ] 설정 파일 수정 완료
- [ ] 터널 실행 테스트 완료
- [ ] Health Check 통과
- [ ] API 테스트 통과
- [ ] Frontend 연결 테스트 완료
