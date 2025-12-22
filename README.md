# 🤖 AI MCP A2A - 투자 분석 통합 AI 에이전트

> **LangGraph + FastMCP + Docker + Cloudflare** 기반의 실무형 AI 에이전트 시스템

[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.11.3-blue)](https://github.com/jlowin/fastmcp)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.6.2-green)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://www.docker.com/)
[![Cloudflare](https://img.shields.io/badge/Cloudflare-Tunnel-orange)](https://www.cloudflare.com/)

---

## 📺 Demo & Links

- 🔗 **Live Demo**: [ai-mcp-a2a.vercel.app](https://ai-mcp-a2a.vercel.app)
- 🎥 **Demo Video**: [시연 영상 보기](https://drive.google.com/file/d/1fmHmhe23Qn6hXvnIRCFPeBGAopsgko-k/view?usp=sharing)
- 🐙 **GitHub**: [github.com/myoungjelee/AI_MCP_A2A](https://github.com/myoungjelee/AI_MCP_A2A)

---

## 🎯 프로젝트 개요

**AI MCP A2A**는 Model Context Protocol(MCP)과 LangGraph를 기반으로 한 투자 분석 통합 AI 에이전트입니다.

단순한 도메인 지식 습득이 아닌, **개발 기술 역량을 증명**하기 위해 최신 기술 스택(FastMCP, LangGraph, Docker, Ollama 등)을 직접 구현하고 통합하여 **실무 수준의 아키텍처 설계 및 운영 능력**을 보여주는 것을 목표로 했습니다.

> **Why NOT A2A (Agent-to-Agent)?**  
> A2A 통신은 아직 기술 성숙도가 낮고 API 변동이 잦아 실무 안정성이 떨어진다고 판단했습니다.  
> 따라서 A2A는 보류하고, **안정적인 MCP + LangGraph 아키텍처**에 집중해 포트폴리오를 완성했습니다.  
> 향후 기술이 안정화되면 A2A를 도입해 에이전트 간 협업 워크플로우까지 확장할 계획입니다.

---

## 🛠 기술 스택

### 🔹 백엔드

- **Python 3.12** – 최신 안정 버전
- **FastMCP** – MCP 서버 개발 프레임워크
- **LangGraph** – AI 에이전트 오케스트레이션
- **FastAPI** – 비동기 REST API 서버
- **Ollama** – 로컬 LLM 서빙 (GPT-OSS 20B)
- **Docker Compose** – 멀티컨테이너 오케스트레이션

### 🔹 프론트엔드 (AI Assisted Coding)

- **Next.js 15 (App Router)** – 현대적 풀스택 프레임워크
- **TypeScript 5** – 정적 타입 안정성
- **Tailwind CSS 3** – 반응형 UI/UX
- **Vercel** – 글로벌 엣지 네트워크 기반 자동 배포 (Always-on Demo)

### 🔹 인프라 & 환경 관리

- **mise** – Python, Node.js, Yarn, uv 통합 환경 관리
- **uv** – Python 패키지 관리
- **Cloudflare Tunnel** – 로컬 백엔드의 안전한 HTTPS 노출
- **Porkbun** – 커스텀 도메인 구매 및 관리

---

## 🔐 보안 및 배포 전략 (의사결정 과정)

1. **초기: ngrok 임시 터널**
   - 빠르게 열 수 있지만, 매번 도메인이 바뀌고 포트 포워딩 구조라 보안·운영 리스크가 큼.
2. **시도: eu.org 무료 도메인**
   - 비용은 없지만 승인까지 시간이 오래 걸리고, 실제 프로젝트 일정에 맞추기 어려워 실사용 실패.
3. **최종 결정: Porkbun 도메인 + Cloudflare Tunnel**
   - 포크번에서 커스텀 도메인 직접 구매.
   - Cloudflare Tunnel과 연동해 고정 HTTPS 엔드포인트 구성.
   - 개인 GPU 워크스테이션(Ollama + Docker Compose 백엔드)와 연결해, 필요 시 외부에서 접속 가능한 **On-Demand 시연 서버**로 운용.

---

## 🏗 아키텍처 구성

### 📡 MCP 서버 (FastMCP 기반)

| 서버 이름              | 역할                    | 데이터 소스                          |
| ---------------------- | ----------------------- | ------------------------------------ |
| **Macroeconomic**      | 거시경제 데이터 수집    | 한국은행 ECOS API, 미국 FRED API     |
| **Stock Analysis**     | 주가/기술적 지표 분석   | 내부 분석 알고리즘                   |
| **Naver News**         | 증권/경제 뉴스 크롤링   | 네이버 검색 OpenAPI                  |
| **Tavily Search**      | 실시간 웹 검색          | Tavily API                           |
| **FinanceDataReader**  | 상장 종목 시세 조회     | FinanceDataReader 라이브러리         |
| **Financial Analysis** | 기업 재무제표·지표 분석 | DART 전자공시 API, 한국은행 ECOS API |

### 🤖 LangGraph 에이전트

- **Integrated Agent** – 모든 MCP 서버를 통합 관리.
- 투자 질문 의도 분석 → 필요한 MCP 호출 → 데이터 통합 → 최종 답변 생성.

---

## 🚀 주요 기능

1. **MCP 서버 통합**

   - 로깅, 에러 처리, 헬스체크, 모니터링.
   - 캐싱·재시도·배치 처리로 성능 최적화.

2. **LangGraph 에이전트 워크플로우**

   - 상태 관리(State Machine).
   - MCP 서버 호출 순서 및 데이터 흐름 제어.
   - 예외 처리 및 인터럽트 관리.

3. **프론트엔드 인터페이스**
   - Next.js 기반 실시간 채팅형 UI.
   - 분석 진행률·MCP 상태 시각화.
   - Vercel 배포로 안정적인 Live Demo 제공.

---

## 📊 기술적 성과

- **아키텍처**
  - 헥사고날 구조, 의존성 역전(DIP), 단일 책임 원칙(SRP) 적용.
- **성능 최적화**
  - `asyncio` 기반 비동기 처리, 배치 처리 설계.
- **코드 품질**
  - 타입 힌트, 계층적 예외 처리, 구조화 로깅.
- **배포 전략**
  - 프론트엔드 → Vercel 자동 배포(고정 URL).
  - 백엔드 → Docker Compose 로컬 실행 + Porkbun 도메인 + Cloudflare Tunnel 기반 **On-Demand 외부 시연**.
  - ngrok 터널링은 보안·운영 리스크로 인해 임시 테스트 후 폐기.
  - eu.org 무료 도메인 시도는 승인 지연으로 실사용 실패, 대신 유료 도메인 구매로 전환.

# 🚀 빠른 시작 (Docker Compose)

### 전체 시스템 실행

Docker Desktop이 설치되어 있다면, 다음 한 줄로 **6개 MCP 서버 + LangGraph Agent + Redis + PostgreSQL**을 모두 띄울 수 있습니다.

docker compose up -d

### Windows (자동 실행 스크립트)

`startup.bat`을 실행하면 다음이 자동으로 처리됩니다.

.\startup.bat

- ✅ Ollama 로컬 LLM 서버 시작 (`gpt-oss:20b`)
- ✅ Docker Compose 서비스 헬스체크
- ✅ Cloudflare Tunnel 연결 및 외부 공개 URL 활성화
