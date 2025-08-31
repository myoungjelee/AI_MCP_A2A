# Docker 러닝 가이드 - MCP 서버 테스트 과정

## 🎯 **학습 목표**

이 가이드를 통해 **Docker 기초**부터 **MCP 서버 테스트**까지의 전체 과정을 단계별로 학습할 수 있습니다. 실제 프로젝트에서 겪었던 문제들과 해결 방법을 포함합니다.

## 🐳 **Docker 기초 개념**

### **1. Docker란?**

- **컨테이너 기술**: 애플리케이션을 독립적인 환경에 패키징
- **가상화**: OS 레벨의 가상화로 가볍고 빠름
- **일관성**: 개발/테스트/운영 환경의 동일성 보장

### **2. 핵심 개념**

```bash
# 이미지 (Image): 애플리케이션의 템플릿
# 컨테이너 (Container): 이미지로부터 실행되는 인스턴스
# Dockerfile: 이미지를 빌드하기 위한 명령어 모음
# docker-compose.yml: 여러 컨테이너를 관리하는 설정 파일
```

## 🚀 **1단계: Docker 설치 및 환경 설정**

### **Windows에서 Docker Desktop 설치**

```bash
# 1. Docker Desktop 다운로드
# https://www.docker.com/products/docker-desktop/

# 2. 설치 후 시스템 재시작

# 3. Docker 버전 확인
docker --version
docker-compose --version

# 4. Docker 서비스 상태 확인
docker info
```

### **WSL2 설정 (Windows 11)**

```bash
# WSL2가 활성화되어 있는지 확인
wsl --list --verbose

# Docker Desktop에서 WSL2 통합 활성화
# Settings > Resources > WSL Integration
```

## 🔧 **2단계: 프로젝트 Docker 설정**

### **Dockerfile 생성**

```dockerfile
# AI_MCP_A2A/Dockerfile
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 실행 명령
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **docker-compose.yml 생성**

```yaml
# AI_MCP_A2A/docker-compose.yml
version: "3.8"

services:
  # 테스트 클라이언트
  test_client:
    build: .
    container_name: test_client
    volumes:
      - .:/app
    working_dir: /app
    command: python -m src.test.test_integration
    environment:
      - PYTHONPATH=/app
    depends_on:
      - stock_analysis_mcp
      - macroeconomic_mcp
      - financial_analysis_mcp
      - naver_news_mcp
      - tavily_search_mcp
      - kiwoom_mcp

  # 주식 분석 MCP 서버
  stock_analysis_mcp:
    build: .
    container_name: stock_analysis_mcp
    ports:
      - "8052:8052"
    environment:
      - MCP_PORT=8052
      - MCP_HOST=0.0.0.0
    command: python -m src.mcp_servers.stock_analysis.server
    volumes:
      - .:/app

  # 거시경제 분석 MCP 서버
  macroeconomic_mcp:
    build: .
    container_name: macroeconomic_mcp
    ports:
      - "8053:8053"
    environment:
      - MCP_PORT=8053
      - MCP_HOST=0.0.0.0
    command: python -m src.mcp_servers.macroeconomic.server
    volumes:
      - .:/app

  # 재무 분석 MCP 서버
  financial_analysis_mcp:
    build: .
    container_name: financial_analysis_mcp
    ports:
      - "8054:8054"
    environment:
      - MCP_PORT=8054
      - MCP_HOST=0.0.0.0
    command: python -m src.mcp_servers.financial_analysis.server
    volumes:
      - .:/app

  # 네이버 뉴스 MCP 서버
  naver_news_mcp:
    build: .
    container_name: naver_news_mcp
    ports:
      - "8055:8055"
    environment:
      - MCP_PORT=8055
      - MCP_HOST=0.0.0.0
    command: python -m src.mcp_servers.naver_news.server
    volumes:
      - .:/app

  # Tavily 검색 MCP 서버
  tavily_search_mcp:
    build: .
    container_name: tavily_search_mcp
    ports:
      - "8056:8056"
    environment:
      - MCP_PORT=8056
      - MCP_HOST=0.0.0.0
    command: python -m src.mcp_servers.tavily_search.server
    volumes:
      - .:/app

  # 키움증권 MCP 서버
  kiwoom_mcp:
    build: .
    container_name: kiwoom_mcp
    ports:
      - "8057:8057"
    environment:
      - MCP_PORT=8057
      - MCP_HOST=0.0.0.0
    command: python -m src.mcp_servers.kiwoom.server
    volumes:
      - .:/app

