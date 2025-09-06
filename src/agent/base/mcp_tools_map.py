from __future__ import annotations

from typing import List

# 서버 → 허용 툴 목록 (실제 MCP list_tools 결과와 일치해야 함)
SERVER_TOOLS_ALLOWLIST: dict[str, List[str]] = {
    "financedatareader": [
        "get_stock_basic_info",
        "get_stock_info",
        "get_stock_list",
        "get_daily_chart",
        "search_stock_by_name",
        "get_market_overview",
        "get_market_status",
    ],
    "stock_analysis": [
        "analyze_data_trends",
        "calculate_statistical_indicators",
        "perform_pattern_recognition",
    ],
    "financial_analysis": [
        "get_financial_data",
        "calculate_financial_ratios",
        "perform_dcf_valuation",
        "generate_investment_report",
    ],
    "macroeconomic": [
        "collect_data",
        "process_data_batch",
        "analyze_data_trends",
    ],
    "naver_news": ["search_news_articles", "get_stock_news"],
    "tavily_search": ["search_web", "search_news", "search_finance"],
}


def select_servers_for_collection(question: str) -> List[str]:
    q = (question or "").lower()
    selected: List[str] = []

    if any(w in q for w in ["주식", "종목", "차트", "기술분석"]):
        selected.extend(["stock_analysis", "financedatareader"])

    if any(w in q for w in ["재무", "가치평가", "dcf", "밸류에이션", "재무제표"]):
        selected.append("financial_analysis")

    if any(w in q for w in ["경기", "거시", "물가", "인플레이션", "실업", "금리"]):
        selected.append("macroeconomic")

    if any(w in q for w in ["뉴스", "헤드라인", "기사", "이슈"]):
        selected.extend(["naver_news", "tavily_search"])

    # 중복 제거(순서 유지)
    seen, deduped = set(), []
    for s in selected:
        if s not in seen:
            deduped.append(s)
            seen.add(s)
    return deduped


def select_tools_for_server(server: str, question: str) -> List[str]:
    q = (question or "").lower()
    tools: List[str] = []

    if server == "financedatareader":
        if any(w in q for w in ["주식", "종목", "가격"]):
            tools.extend(["get_stock_basic_info", "get_stock_info"])
        if "차트" in q:
            tools.append("get_daily_chart")
        if any(w in q for w in ["시장", "상태"]):
            tools.append("get_market_status")
        if not tools:
            tools = ["get_market_overview"]

    elif server == "stock_analysis":
        tools = ["analyze_data_trends"]

    elif server == "financial_analysis":
        tools = ["get_financial_data"]

    elif server == "macroeconomic":
        tools = ["collect_data"]

    elif server == "naver_news":
        if any(w in q for w in ["종목", "기업", "회사"]):
            tools.append("get_stock_news")
        else:
            tools.append("search_news_articles")

    elif server == "tavily_search":
        if "뉴스" in q:
            tools.append("search_news")
        elif "증권" in q or "주가" in q:
            tools.append("search_finance")
        else:
            tools.append("search_web")

    # allowlist 필터 적용
    allow = set(SERVER_TOOLS_ALLOWLIST.get(server, []))
    tools = [t for t in tools if t in allow] or list(allow)[:1]

    # 중복 제거
    seen, deduped = set(), []
    for t in tools:
        if t not in seen:
            deduped.append(t)
            seen.add(t)
    return deduped
