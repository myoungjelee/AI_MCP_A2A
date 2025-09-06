"""
한국 주식 데이터 MCP 서버 (FinanceDataReader 기반)

FinanceDataReader를 통한 한국 주식 데이터 조회 및 분석 기능을 제공하는 MCP 서버입니다.
실제 한국 주식 시장 데이터를 안정적으로 제공합니다.

주요 기능:
- 주식 기본 정보 조회 (현재가, 등락률, 거래량)
- 주식 목록 조회 (KOSPI, KOSDAQ)
- 일봉 차트 데이터 조회
- 등락률/거래량 순위 조회
- 캐싱 및 성능 최적화

개발 기술 어필:
- FastMCP 기반 MCP 서버 구현
- FinanceDataReader를 통한 실제 데이터 조회
- 비동기 데이터 처리 (asyncio)
- 메모리 캐싱 시스템
- 체계적인 에러 처리
- 로깅 및 모니터링
"""

from .client import DataSourceError, FinanceDataReaderClient
from .server import FDRMCPServer

__version__ = "1.0.0"
__all__ = [
    "FinanceDataReaderClient",
    "DataSourceError",
    "FDRMCPServer",
]