networks:
  default:
    name: mcp_network
```

## 🧪 **3단계: Docker 빌드 및 실행**

### **이미지 빌드**

```bash
# 현재 디렉토리에서 Docker 이미지 빌드
docker build -t ai-mcp-a2a .

# 빌드된 이미지 확인
docker images

# 이미지 상세 정보 확인
docker inspect ai-mcp-a2a
```

### **컨테이너 실행**

```bash
# docker-compose로 모든 서비스 실행
docker-compose up --build -d

# 실행 중인 컨테이너 확인
docker ps

# 컨테이너 로그 확인
docker logs test_client
docker logs stock_analysis_mcp
docker logs macroeconomic_mcp
```

## 🚨 **4단계: 실제 겪었던 문제들과 해결 방법**

### **문제 1: mise 설정 파일 신뢰 문제**

```bash
# ❌ 에러: mise configuration file trust issue
# Docker Compose 실행 시 설정 파일을 신뢰할지 묻는 프롬프트

# ✅ 해결 방법: 터미널에서 'a' 입력 또는 "All" 버튼 클릭
# 이는 Windows 환경에서 자주 발생하는 보안 관련 문제
```

### **문제 2: 포트 충돌**

```bash
# ❌ 에러: Port already in use
# Error: listen tcp :8052: bind: address already in use

# ✅ 해결 방법: 포트 사용 중인 프로세스 확인 및 종료
netstat -ano | findstr :8052
taskkill /PID <프로세스ID> /F

# 또는 다른 포트 사용
docker-compose down
# docker-compose.yml에서 포트 변경 후 재실행
```

### **문제 3: 볼륨 마운트 문제**

```bash
# ❌ 에러: Volume mount failed
# Windows에서 경로 문제 발생 가능

# ✅ 해결 방법: 절대 경로 사용 또는 WSL2 경로 사용
volumes:
  - ./:/app  # 상대 경로
  - /d/Python/FastCampus_mcp_a2a_stock_project/AI_MCP_A2A:/app  # 절대 경로
```

## 📊 **5단계: 테스트 과정 및 결과 확인**

### **통합 테스트 실행**

```bash
# 1. 로컬 테스트 (Docker 없이)
uv run python -m src.test.test_integration

# 2. Docker 환경에서 테스트
docker-compose up --build -d
docker logs test_client

# 3. 개별 컨테이너 테스트
docker exec -it stock_analysis_mcp python -m src.test.test_stock_analysis
```

### **테스트 결과 해석**

```bash
# ✅ 성공적인 테스트 결과 예시
=== 주식 분석 시스템 테스트 시작 ===
✅ 도구 목록 조회 성공: 3개 도구
✅ 데이터 트렌드 분석 성공
✅ 통계적 지표 계산 성공
✅ 패턴 인식 성공
=== 주식 분석 시스템 테스트 완료 ===

# ❌ 실패한 테스트 결과 예시
❌ 주식 분석 테스트 실패: 'success' key error
# 이는 응답 구조가 예상과 다를 때 발생
```

## 🔍 **6단계: 디버깅 및 문제 해결**

### **컨테이너 상태 확인**

```bash
# 실행 중인 컨테이너 목록
docker ps

# 모든 컨테이너 (중지된 것 포함)
docker ps -a

# 컨테이너 상세 정보
docker inspect <container_name>

