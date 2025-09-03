# 🤖 AI MCP A2A - 제로 코스트 AI 에이전트 시스템

> **LangGraph + FastMCP + Docker** 기반의 실시간 AI 에이전트 포트폴리오  
> **완전 무료 인프라**로 구축된 하이브리드 아키텍처 시연

[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.11.3-blue)](https://github.com/jlowin/fastmcp)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.6.2-green)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://www.docker.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.12-yellow)](https://www.python.org/)

## 📺 **데모 사이트**

🚀 **Live Demo**: [https://ai-mcp-a2a-frontend.vercel.app](https://ai-mcp-a2a-frontend.vercel.app)

> **주의**: 백엔드는 로컬에서 동적으로 실행되므로, 데모 접속 시간에 따라 사용 가능 여부가 달라질 수 있습니다.

## 🎯 프로젝트 목표

**도메인 전문가가 아닌 개발 기술 전문가**임을 어필하는 포트폴리오입니다.

- ✅ **LangGraph 기반 AI 에이전트** 워크플로우 설계
- ✅ **FastMCP 서버** 개발 및 통합
- ✅ **Docker 컨테이너화** 및 마이크로서비스 아키텍처
- ✅ **제로 코스트 배포** - 완전 무료 인프라 구축
- ⏳ **A2A 통신** (보류 - 현재 실력 부족으로 추후 진행 예정)

## 🏗️ 시스템 아키텍처

```
🌐 Vercel Frontend (CDN)
    ↓ HTTPS API 호출
🌍 Tunneling Service (고정 URL)
    ↓ 보안 터널 연결
🏠 로컬 Docker Compose
    ├── 🤖 LangGraph 통합 에이전트 (FastAPI)
    ├── 📊 거시경제 MCP 서버 (FastMCP)
    ├── 📈 주식분석 MCP 서버 (FastMCP)
    ├── 📰 네이버뉴스 MCP 서버 (FastMCP)
    ├── 🔍 Tavily 검색 MCP 서버 (FastMCP)
    ├── 💹 키움 API MCP 서버 (FastMCP)
    ├── 🧠 Ollama (로컬 LLM - llama3.1:8b)
    └── 📊 모니터링 & 로깅
```

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

### **인프라 (완전 무료)**

- **Vercel**: 프론트엔드 호스팅 + CDN (무료 - 월 100GB)
- **터널링 서비스**: 보안 터널링 (무료 - 다중 옵션)
- **Docker**: 로컬 컨테이너 오케스트레이션 (무료)
- **Ollama**: 로컬 LLM 서빙 (무료)

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
└── 🐳 docker/               # Docker 설정
```

## 🌟 핵심 기능

### **1. 🤖 LangGraph 에이전트 워크플로우**

- **상태 기반 실행**: 체크포인팅과 지속성 지원
- **다중 MCP 통합**: 6개 전문 MCP 서버 오케스트레이션
- **스트리밍 응답**: 실시간 분석 진행률 전송
- **에러 복구**: 강력한 예외 처리 및 재시도 로직

### **2. 🚀 FastMCP 서버 생태계**

- **모듈화 아키텍처**: 독립적인 마이크로서비스 설계
- **공통 베이스 클래스**: 코드 재사용 및 일관성 확보
- **성능 최적화**: 캐싱, 연결 풀링, 배치 처리
- **모니터링**: 헬스 체크, 메트릭 수집, 로깅

### **3. 💡 하이브리드 배포 전략**

- **프론트엔드**: 글로벌 CDN으로 빠른 접근
- **백엔드**: 로컬 GPU/CPU 자원 활용
- **연결**: 보안 터널로 안전한 통신
- **비용**: 완전 무료 인프라 구축

## 🎨 UI/UX 특징

- **실시간 채팅** 인터페이스
- **분석 진행률** 시각화
- **MCP 서버 상태** 모니터링
- **사용된 서버** 투명성 표시
- **반응형 디자인** (모바일 최적화)

## ⚙️ 로컬 개발 환경

### 필수 요구사항

```bash
# Windows 환경 권장
✅ Docker Desktop 4.0+
✅ Python 3.12+ (uv 패키지 매니저)
✅ Node.js 18+ (npm/pnpm)
✅ Ollama (llama3.1:8b 모델)
✅ Git
```

### 🚀 빠른 시작

```bash
# 1. 저장소 클론
git clone <repository-url>
cd AI_MCP_A2A

# 2. Python 환경 설정
mise use python
uv sync

# 3. 백엔드 실행 (모든 MCP 서버 + 에이전트)
cd docker
docker-compose up --build

# 4. 프론트엔드 실행 (별도 터미널)
cd frontend
npm install
npm run dev
```

## 🔒 보안 및 성능

### **보안 특징**

- Cloudflare 보안 터널링
- CORS 정책 적용
- 입력값 검증 및 sanitization
- Docker 격리 환경

### **시스템 상태**

- MCP 서버 헬스 체크
- Docker 컨테이너 상태
- 터널 연결 상태
- API 응답 시간

### **사용자 피드백**

- 실시간 로딩 상태
- 에러 메시지 표시
- 분석 진행률 표시

## 💼 **기술 어필 포인트**

### **🔧 개발 기술 전문성**

- **FastMCP 프레임워크**: 6개 전문 MCP 서버 개발
- **LangGraph 에이전트**: 상태 기반 AI 워크플로우 설계
- **Docker 마이크로서비스**: 컨테이너 오케스트레이션 및 관리
- **Next.js 15**: 최신 React 기술 스택 활용

### **🏗️ 아키텍처 설계 능력**

- **하이브리드 배포**: 프론트엔드(클라우드) + 백엔드(로컬) 조합
- **제로 코스트 인프라**: 완전 무료 서비스로 프로덕션 환경 구축
- **모듈화 설계**: 재사용 가능한 베이스 클래스 및 미들웨어
- **성능 최적화**: 캐싱, 연결 풀링, 비동기 처리

### **🔒 DevOps 및 운영**

- **자동화 스크립트**: 원클릭 배포 및 환경 구성
- **모니터링 시스템**: 헬스 체크, 메트릭 수집, 로깅
- **보안 터널링**: 안전한 외부 접근 환경 구축
- **CI/CD 파이프라인**: Vercel 자동 배포 설정

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

## 📈 **성과 지표**

### **📊 기술 메트릭**

- **MCP 서버**: 6개 독립 마이크로서비스
- **코드 라인**: ~10,000+ lines (Python + TypeScript)
- **Docker 컨테이너**: 7개 서비스 오케스트레이션
- **API 엔드포인트**: 20+ RESTful APIs
- **응답 시간**: 평균 2-3초 (스트리밍)

### **🏆 기술적 성취**

- ✅ **제로 코스트** 완전 무료 인프라 구축
- ✅ **실시간 스트리밍** AI 에이전트 구현
- ✅ **마이크로서비스** 아키텍처 설계
- ✅ **최신 기술 스택** 활용 (Next.js 15, Python 3.12)
- ✅ **프로덕션 레벨** 코드 품질 및 문서화

## 🤝 **프로젝트 정보**

- **개발 기간**: 2025년 8월 23일 ~ 2025년 9월 3일 (a2a 기술 안정화 후 추가개발 예정)
- **기술 스택**: LangGraph, FastMCP, Docker, Next.js, TypeScript
- **특기 분야**: AI 에이전트, 마이크로서비스, 클라우드 아키텍처
- **개발 철학**: 도메인 전문성 < **개발 기술 전문성**

---

> **🚀 이 프로젝트는 주식/경제 전문가가 아닌 순수 개발 기술력을 어필하기 위해 제작되었습니다.**  
> **💡 핵심은 FastMCP, LangGraph, Docker를 활용한 현대적 AI 시스템 아키텍처입니다.**
