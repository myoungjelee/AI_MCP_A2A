"""
Naver News MCP Server

네이버 뉴스 수집 및 감정 분석에 특화된 MCP 서버로, 다음 기능을 제공합니다:
- 네이버 뉴스 검색 및 수집
- 뉴스 감정 분석
- 키워드 트렌드 분석
- 주식 관련 뉴스 필터링
- 시장 임팩트 평가
"""

from .client import NewsClient
from .server import NaverNewsMCPServer

__all__ = ["NewsClient", "NaverNewsMCPServer"]
