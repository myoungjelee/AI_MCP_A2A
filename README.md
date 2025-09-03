# 🤖 AI MCP A2A - 제로 코스트 AI 에이전트 시스템

> **LangGraph + FastMCP + Docker** 기반의 실시간 AI 에이전트 포트폴리오  
> **완전 무료 인프라**로 구축된 하이브리드 아키텍처 시연

[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.11.3-blue)](https://github.com/jlowin/fastmcp)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.6.2-green)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://www.docker.com/)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-black)](https://vercel.com/)

## 🎯 프로젝트 목표

**도메인 전문가가 아닌 개발 기술 전문가**임을 어필하는 포트폴리오입니다.

- ✅ **LangGraph 기반 AI 에이전트** 워크플로우 설계
- ✅ **FastMCP 서버** 개발 및 통합
- ✅ **Docker 컨테이너화** 및 마이크로서비스 아키텍처
- ✅ **제로 코스트 배포** - 완전 무료 인프라 구축
- ⏳ **A2A 통신** (보류 - 현재 실력 부족으로 추후 진행 예정)

## 🏗️ 시스템 아키텍처

```
🌐 Vercel (프론트엔드)
    ↓ API 호출
🦆 DuckDNS (ai-mcp-a2a-backend.duckdns.org)
    ↓ 도메인 라우팅
☁️ Cloudflare Tunnel (보안 터널)
    ↓ 터널 연결
🏠 로컬 서버 (Docker Compose)
    ├── 🤖 LangGraph 통합 에이전트
    ├── 📊 거시경제 MCP 서버
    ├── 📈 주식분석 MCP 서버
    ├── 📰 네이버뉴스 MCP 서버
    ├── 🔍 Tavily 검색 MCP 서버
    ├── 💹 키움 API MCP 서버
    └── 🧠 Ollama (로컬 LLM)
```

## 🚀 완전 자동화 시작

### 원클릭 시작

```bash
# Windows 시작프로그램에 등록하거나 수동 실행
.\startup.bat
```

### 자동화 프로세스

1. **Ollama 서버** 자동 시작
2. **Docker Desktop** 자동 시작 및 대기
3. **Docker Compose** 모든 MCP 서버 시작
4. **서비스 상태** 자동 확인
5. **Cloudflare Tunnel** 외부 연결 생성

## 💻 기술 스택

### **백엔드 (로컬 Docker)**

- **LangGraph 0.6.2**: AI 에이전트 워크플로우 관리
- **FastMCP 2.11.3**: MCP 서버 개발 프레임워크
- **FastAPI**: REST API 서버
- **Docker Compose**: 마이크로서비스 오케스트레이션
- **Ollama**: 로컬 LLM 서빙

### **프론트엔드 (Vercel)**

- **Next.js 15**: React 프레임워크
- **TypeScript**: 타입 안전성
- **Tailwind CSS**: 모던 UI/UX
- **Vercel**: 무료 배포 및 CDN

### **인프라 (무료)**

- **Vercel**: 프론트엔드 호스팅 (무료)
- **DuckDNS**: 무료 동적 DNS (무료)
- **Cloudflare Tunnel**: 보안 터널링 (무료)
- **Docker**: 로컬 컨테이너 (무료)

## 📂 프로젝트 구조

```
AI_MCP_A2A/
├── 🌐 frontend/              # Next.js 프론트엔드
│   ├── app/                  # App Router
│   ├── components/           # React 컴포넌트
│   └── vercel.json          # Vercel 배포 설정
│
├── 🤖 src/
│   ├── mcp_servers/         # FastMCP 서버들
│   │   ├── base/            # 공통 베이스 클래스
│   │   ├── macroeconomic/   # 거시경제 데이터
│   │   ├── stock_analysis/  # 주식 분석
│   │   ├── naver_news/      # 뉴스 수집
│   │   ├── tavily_search/   # 웹 검색
│   │   └── kiwoom/          # 키움 API
│   │
│   └── la_agents/           # LangGraph 에이전트
│       ├── base/            # 공통 베이스
│       └── integrated_agent/ # 통합 에이전트
│
├── 🐳 docker/               # Docker 설정
├── 📋 startup.bat           # 완전 자동화 스크립트
└── 🔧 docker-compose.yml   # 서비스 오케스트레이션
```

## 🌟 핵심 기능

### **1. LangGraph 에이전트 워크플로우**

- 다중 MCP 서버 통합 관리
- 상태 기반 워크플로우 실행
- 인터럽트 및 에러 핸들링

### **2. FastMCP 서버 생태계**

- 모듈화된 MCP 서버 아키텍처
- 공통 베이스 클래스 및 미들웨어
- 캐싱, 재시도, 모니터링 기능

### **3. 하이브리드 배포 전략**

- 프론트엔드: 글로벌 CDN (Vercel)
- 백엔드: 로컬 고성능 (Docker)
- 연결: 보안 터널 (Cloudflare)

## 🎨 UI/UX 특징

- **실시간 채팅** 인터페이스
- **분석 진행률** 시각화
- **MCP 서버 상태** 모니터링
- **사용된 서버** 투명성 표시
- **반응형 디자인** (모바일 최적화)

## ⚙️ 로컬 개발 환경

### 필수 요구사항

```bash
# Windows 환경
- Docker Desktop
- Python 3.12+
- Node.js 18+
- Ollama
```

### 개발 모드 실행

```bash
# 백엔드 (MCP 서버들)
docker-compose up --build

# 프론트엔드 (개발 서버)
cd frontend
npm install
npm run dev
```

### 환경 변수 설정

```bash
# .env.local (프론트엔드)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
BACKEND_URL=http://integrated_agent:8000
```

## 🔒 보안 및 성능

### **보안 특징**

- Cloudflare 보안 터널링
- CORS 정책 적용
- 입력값 검증 및 sanitization
- Docker 격리 환경

### **성능 최적화**

- Redis 캐싱 (메모리/디스크)
- 연결 풀링 및 재사용
- 비동기 처리 (asyncio)
- 배치 처리 최적화

## 📊 모니터링

### **시스템 상태**

- MCP 서버 헬스 체크
- Docker 컨테이너 상태
- 터널 연결 상태
- API 응답 시간

### **사용자 피드백**

- 실시간 로딩 상태
- 에러 메시지 표시
- 분석 진행률 표시

## 🎯 면접 시연 시나리오

### **원격 시연 준비**

1. **스마트플러그**로 집 컴퓨터 원격 전원 ON
2. **startup.bat** 자동 실행으로 모든 서비스 시작
3. **고정 URL** 접속으로 즉시 데모 가능

### **기술 어필 포인트**

- **제로 코스트 인프라** 구축 능력
- **마이크로서비스** 아키텍처 설계
- **Docker 컨테이너화** 및 오케스트레이션
- **AI 에이전트** 워크플로우 개발
- **보안 터널링** 및 네트워킹

## 🚧 A2A 통신 (보류 사유)

### **현재 상태: 보류**

```
❌ A2A 에이전트 간 통신 구현 미완료
```

### **보류 사유**

1. **기술 안정성**: A2A가 초창기 단계로 API 변경이 빈번함 (며칠마다 버전업)
2. **프로덕션 고려**: 불안정한 기술 스택으로 포트폴리오 구현 시 위험성
3. **학습 효율성**: 안정화된 후 학습이 더 효율적
4. **우선순위**: 현재는 검증된 MCP + LangGraph 기술 어필에 집중

### **향후 계획**

- **A2A 안정화 모니터링**: 버전 업데이트 및 API 변경 추적
- **프로토콜 표준화 대기**: 주요 버전 릴리스 및 안정성 확보 후 적용
- **에이전트 간 통신 구현**: 메시지 패싱 및 협업 워크플로우 개발
- **분산 AI 시스템 확장**: 멀티 에이전트 아키텍처 구현

## 🤝 기술 문의

- **개발자**: [GitHub 프로필]
- **기술 스택**: LangGraph, FastMCP, Docker, Next.js
- **특기 분야**: AI 에이전트, 마이크로서비스, 인프라 자동화

---

**🚀 이 프로젝트는 도메인 지식이 아닌 순수 개발 기술력을 어필하기 위해 제작되었습니다.**
