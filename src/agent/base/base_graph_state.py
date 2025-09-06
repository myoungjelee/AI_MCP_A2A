"""
LangGraph 에이전트의 기본 상태 클래스 정의.

이 모듈은 모든 LangGraph 에이전트가 사용하는 기본 상태 스키마를 정의합니다.
상태는 TypedDict로 정의되며, 노드 간 데이터 전달에 사용됩니다.
"""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class BaseGraphInputState(TypedDict):
    """
    LangGraph 워크플로우의 기본 입력 상태 스키마.
    """

    messages: Annotated[list[BaseMessage], add_messages]


class BaseGraphState(BaseGraphInputState):
    """
    LangGraph 워크플로우의 기본 상태 스키마.

    모든 LangGraph 에이전트의 상태는 이 클래스를 확장하여 사용합니다.
    노드 간 데이터 흐름을 관리하며, 메시지 히스토리를 유지합니다.
    """
