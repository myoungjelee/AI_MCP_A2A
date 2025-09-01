#!/usr/bin/env python3
"""
ECOS API 응답 디버깅 스크립트
"""

import json
import os

import requests
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


def debug_ecos_api():
    """ECOS API 응답을 디버깅합니다."""
    print("🔍 ECOS API 응답 디버깅 시작")

    # API 키 확인
    api_key = os.getenv("ECOS_API_KEY")
    if not api_key:
        print("❌ ECOS_API_KEY가 설정되지 않았습니다")
        print("💡 .env 파일을 확인해주세요")
        return

    print(f"✅ ECOS API Key: {api_key[:10]}...")

    # ECOS API 호출
    base_url = "https://ecos.bok.or.kr/api"

    # 여러 지표와 날짜 형식으로 테스트
    test_cases = [
        {
            "name": "KOSPI (연간)",
            "indicator": "901Y009",
            "start_date": "2020",
            "end_date": "2024",
            "cycle": "A",  # 연간
        },
        {
            "name": "KOSPI (월간)",
            "indicator": "901Y009",
            "start_date": "202401",
            "end_date": "202412",
            "cycle": "M",  # 월간
        },
        {
            "name": "GDP (연간)",
            "indicator": "200Y001",
            "start_date": "2020",
            "end_date": "2024",
            "cycle": "A",  # 연간
        },
    ]

    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"🧪 테스트: {test_case['name']}")
        print(f"{'='*60}")

        url = f"{base_url}/StatisticSearch/{api_key}/json/kr/1/1000/{test_case['indicator']}/{test_case['cycle']}/{test_case['start_date']}/{test_case['end_date']}"

        print(f"📡 API 호출 URL: {url}")

        try:
            response = requests.get(url, timeout=30)
            print(f"📊 HTTP 상태 코드: {response.status_code}")

            if response.status_code == 200:
                print("✅ API 호출 성공!")

                # 응답 내용 확인
                content = response.text
                print(f"📄 응답 길이: {len(content)} 문자")
                print(f"📄 응답 내용 (처음 300자): {content[:300]}")

                # JSON 파싱 시도
                try:
                    data = response.json()
                    print("✅ JSON 파싱 성공!")

                    # StatisticSearch 키 확인
                    if "StatisticSearch" in data:
                        print("✅ StatisticSearch 키 발견!")
                        search_data = data["StatisticSearch"]
                        if "row" in search_data:
                            rows = search_data["row"]
                            print(f"📊 데이터 행 수: {len(rows)}")
                            if rows:
                                print(
                                    f"📊 첫 번째 데이터: {json.dumps(rows[0], indent=2, ensure_ascii=False)}"
                                )
                        else:
                            print(
                                f"📊 StatisticSearch 구조: {json.dumps(search_data, indent=2, ensure_ascii=False)[:500]}"
                            )
                    elif "RESULT" in data:
                        result = data["RESULT"]
                        print(
                            f"❌ API 오류: {result.get('CODE', 'UNKNOWN')} - {result.get('MESSAGE', '알 수 없는 오류')}"
                        )
                    else:
                        print(f"📊 사용 가능한 키들: {list(data.keys())}")

                except json.JSONDecodeError as e:
                    print(f"❌ JSON 파싱 실패: {e}")
                    print(f"📄 원본 응답: {content}")
            else:
                print(f"❌ API 호출 실패: {response.status_code}")
                print(f"📄 에러 응답: {response.text}")

        except Exception as e:
            print(f"❌ 요청 실패: {e}")


if __name__ == "__main__":
    debug_ecos_api()
