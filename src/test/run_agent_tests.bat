@echo off
REM AI MCP A2A 에이전트 테스트 실행 스크립트 (Windows)

echo 🚀 AI MCP A2A 에이전트 테스트 시작
echo ==================================

REM Python 경로 설정
set PYTHONPATH=%PYTHONPATH%;%~dp0..

REM 테스트 실행
echo.
echo 🔍 Analysis Agent 테스트...
python test_analysis_agent.py

echo.
echo 📊 Data Collector Agent 테스트...
python test_data_collector_agent.py

echo.
echo 💼 Portfolio Agent 테스트...
python test_portfolio_agent.py

echo.
echo 👑 Supervisor Agent 테스트...
python test_supervisor_agent.py

echo.
echo 🚀 모든 에이전트 통합 테스트...
python test_all_agents.py

echo.
echo ✅ 모든 테스트 완료!
pause