# 컨테이너 리소스 사용량
docker stats
```

### **로그 분석**

```bash
# 실시간 로그 확인
docker logs -f <container_name>

# 마지막 N줄 로그
docker logs --tail 100 <container_name>

# 특정 시간 이후 로그
docker logs --since "2024-01-01T10:00:00" <container_name>
```

### **컨테이너 내부 접근**

```bash
# 실행 중인 컨테이너에 접근
docker exec -it <container_name> /bin/bash

# Python 환경 확인
docker exec -it <container_name> python --version
docker exec -it <container_name> pip list

# 파일 시스템 확인
docker exec -it <container_name> ls -la
```

## 🧹 **7단계: 정리 및 관리**

### **컨테이너 정리**

```bash
# 모든 컨테이너 중지 및 제거
docker-compose down

# 이미지까지 모두 제거
docker-compose down --rmi all

# 사용하지 않는 리소스 정리
docker system prune -a

# 볼륨 정리
docker volume prune
```

### **리소스 모니터링**

```bash
# Docker 시스템 정보
docker system df

# 디스크 사용량
docker system df -v

# 메모리 사용량
docker stats --no-stream
```

## 📈 **8단계: 고급 Docker 기능**

### **멀티 스테이지 빌드**

```dockerfile
# 개발용 이미지
FROM python:3.12-slim as development
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# 프로덕션용 이미지
FROM python:3.12-slim as production
WORKDIR /app
COPY --from=development /app /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **환경별 설정**

```yaml
# docker-compose.override.yml (개발용)
version: '3.8'
services:
  test_client:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    volumes:
      - .:/app
      - /app/__pycache__

# docker-compose.prod.yml (운영용)
version: '3.8'
services:
  test_client:
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

## 🎯 **실습 과제**

### **과제 1: 기본 Docker 명령어 연습**

```bash
# 1. 간단한 Python 애플리케이션 Dockerfile 작성
# 2. 이미지 빌드 및 실행
# 3. 컨테이너 내부에서 파일 수정
# 4. 볼륨 마운트로 데이터 영속성 확인
```

### **과제 2: MCP 서버 Docker화**

```bash
# 1. 각 MCP 서버를 개별 컨테이너로 실행
# 2. 네트워크 연결 확인
# 3. 로그 수집 및 분석
# 4. 성능 모니터링
```

### **과제 3: 문제 해결 시나리오**

```bash
# 1. 포트 충돌 상황 재현 및 해결
# 2. 메모리 부족 상황 처리
# 3. 네트워크 연결 문제 디버깅
# 4. 로그 분석을 통한 문제 진단
```

## 📚 **추가 학습 자료**

### **Docker 공식 문서**

- **Docker Documentation**: https://docs.docker.com/
- **Docker Compose**: https://docs.docker.com/compose/
- **Best Practices**: https://docs.docker.com/develop/dev-best-practices/

### **실습 환경**

- **Play with Docker**: https://labs.play-with-docker.com/
- **Docker Desktop**: 로컬 개발 환경
- **GitHub Codespaces**: 클라우드 개발 환경

### **다음 단계**

- **Kubernetes**: 컨테이너 오케스트레이션
- **Docker Swarm**: 클러스터 관리
- **CI/CD 파이프라인**: 자동화된 배포

## 🎉 **성취 체크리스트**

- [ ] **Docker 설치** 및 기본 환경 설정
- [ ] **Dockerfile 작성** 및 이미지 빌드
- [ ] **docker-compose.yml** 설정 및 서비스 실행
- [ ] **MCP 서버 컨테이너화** 및 테스트
- [ ] **문제 해결** 및 디버깅 과정 경험
- [ ] **로그 분석** 및 성능 모니터링
- [ ] **컨테이너 관리** 및 리소스 정리
- [ ] **고급 Docker 기능** 활용

이제 **Docker를 마스터**하여 **MCP 서버를 효율적으로 컨테이너화**하고 **개발 기술 중심의 포트폴리오**를 완성할 수 있습니다! 🚀
