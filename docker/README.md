# 🐳 AI MCP A2A Docker 실행 가이드

## 📋 개요

이 프로젝트는 Docker를 사용하여 MCP 서버들과 LangGraph 에이전트를 컨테이너화하여 실행합니다.

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP 서버들    │    │  통합 에이전트   │    │  인프라 서비스   │
│                 │    │                 │    │                 │
│ • Macroeconomic │    │ • LangGraph     │    │ • Redis         │
│ • Financial     │◄──►│ • HTTP API      │◄──►│ • PostgreSQL    │
│ • Stock         │    │ • 워크플로우     │    │ • Prometheus    │
│ • News          │    │ • 의사결정      │    │ • Grafana       │
│ • Search        │    │                 │    │                 │
│ • Kiwoom        │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 빠른 시작

### 1. 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성하고 필요한 API 키들을 설정하세요:

```bash
# API Keys
ECOS_API_KEY=your_ecos_api_key
DART_API_KEY=your_dart_api_key
FRED_API_KEY=your_fred_api_key
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
TAVILY_API_KEY=your_tavily_api_key
KIWOOM_APP_KEY=your_kiwoom_app_key
KIWOOM_APP_SECRET=your_kiwoom_app_secret
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 2. Docker 이미지 빌드

#### Windows (PowerShell)

```powershell
cd docker/scripts
.\build.ps1
```

#### Linux/Mac (Bash)

```bash
cd docker/scripts
chmod +x build.sh
./build.sh
```

### 3. 서비스 시작

#### Windows (PowerShell)

```powershell
cd docker/scripts
.\start.ps1
```

#### Linux/Mac (Bash)

```bash
cd docker/scripts
chmod +x start.sh
./start.sh
```

### 4. 서비스 중지

#### Windows (PowerShell)

```powershell
cd docker/scripts
.\stop.ps1
```

#### Linux/Mac (Bash)

```bash
cd docker/scripts
chmod +x stop.sh
./stop.sh
```

## 🌐 서비스 접속 정보

| 서비스            | URL                        | 설명                            |
| ----------------- | -------------------------- | ------------------------------- |
| 통합 에이전트 API | http://localhost:8000      | LangGraph 에이전트 HTTP API     |
| API 문서          | http://localhost:8000/docs | FastAPI 자동 생성 문서          |
| Grafana           | http://localhost:3000      | 모니터링 대시보드 (admin/admin) |
| Prometheus        | http://localhost:9090      | 메트릭 수집 및 조회             |
| Redis             | localhost:6379             | 캐싱 및 세션 저장               |
| PostgreSQL        | localhost:5432             | 데이터베이스                    |

## 📊 MCP 서버 포트

| 서비스                 | 포트 | 설명                 |
| ---------------------- | ---- | -------------------- |
| Macroeconomic MCP      | 8042 | 거시경제 데이터 처리 |
| Financial Analysis MCP | 8041 | 재무 분석            |
| Stock Analysis MCP     | 8052 | 주식 분석            |
| Naver News MCP         | 8051 | 뉴스 수집            |
| Tavily Search MCP      | 8053 | 검색                 |
| Kiwoom MCP             | 8030 | 키움 API 연동        |

## 🔧 수동 실행

### Docker Compose 직접 사용

```bash
# 모든 서비스 빌드
docker-compose build

# 서비스 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f [서비스명]

# 서비스 중지
docker-compose down
```

### 개별 서비스 실행

```bash
# 특정 MCP 서버만 실행
docker-compose up -d macroeconomic_mcp

# 에이전트만 실행
docker-compose up -d integrated_agent

# 인프라 서비스만 실행
docker-compose up -d redis postgres
```

## 📝 로그 확인

```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f integrated_agent
docker-compose logs -f macroeconomic_mcp

# 에러 로그만
docker-compose logs --tail=100 | grep ERROR
```

## 🐛 문제 해결

### 1. 포트 충돌

포트가 이미 사용 중인 경우:

```bash
# 포트 사용 확인
netstat -an | findstr :8000  # Windows
lsof -i :8000               # Linux/Mac

# 다른 포트로 변경 (docker-compose.yml 수정)
```

### 2. 메모리 부족

Docker Desktop 메모리 설정을 늘리세요:

- Docker Desktop → Settings → Resources → Memory: 4GB 이상

### 3. API 키 오류

`.env` 파일의 API 키가 올바른지 확인:

```bash
# 환경 변수 확인
docker-compose exec integrated_agent env | grep API_KEY
```

### 4. 네트워크 문제

컨테이너 간 통신 문제:

```bash
# 네트워크 확인
docker network ls
docker network inspect ai_mcp_network

# 컨테이너 재시작
docker-compose restart
```

## 🔄 개발 모드

개발 중 코드 변경사항을 즉시 반영하려면:

```bash
# 볼륨 마운트로 소스 코드 변경 실시간 반영
docker-compose up -d --build
```

## 📈 모니터링

### Grafana 대시보드

1. http://localhost:3000 접속
2. 로그인: admin/admin
3. 데이터 소스 추가: Prometheus (http://prometheus:9090)
4. 대시보드 임포트

### Prometheus 메트릭

- MCP 서버 응답 시간
- 에이전트 실행 통계
- 에러율 및 성공률
- 리소스 사용량

## 🧹 정리

### 완전 정리 (모든 데이터 삭제)

```bash
# 컨테이너, 볼륨, 이미지 모두 삭제
docker-compose down -v --rmi all

# Docker 시스템 정리
docker system prune -a --volumes
```

### 부분 정리

```bash
# 컨테이너만 중지
docker-compose down

# 볼륨 유지하면서 컨테이너만 삭제
docker-compose down --remove-orphans
```

## 📚 추가 정보

- [Docker Compose 문서](https://docs.docker.com/compose/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [LangGraph 문서](https://langchain-ai.github.io/langgraph/)
- [MCP 프로토콜](https://modelcontextprotocol.io/)
