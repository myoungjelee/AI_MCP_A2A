"""
키움증권 API 타입 정의

180개 API ID와 카테고리를 Enum으로 정의하여 타입 안전성과 자동완성을 지원합니다.
"""

from enum import Enum


class KiwoomCategory(str, Enum):
    """API 카테고리 열거형"""

    AUTH = "auth"  # OAuth 인증
    STKINFO = "stkinfo"  # 종목정보
    MRKCOND = "mrkcond"  # 시세
    FRGNISTT = "frgnistt"  # 기관/외국인
    SECT = "sect"  # 업종
    SHSA = "shsa"  # 공매도
    RKINFO = "rkinfo"  # 순위정보
    CHART = "chart"  # 차트
    SLB = "slb"  # 대차거래
    ACNT = "acnt"  # 계좌
    ELW = "elw"  # ELW
    ETF = "etf"  # ETF
    THME = "thme"  # 테마
    ORDR = "ordr"  # 주문
    CRDORDR = "crdordr"  # 신용주문
    WEBSOCKET = "websocket"  # WebSocket


class KiwoomAPIID(str, Enum):
    """키움 API ID 열거형 (총 180개)"""

    # ===== OAuth 인증 (2개) =====
    TOKEN_ISSUE = "au10001"  # 접근토큰 발급
    TOKEN_REVOKE = "au10002"  # 접근토큰 폐기

    # ===== 종목정보 (28개) =====
    STOCK_BASIC_INFO = "ka10001"  # 주식기본정보요청
    STOCK_TRADING_MEMBER = "ka10002"  # 주식거래원요청
    STOCK_EXECUTION_INFO = "ka10003"  # 체결정보요청
    CREDIT_TRADE_TREND = "ka10013"  # 신용매매동향요청
    DAILY_TRADE_DETAIL = "ka10015"  # 일별거래상세요청
    NEW_HIGH_LOW = "ka10016"  # 신고저가요청
    UPPER_LOWER_LIMIT = "ka10017"  # 상하한가요청
    HIGH_LOW_APPROACH = "ka10018"  # 고저가근접요청
    PRICE_SURGE_DROP = "ka10019"  # 가격급등락요청
    VOLUME_RENEWAL = "ka10024"  # 거래량갱신요청
    OFFER_CONCENTRATION = "ka10025"  # 매물대집중요청
    HIGH_LOW_PER = "ka10026"  # 고저PER요청
    OPEN_PRICE_COMPARE = "ka10028"  # 시가대비등락률요청
    TRADER_OFFER_ANALYSIS = "ka10043"  # 거래원매물대분석요청
    TRADER_INSTANT_VOLUME = "ka10052"  # 거래원순간거래량요청
    VOLATILITY_INTERRUPT = "ka10054"  # 변동성완화장치발동종목요청
    TODAY_YESTERDAY_VOLUME = "ka10055"  # 당일전일체결량요청
    INVESTOR_DAILY_TRADE = "ka10058"  # 투자자별일별매매종목요청
    STOCK_INVESTOR_BY_INST = "ka10059"  # 종목별투자자기관별요청
    STOCK_INVESTOR_BY_INST_SUM = "ka10061"  # 종목별투자자기관별합계요청
    TODAY_YESTERDAY_EXECUTION = "ka10084"  # 당일전일체결요청
    WATCHLIST_INFO = "ka10095"  # 관심종목정보요청
    STOCK_LIST = "ka10099"  # 종목정보 리스트
    STOCK_INFO = "ka10100"  # 종목정보 조회
    SECTOR_CODE_LIST = "ka10101"  # 업종코드 리스트
    MEMBER_LIST = "ka10102"  # 회원사 리스트
    PROGRAM_NET_BUY_TOP50 = "ka90003"  # 프로그램순매수상위50요청
    STOCK_PROGRAM_TRADE = "ka90004"  # 종목별프로그램매매현황요청
    CREDIT_AVAILABLE_STOCK = "kt20016"  # 신용융자 가능종목요청
    CREDIT_AVAILABLE_INQUIRY = "kt20017"  # 신용융자 가능문의

    # ===== 시세 (21개) =====
    STOCK_ORDERBOOK = "ka10004"  # 주식호가요청
    STOCK_DAILY_WEEKLY_MONTHLY = "ka10005"  # 주식일주월시분요청
    STOCK_MINUTE = "ka10006"  # 주식시분요청
    MARKET_INFO = "ka10007"  # 시세표성정보요청
    NEW_STOCK_RIGHT = "ka10011"  # 신주인수권전체시세요청
    DAILY_INST_TRADE = "ka10044"  # 일별기관매매종목요청
    STOCK_INST_TRADE_TREND = "ka10045"  # 종목별기관매매추이요청
    EXECUTION_STRENGTH_HOURLY = "ka10046"  # 체결강도추이시간별요청
    EXECUTION_STRENGTH_DAILY = "ka10047"  # 체결강도추이일별요청
    INTRADAY_INVESTOR_TRADE = "ka10063"  # 장중투자자별매매요청
    AFTER_HOURS_INVESTOR = "ka10066"  # 장마감후투자자별매매요청
    BROKER_STOCK_TREND = "ka10078"  # 증권사별종목매매동향요청
    DAILY_PRICE = "ka10086"  # 일별주가요청
    AFTER_HOURS_SINGLE = "ka10087"  # 시간외단일가요청
    PROGRAM_TRADE_HOURLY = "ka90005"  # 프로그램매매추이요청 시간대별
    PROGRAM_ARBITRAGE = "ka90006"  # 프로그램매매차익잔고추이요청
    PROGRAM_CUMULATIVE = "ka90007"  # 프로그램매매누적추이요청
    STOCK_PROGRAM_HOURLY = "ka90008"  # 종목시간별프로그램매매추이요청
    PROGRAM_TRADE_DAILY = "ka90010"  # 프로그램매매추이요청 일자별
    STOCK_PROGRAM_DAILY = "ka90013"  # 종목일별프로그램매매추이요청

    # ===== 기관/외국인 (3개) =====
    FOREIGN_STOCK_TRADE = "ka10008"  # 주식외국인종목별매매동향
    STOCK_INSTITUTION = "ka10009"  # 주식기관요청
    INST_FOREIGN_CONTINUOUS = "ka10131"  # 기관외국인연속매매현황요청

    # ===== 업종 (6개) =====
    SECTOR_PROGRAM = "ka10010"  # 업종프로그램요청
    SECTOR_INVESTOR_NET_BUY = "ka10051"  # 업종별투자자순매수요청
    SECTOR_CURRENT_PRICE = "ka20001"  # 업종현재가요청
    SECTOR_PRICE = "ka20002"  # 업종별주가요청
    ALL_SECTOR_INDEX = "ka20003"  # 전업종지수요청
    SECTOR_DAILY = "ka20009"  # 업종현재가일별요청

    # ===== 공매도 (1개) =====
    SHORT_SELLING_TREND = "ka10014"  # 공매도추이요청

    # ===== 순위정보 (23개) =====
    ORDERBOOK_TOP = "ka10020"  # 호가잔량상위요청
    ORDERBOOK_SURGE = "ka10021"  # 호가잔량급증요청
    REMAINING_RATE_SURGE = "ka10022"  # 잔량율급증요청
    VOLUME_SURGE = "ka10023"  # 거래량급증요청
    DAILY_CHANGE_TOP = "ka10027"  # 전일대비등락률상위요청
    EXPECTED_CHANGE_TOP = "ka10029"  # 예상체결등락률상위요청
    TODAY_VOLUME_TOP = "ka10030"  # 당일거래량상위요청
    YESTERDAY_VOLUME_TOP = "ka10031"  # 전일거래량상위요청
    TRADE_VALUE_TOP = "ka10032"  # 거래대금상위요청
    CREDIT_RATIO_TOP = "ka10033"  # 신용비율상위요청
    FOREIGN_PERIOD_TOP = "ka10034"  # 외인기간별매매상위요청
    FOREIGN_CONTINUOUS_TOP = "ka10035"  # 외인연속순매매상위요청
    FOREIGN_LIMIT_EXHAUST = "ka10036"  # 외인한도소진율증가상위
    FOREIGN_WINDOW_TOP = "ka10037"  # 외국계창구매매상위요청
    STOCK_BROKER_RANK = "ka10038"  # 종목별증권사순위요청
    BROKER_TRADE_TOP = "ka10039"  # 증권사별매매상위요청
    TODAY_MAIN_TRADER = "ka10040"  # 당일주요거래원요청
    NET_BUY_TRADER_RANK = "ka10042"  # 순매수거래원순위요청
    TODAY_TOP_LEAVE = "ka10053"  # 당일상위이탈원요청
    SAME_NET_TRADE_RANK = "ka10062"  # 동일순매매순위요청
    INTRADAY_INVESTOR_TOP = "ka10065"  # 장중투자자별매매상위요청
    AFTER_HOURS_CHANGE_RANK = "ka10098"  # 시간외단일가등락율순위요청
    FOREIGN_INST_TOP = "ka90009"  # 외국인기관매매상위요청

    # ===== 차트 (12개) =====
    STOCK_TICK_CHART = "ka10079"  # 주식틱차트조회요청
    STOCK_MINUTE_CHART = "ka10080"  # 주식분봉차트조회요청
    STOCK_DAILY_CHART = "ka10081"  # 주식일봉차트조회요청
    STOCK_WEEKLY_CHART = "ka10082"  # 주식주봉차트조회요청
    STOCK_MONTHLY_CHART = "ka10083"  # 주식월봉차트조회요청
    STOCK_YEARLY_CHART = "ka10094"  # 주식년봉차트조회요청
    SECTOR_TICK_CHART = "ka20004"  # 업종틱차트조회요청
    SECTOR_MINUTE_CHART = "ka20005"  # 업종분봉조회요청
    SECTOR_DAILY_CHART = "ka20006"  # 업종일봉조회요청
    SECTOR_WEEKLY_CHART = "ka20007"  # 업종주봉조회요청
    SECTOR_MONTHLY_CHART = "ka20008"  # 업종월봉조회요청
    SECTOR_YEARLY_CHART = "ka20019"  # 업종년봉조회요청

    # ===== 대차거래 (4개) =====
    SLB_TREND = "ka10068"  # 대차거래추이요청
    SLB_TOP10 = "ka10069"  # 대차거래상위10종목요청
    SLB_TREND_BY_STOCK = "ka20068"  # 대차거래추이요청(종목별)
    SLB_DETAIL = "ka90012"  # 대차거래내역요청

    # ===== 계좌 (18개) =====
    REALIZED_PL_BY_DATE = "ka10072"  # 일자별종목별실현손익요청_일자
    REALIZED_PL_BY_PERIOD = "ka10073"  # 일자별종목별실현손익요청_기간
    DAILY_REALIZED_PL = "ka10074"  # 일자별실현손익요청
    OUTSTANDING_ORDER = "ka10075"  # 미체결요청
    EXECUTION_REQUEST = "ka10076"  # 체결요청
    TODAY_REALIZED_PL_DETAIL = "ka10077"  # 당일실현손익상세요청
    ACCOUNT_RETURN = "ka10085"  # 계좌수익률요청
    OUTSTANDING_SPLIT_DETAIL = "ka10088"  # 미체결 분할주문 상세
    TODAY_TRADE_LOG = "ka10170"  # 당일매매일지요청
    DEPOSIT_DETAIL = "kt00001"  # 예수금상세현황요청
    DAILY_ESTIMATED_ASSET = "kt00002"  # 일별추정예탁자산현황요청
    ESTIMATED_ASSET = "kt00003"  # 추정자산조회요청
    ACCOUNT_EVALUATION = "kt00004"  # 계좌평가현황요청
    EXECUTION_BALANCE = "kt00005"  # 체결잔고요청
    ACCOUNT_ORDER_DETAIL = "kt00007"  # 계좌별주문체결내역상세요청
    NEXT_DAY_SETTLEMENT = "kt00008"  # 계좌별익일결제예정내역요청
    ACCOUNT_ORDER_STATUS = "kt00009"  # 계좌별주문체결현황요청
    ORDER_WITHDRAWABLE = "kt00010"  # 주문인출가능금액요청
    MARGIN_ORDER_QUANTITY = "kt00011"  # 증거금율별주문가능수량조회요청
    CREDIT_ORDER_QUANTITY = "kt00012"  # 신용보증금율별주문가능수량조회요청
    MARGIN_DETAIL = "kt00013"  # 증거금세부내역조회요청
    CONSIGNMENT_TRADE = "kt00015"  # 위탁종합거래내역요청
    DAILY_ACCOUNT_RETURN = "kt00016"  # 일별계좌수익률상세현황요청
    ACCOUNT_TODAY_STATUS = "kt00017"  # 계좌별당일현황요청
    ACCOUNT_BALANCE_DETAIL = "kt00018"  # 계좌평가잔고내역요청

    # ===== ELW (12개) =====
    ELW_DAILY_SENSITIVITY = "ka10048"  # ELW일별민감도지표요청
    ELW_SENSITIVITY = "ka10050"  # ELW민감도지표요청
    ELW_PRICE_SURGE = "ka30001"  # ELW가격급등락요청
    TRADER_ELW_NET_TOP = "ka30002"  # 거래원별ELW순매매상위요청
    ELW_LP_DAILY_TREND = "ka30003"  # ELWLP보유일별추이요청
    ELW_DISPARITY = "ka30004"  # ELW괴리율요청
    ELW_SEARCH = "ka30005"  # ELW조건검색요청
    ELW_CHANGE_RANK = "ka30009"  # ELW등락율순위요청
    ELW_REMAINING_RANK = "ka30010"  # ELW잔량순위요청
    ELW_APPROACH_RATE = "ka30011"  # ELW근접율요청
    ELW_DETAIL_INFO = "ka30012"  # ELW종목상세정보요청

    # ===== ETF (9개) =====
    ETF_RETURN = "ka40001"  # ETF수익율요청
    ETF_STOCK_INFO = "ka40002"  # ETF종목정보요청
    ETF_DAILY_TREND = "ka40003"  # ETF일별추이요청
    ETF_TOTAL_QUOTE = "ka40004"  # ETF전체시세요청
    ETF_HOURLY_TREND = "ka40006"  # ETF시간대별추이요청
    ETF_HOURLY_EXECUTION = "ka40007"  # ETF시간대별체결요청
    ETF_DAILY_EXECUTION = "ka40008"  # ETF일자별체결요청
    ETF_HOURLY_EXECUTION2 = "ka40009"  # ETF시간대별체결요청2
    ETF_HOURLY_TREND2 = "ka40010"  # ETF시간대별추이요청2

    # ===== 테마 (2개) =====
    THEME_GROUP = "ka90001"  # 테마그룹별요청
    THEME_STOCKS = "ka90002"  # 테마구성종목요청

    # ===== 주문 (4개) =====
    STOCK_BUY_ORDER = "kt10000"  # 주식 매수주문
    STOCK_SELL_ORDER = "kt10001"  # 주식 매도주문
    STOCK_MODIFY_ORDER = "kt10002"  # 주식 정정주문
    STOCK_CANCEL_ORDER = "kt10003"  # 주식 취소주문

    # ===== 신용주문 (4개) =====
    CREDIT_BUY_ORDER = "kt10006"  # 신용 매수주문
    CREDIT_SELL_ORDER = "kt10007"  # 신용 매도주문
    CREDIT_MODIFY_ORDER = "kt10008"  # 신용 정정주문
    CREDIT_CANCEL_ORDER = "kt10009"  # 신용 취소주문

    # ===== WebSocket (22개) =====
    WS_ORDER_EXECUTION = "ws_00"  # 주문체결
    WS_BALANCE = "ws_04"  # 잔고
    WS_STOCK_QUOTE = "ws_0A"  # 주식기세
    WS_STOCK_EXECUTION = "ws_0B"  # 주식체결
    WS_STOCK_PRIORITY = "ws_0C"  # 주식우선호가
    WS_STOCK_ORDERBOOK = "ws_0D"  # 주식호가잔량
    WS_AFTER_HOURS_QUOTE = "ws_0E"  # 주식시간외호가
    WS_TODAY_TRADER = "ws_0F"  # 주식당일거래원
    WS_ETF_NAV = "ws_0G"  # ETF NAV
    WS_EXPECTED_EXECUTION = "ws_0H"  # 주식예상체결
    WS_SECTOR_INDEX = "ws_0J"  # 업종지수
    WS_SECTOR_CHANGE = "ws_0U"  # 업종등락
    WS_STOCK_INFO = "ws_0g"  # 주식종목정보
    WS_ELW_THEORY = "ws_0m"  # ELW 이론가
    WS_MARKET_TIME = "ws_0s"  # 장시작시간
    WS_ELW_INDICATOR = "ws_0u"  # ELW 지표
    WS_STOCK_PROGRAM = "ws_0w"  # 종목프로그램매매
    WS_VI_TRIGGER = "ws_1h"  # VI발동/해제

    # 조건 검색
    CONDITION_LIST = "ka10171"  # 조건검색 목록조회
    CONDITION_SEARCH = "ka10172"  # 조건검색 요청 일반
    CONDITION_REALTIME = "ka10173"  # 조건검색 요청 실시간
    CONDITION_CANCEL = "ka10174"  # 조건검색 실시간 해제


class APIEndpointPath(str, Enum):
    """API 엔드포인트 경로"""

    # OAuth
    OAUTH_TOKEN = "/oauth2/token"
    OAUTH_REVOKE = "/oauth2/revoke"

    # 국내주식
    DOSTK_STKINFO = "/api/dostk/stkinfo"
    DOSTK_MRKCOND = "/api/dostk/mrkcond"
    DOSTK_FRGNISTT = "/api/dostk/frgnistt"
    DOSTK_SECT = "/api/dostk/sect"
    DOSTK_SHSA = "/api/dostk/shsa"
    DOSTK_RKINFO = "/api/dostk/rkinfo"
    DOSTK_CHART = "/api/dostk/chart"
    DOSTK_SLB = "/api/dostk/slb"
    DOSTK_ACNT = "/api/dostk/acnt"
    DOSTK_ELW = "/api/dostk/elw"
    DOSTK_ETF = "/api/dostk/etf"
    DOSTK_THME = "/api/dostk/thme"
    DOSTK_ORDR = "/api/dostk/ordr"
    DOSTK_CRDORDR = "/api/dostk/crdordr"

    # WebSocket
    WEBSOCKET = "/api/dostk/websocket"


# API 카테고리별 ID 매핑
API_CATEGORY_MAP = {
    KiwoomCategory.AUTH: [
        KiwoomAPIID.TOKEN_ISSUE,
        KiwoomAPIID.TOKEN_REVOKE,
    ],
    KiwoomCategory.STKINFO: [
        KiwoomAPIID.STOCK_BASIC_INFO,
        KiwoomAPIID.STOCK_TRADING_MEMBER,
        KiwoomAPIID.STOCK_EXECUTION_INFO,
        KiwoomAPIID.CREDIT_TRADE_TREND,
        KiwoomAPIID.DAILY_TRADE_DETAIL,
        KiwoomAPIID.NEW_HIGH_LOW,
        KiwoomAPIID.UPPER_LOWER_LIMIT,
        KiwoomAPIID.HIGH_LOW_APPROACH,
        KiwoomAPIID.PRICE_SURGE_DROP,
        KiwoomAPIID.VOLUME_RENEWAL,
        KiwoomAPIID.OFFER_CONCENTRATION,
        KiwoomAPIID.HIGH_LOW_PER,
        KiwoomAPIID.OPEN_PRICE_COMPARE,
        KiwoomAPIID.TRADER_OFFER_ANALYSIS,
        KiwoomAPIID.TRADER_INSTANT_VOLUME,
        KiwoomAPIID.VOLATILITY_INTERRUPT,
        KiwoomAPIID.TODAY_YESTERDAY_VOLUME,
        KiwoomAPIID.INVESTOR_DAILY_TRADE,
        KiwoomAPIID.STOCK_INVESTOR_BY_INST,
        KiwoomAPIID.STOCK_INVESTOR_BY_INST_SUM,
        KiwoomAPIID.TODAY_YESTERDAY_EXECUTION,
        KiwoomAPIID.WATCHLIST_INFO,
        KiwoomAPIID.STOCK_LIST,
        KiwoomAPIID.STOCK_INFO,
        KiwoomAPIID.SECTOR_CODE_LIST,
        KiwoomAPIID.MEMBER_LIST,
        KiwoomAPIID.PROGRAM_NET_BUY_TOP50,
        KiwoomAPIID.STOCK_PROGRAM_TRADE,
        KiwoomAPIID.CREDIT_AVAILABLE_STOCK,
        KiwoomAPIID.CREDIT_AVAILABLE_INQUIRY,
        KiwoomAPIID.CONDITION_LIST,
        KiwoomAPIID.CONDITION_SEARCH,
        KiwoomAPIID.CONDITION_REALTIME,
        KiwoomAPIID.CONDITION_CANCEL,
    ],
    KiwoomCategory.MRKCOND: [
        KiwoomAPIID.STOCK_ORDERBOOK,
        KiwoomAPIID.STOCK_DAILY_WEEKLY_MONTHLY,
        KiwoomAPIID.STOCK_MINUTE,
        KiwoomAPIID.MARKET_INFO,
        KiwoomAPIID.NEW_STOCK_RIGHT,
        KiwoomAPIID.DAILY_INST_TRADE,
        KiwoomAPIID.STOCK_INST_TRADE_TREND,
        KiwoomAPIID.EXECUTION_STRENGTH_HOURLY,
        KiwoomAPIID.EXECUTION_STRENGTH_DAILY,
        KiwoomAPIID.INTRADAY_INVESTOR_TRADE,
        KiwoomAPIID.AFTER_HOURS_INVESTOR,
        KiwoomAPIID.BROKER_STOCK_TREND,
        KiwoomAPIID.DAILY_PRICE,
        KiwoomAPIID.AFTER_HOURS_SINGLE,
        KiwoomAPIID.PROGRAM_TRADE_HOURLY,
        KiwoomAPIID.PROGRAM_ARBITRAGE,
        KiwoomAPIID.PROGRAM_CUMULATIVE,
        KiwoomAPIID.STOCK_PROGRAM_HOURLY,
        KiwoomAPIID.PROGRAM_TRADE_DAILY,
        KiwoomAPIID.STOCK_PROGRAM_DAILY,
    ],
    KiwoomCategory.FRGNISTT: [
        KiwoomAPIID.FOREIGN_STOCK_TRADE,
        KiwoomAPIID.STOCK_INSTITUTION,
        KiwoomAPIID.INST_FOREIGN_CONTINUOUS,
    ],
    KiwoomCategory.SECT: [
        KiwoomAPIID.SECTOR_PROGRAM,
        KiwoomAPIID.SECTOR_INVESTOR_NET_BUY,
        KiwoomAPIID.SECTOR_CURRENT_PRICE,
        KiwoomAPIID.SECTOR_PRICE,
        KiwoomAPIID.ALL_SECTOR_INDEX,
        KiwoomAPIID.SECTOR_DAILY,
    ],
    KiwoomCategory.SHSA: [
        KiwoomAPIID.SHORT_SELLING_TREND,
    ],
    KiwoomCategory.RKINFO: [
        KiwoomAPIID.ORDERBOOK_TOP,
        KiwoomAPIID.ORDERBOOK_SURGE,
        KiwoomAPIID.REMAINING_RATE_SURGE,
        KiwoomAPIID.VOLUME_SURGE,
        KiwoomAPIID.DAILY_CHANGE_TOP,
        KiwoomAPIID.EXPECTED_CHANGE_TOP,
        KiwoomAPIID.TODAY_VOLUME_TOP,
        KiwoomAPIID.YESTERDAY_VOLUME_TOP,
        KiwoomAPIID.TRADE_VALUE_TOP,
        KiwoomAPIID.CREDIT_RATIO_TOP,
        KiwoomAPIID.FOREIGN_PERIOD_TOP,
        KiwoomAPIID.FOREIGN_CONTINUOUS_TOP,
        KiwoomAPIID.FOREIGN_LIMIT_EXHAUST,
        KiwoomAPIID.FOREIGN_WINDOW_TOP,
        KiwoomAPIID.STOCK_BROKER_RANK,
        KiwoomAPIID.BROKER_TRADE_TOP,
        KiwoomAPIID.TODAY_MAIN_TRADER,
        KiwoomAPIID.NET_BUY_TRADER_RANK,
        KiwoomAPIID.TODAY_TOP_LEAVE,
        KiwoomAPIID.SAME_NET_TRADE_RANK,
        KiwoomAPIID.INTRADAY_INVESTOR_TOP,
        KiwoomAPIID.AFTER_HOURS_CHANGE_RANK,
        KiwoomAPIID.FOREIGN_INST_TOP,
    ],
    KiwoomCategory.CHART: [
        KiwoomAPIID.STOCK_TICK_CHART,
        KiwoomAPIID.STOCK_MINUTE_CHART,
        KiwoomAPIID.STOCK_DAILY_CHART,
        KiwoomAPIID.STOCK_WEEKLY_CHART,
        KiwoomAPIID.STOCK_MONTHLY_CHART,
        KiwoomAPIID.STOCK_YEARLY_CHART,
        KiwoomAPIID.SECTOR_TICK_CHART,
        KiwoomAPIID.SECTOR_MINUTE_CHART,
        KiwoomAPIID.SECTOR_DAILY_CHART,
        KiwoomAPIID.SECTOR_WEEKLY_CHART,
        KiwoomAPIID.SECTOR_MONTHLY_CHART,
        KiwoomAPIID.SECTOR_YEARLY_CHART,
    ],
    KiwoomCategory.SLB: [
        KiwoomAPIID.SLB_TREND,
        KiwoomAPIID.SLB_TOP10,
        KiwoomAPIID.SLB_TREND_BY_STOCK,
        KiwoomAPIID.SLB_DETAIL,
    ],
    KiwoomCategory.ACNT: [
        KiwoomAPIID.REALIZED_PL_BY_DATE,
        KiwoomAPIID.REALIZED_PL_BY_PERIOD,
        KiwoomAPIID.DAILY_REALIZED_PL,
        KiwoomAPIID.OUTSTANDING_ORDER,
        KiwoomAPIID.EXECUTION_REQUEST,
        KiwoomAPIID.TODAY_REALIZED_PL_DETAIL,
        KiwoomAPIID.ACCOUNT_RETURN,
        KiwoomAPIID.OUTSTANDING_SPLIT_DETAIL,
        KiwoomAPIID.TODAY_TRADE_LOG,
        KiwoomAPIID.DEPOSIT_DETAIL,
        KiwoomAPIID.DAILY_ESTIMATED_ASSET,
        KiwoomAPIID.ESTIMATED_ASSET,
        KiwoomAPIID.ACCOUNT_EVALUATION,
        KiwoomAPIID.EXECUTION_BALANCE,
        KiwoomAPIID.ACCOUNT_ORDER_DETAIL,
        KiwoomAPIID.NEXT_DAY_SETTLEMENT,
        KiwoomAPIID.ACCOUNT_ORDER_STATUS,
        KiwoomAPIID.ORDER_WITHDRAWABLE,
        KiwoomAPIID.MARGIN_ORDER_QUANTITY,
        KiwoomAPIID.CREDIT_ORDER_QUANTITY,
        KiwoomAPIID.MARGIN_DETAIL,
        KiwoomAPIID.CONSIGNMENT_TRADE,
        KiwoomAPIID.DAILY_ACCOUNT_RETURN,
        KiwoomAPIID.ACCOUNT_TODAY_STATUS,
        KiwoomAPIID.ACCOUNT_BALANCE_DETAIL,
    ],
    KiwoomCategory.ELW: [
        KiwoomAPIID.ELW_DAILY_SENSITIVITY,
        KiwoomAPIID.ELW_SENSITIVITY,
        KiwoomAPIID.ELW_PRICE_SURGE,
        KiwoomAPIID.TRADER_ELW_NET_TOP,
        KiwoomAPIID.ELW_LP_DAILY_TREND,
        KiwoomAPIID.ELW_DISPARITY,
        KiwoomAPIID.ELW_SEARCH,
        KiwoomAPIID.ELW_CHANGE_RANK,
        KiwoomAPIID.ELW_REMAINING_RANK,
        KiwoomAPIID.ELW_APPROACH_RATE,
        KiwoomAPIID.ELW_DETAIL_INFO,
    ],
    KiwoomCategory.ETF: [
        KiwoomAPIID.ETF_RETURN,
        KiwoomAPIID.ETF_STOCK_INFO,
        KiwoomAPIID.ETF_DAILY_TREND,
        KiwoomAPIID.ETF_TOTAL_QUOTE,
        KiwoomAPIID.ETF_HOURLY_TREND,
        KiwoomAPIID.ETF_HOURLY_EXECUTION,
        KiwoomAPIID.ETF_DAILY_EXECUTION,
        KiwoomAPIID.ETF_HOURLY_EXECUTION2,
        KiwoomAPIID.ETF_HOURLY_TREND2,
    ],
    KiwoomCategory.THME: [
        KiwoomAPIID.THEME_GROUP,
        KiwoomAPIID.THEME_STOCKS,
    ],
    KiwoomCategory.ORDR: [
        KiwoomAPIID.STOCK_BUY_ORDER,
        KiwoomAPIID.STOCK_SELL_ORDER,
        KiwoomAPIID.STOCK_MODIFY_ORDER,
        KiwoomAPIID.STOCK_CANCEL_ORDER,
    ],
    KiwoomCategory.CRDORDR: [
        KiwoomAPIID.CREDIT_BUY_ORDER,
        KiwoomAPIID.CREDIT_SELL_ORDER,
        KiwoomAPIID.CREDIT_MODIFY_ORDER,
        KiwoomAPIID.CREDIT_CANCEL_ORDER,
    ],
    KiwoomCategory.WEBSOCKET: [
        KiwoomAPIID.WS_ORDER_EXECUTION,
        KiwoomAPIID.WS_BALANCE,
        KiwoomAPIID.WS_STOCK_QUOTE,
        KiwoomAPIID.WS_STOCK_EXECUTION,
        KiwoomAPIID.WS_STOCK_PRIORITY,
        KiwoomAPIID.WS_STOCK_ORDERBOOK,
        KiwoomAPIID.WS_AFTER_HOURS_QUOTE,
        KiwoomAPIID.WS_TODAY_TRADER,
        KiwoomAPIID.WS_ETF_NAV,
        KiwoomAPIID.WS_EXPECTED_EXECUTION,
        KiwoomAPIID.WS_SECTOR_INDEX,
        KiwoomAPIID.WS_SECTOR_CHANGE,
        KiwoomAPIID.WS_STOCK_INFO,
        KiwoomAPIID.WS_ELW_THEORY,
        KiwoomAPIID.WS_MARKET_TIME,
        KiwoomAPIID.WS_ELW_INDICATOR,
        KiwoomAPIID.WS_STOCK_PROGRAM,
        KiwoomAPIID.WS_VI_TRIGGER,
    ],
}

# API ID별 엔드포인트 경로 매핑
API_ENDPOINT_MAP = {
    # OAuth
    KiwoomAPIID.TOKEN_ISSUE: APIEndpointPath.OAUTH_TOKEN,
    KiwoomAPIID.TOKEN_REVOKE: APIEndpointPath.OAUTH_REVOKE,
    # 종목정보 (STKINFO)
    KiwoomAPIID.STOCK_BASIC_INFO: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.STOCK_TRADING_MEMBER: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.STOCK_EXECUTION_INFO: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.CREDIT_TRADE_TREND: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.DAILY_TRADE_DETAIL: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.NEW_HIGH_LOW: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.UPPER_LOWER_LIMIT: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.HIGH_LOW_APPROACH: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.PRICE_SURGE_DROP: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.VOLUME_RENEWAL: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.OFFER_CONCENTRATION: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.HIGH_LOW_PER: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.OPEN_PRICE_COMPARE: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.TRADER_OFFER_ANALYSIS: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.TRADER_INSTANT_VOLUME: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.VOLATILITY_INTERRUPT: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.TODAY_YESTERDAY_VOLUME: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.INVESTOR_DAILY_TRADE: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.STOCK_INVESTOR_BY_INST: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.STOCK_INVESTOR_BY_INST_SUM: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.TODAY_YESTERDAY_EXECUTION: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.WATCHLIST_INFO: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.STOCK_LIST: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.STOCK_INFO: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.SECTOR_CODE_LIST: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.MEMBER_LIST: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.PROGRAM_NET_BUY_TOP50: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.STOCK_PROGRAM_TRADE: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.CREDIT_AVAILABLE_STOCK: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.CREDIT_AVAILABLE_INQUIRY: APIEndpointPath.DOSTK_STKINFO,
    # 시세 (MRKCOND)
    KiwoomAPIID.STOCK_ORDERBOOK: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.STOCK_DAILY_WEEKLY_MONTHLY: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.STOCK_MINUTE: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.MARKET_INFO: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.NEW_STOCK_RIGHT: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.DAILY_INST_TRADE: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.STOCK_INST_TRADE_TREND: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.EXECUTION_STRENGTH_HOURLY: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.EXECUTION_STRENGTH_DAILY: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.INTRADAY_INVESTOR_TRADE: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.AFTER_HOURS_INVESTOR: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.BROKER_STOCK_TREND: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.DAILY_PRICE: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.AFTER_HOURS_SINGLE: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.PROGRAM_TRADE_HOURLY: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.PROGRAM_ARBITRAGE: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.PROGRAM_CUMULATIVE: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.STOCK_PROGRAM_HOURLY: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.PROGRAM_TRADE_DAILY: APIEndpointPath.DOSTK_MRKCOND,
    KiwoomAPIID.STOCK_PROGRAM_DAILY: APIEndpointPath.DOSTK_MRKCOND,
    # 기관/외국인 (FRGNISTT)
    KiwoomAPIID.FOREIGN_STOCK_TRADE: APIEndpointPath.DOSTK_FRGNISTT,
    KiwoomAPIID.STOCK_INSTITUTION: APIEndpointPath.DOSTK_FRGNISTT,
    KiwoomAPIID.INST_FOREIGN_CONTINUOUS: APIEndpointPath.DOSTK_FRGNISTT,
    # 업종 (SECT)
    KiwoomAPIID.SECTOR_PROGRAM: APIEndpointPath.DOSTK_SECT,
    KiwoomAPIID.SECTOR_INVESTOR_NET_BUY: APIEndpointPath.DOSTK_SECT,
    KiwoomAPIID.SECTOR_CURRENT_PRICE: APIEndpointPath.DOSTK_SECT,
    KiwoomAPIID.SECTOR_PRICE: APIEndpointPath.DOSTK_SECT,
    KiwoomAPIID.ALL_SECTOR_INDEX: APIEndpointPath.DOSTK_SECT,
    KiwoomAPIID.SECTOR_DAILY: APIEndpointPath.DOSTK_SECT,
    # 공매도 (SHSA)
    KiwoomAPIID.SHORT_SELLING_TREND: APIEndpointPath.DOSTK_SHSA,
    # 순위정보 (RKINFO)
    KiwoomAPIID.ORDERBOOK_TOP: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.ORDERBOOK_SURGE: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.REMAINING_RATE_SURGE: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.VOLUME_SURGE: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.DAILY_CHANGE_TOP: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.EXPECTED_CHANGE_TOP: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.TODAY_VOLUME_TOP: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.YESTERDAY_VOLUME_TOP: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.TRADE_VALUE_TOP: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.CREDIT_RATIO_TOP: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.FOREIGN_PERIOD_TOP: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.FOREIGN_CONTINUOUS_TOP: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.FOREIGN_LIMIT_EXHAUST: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.FOREIGN_WINDOW_TOP: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.STOCK_BROKER_RANK: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.BROKER_TRADE_TOP: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.TODAY_MAIN_TRADER: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.NET_BUY_TRADER_RANK: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.TODAY_TOP_LEAVE: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.SAME_NET_TRADE_RANK: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.INTRADAY_INVESTOR_TOP: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.AFTER_HOURS_CHANGE_RANK: APIEndpointPath.DOSTK_RKINFO,
    KiwoomAPIID.FOREIGN_INST_TOP: APIEndpointPath.DOSTK_RKINFO,
    # 차트 (CHART)
    KiwoomAPIID.STOCK_TICK_CHART: APIEndpointPath.DOSTK_CHART,
    KiwoomAPIID.STOCK_MINUTE_CHART: APIEndpointPath.DOSTK_CHART,
    KiwoomAPIID.STOCK_DAILY_CHART: APIEndpointPath.DOSTK_CHART,
    KiwoomAPIID.STOCK_WEEKLY_CHART: APIEndpointPath.DOSTK_CHART,
    KiwoomAPIID.STOCK_MONTHLY_CHART: APIEndpointPath.DOSTK_CHART,
    KiwoomAPIID.STOCK_YEARLY_CHART: APIEndpointPath.DOSTK_CHART,
    KiwoomAPIID.SECTOR_TICK_CHART: APIEndpointPath.DOSTK_CHART,
    KiwoomAPIID.SECTOR_MINUTE_CHART: APIEndpointPath.DOSTK_CHART,
    KiwoomAPIID.SECTOR_DAILY_CHART: APIEndpointPath.DOSTK_CHART,
    KiwoomAPIID.SECTOR_WEEKLY_CHART: APIEndpointPath.DOSTK_CHART,
    KiwoomAPIID.SECTOR_MONTHLY_CHART: APIEndpointPath.DOSTK_CHART,
    KiwoomAPIID.SECTOR_YEARLY_CHART: APIEndpointPath.DOSTK_CHART,
    # 대차거래 (SLB)
    KiwoomAPIID.SLB_TREND: APIEndpointPath.DOSTK_SLB,
    KiwoomAPIID.SLB_TOP10: APIEndpointPath.DOSTK_SLB,
    KiwoomAPIID.SLB_TREND_BY_STOCK: APIEndpointPath.DOSTK_SLB,
    KiwoomAPIID.SLB_DETAIL: APIEndpointPath.DOSTK_SLB,
    # 계좌 (ACNT)
    KiwoomAPIID.REALIZED_PL_BY_DATE: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.REALIZED_PL_BY_PERIOD: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.DAILY_REALIZED_PL: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.OUTSTANDING_ORDER: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.EXECUTION_REQUEST: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.TODAY_REALIZED_PL_DETAIL: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.ACCOUNT_RETURN: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.OUTSTANDING_SPLIT_DETAIL: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.TODAY_TRADE_LOG: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.DEPOSIT_DETAIL: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.DAILY_ESTIMATED_ASSET: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.ESTIMATED_ASSET: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.ACCOUNT_EVALUATION: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.EXECUTION_BALANCE: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.ACCOUNT_ORDER_DETAIL: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.NEXT_DAY_SETTLEMENT: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.ACCOUNT_ORDER_STATUS: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.ORDER_WITHDRAWABLE: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.MARGIN_ORDER_QUANTITY: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.CREDIT_ORDER_QUANTITY: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.MARGIN_DETAIL: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.CONSIGNMENT_TRADE: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.DAILY_ACCOUNT_RETURN: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.ACCOUNT_TODAY_STATUS: APIEndpointPath.DOSTK_ACNT,
    KiwoomAPIID.ACCOUNT_BALANCE_DETAIL: APIEndpointPath.DOSTK_ACNT,
    # ELW
    KiwoomAPIID.ELW_DAILY_SENSITIVITY: APIEndpointPath.DOSTK_ELW,
    KiwoomAPIID.ELW_SENSITIVITY: APIEndpointPath.DOSTK_ELW,
    KiwoomAPIID.ELW_PRICE_SURGE: APIEndpointPath.DOSTK_ELW,
    KiwoomAPIID.TRADER_ELW_NET_TOP: APIEndpointPath.DOSTK_ELW,
    KiwoomAPIID.ELW_LP_DAILY_TREND: APIEndpointPath.DOSTK_ELW,
    KiwoomAPIID.ELW_DISPARITY: APIEndpointPath.DOSTK_ELW,
    KiwoomAPIID.ELW_SEARCH: APIEndpointPath.DOSTK_ELW,
    KiwoomAPIID.ELW_CHANGE_RANK: APIEndpointPath.DOSTK_ELW,
    KiwoomAPIID.ELW_REMAINING_RANK: APIEndpointPath.DOSTK_ELW,
    KiwoomAPIID.ELW_APPROACH_RATE: APIEndpointPath.DOSTK_ELW,
    KiwoomAPIID.ELW_DETAIL_INFO: APIEndpointPath.DOSTK_ELW,
    # ETF
    KiwoomAPIID.ETF_RETURN: APIEndpointPath.DOSTK_ETF,
    KiwoomAPIID.ETF_STOCK_INFO: APIEndpointPath.DOSTK_ETF,
    KiwoomAPIID.ETF_DAILY_TREND: APIEndpointPath.DOSTK_ETF,
    KiwoomAPIID.ETF_TOTAL_QUOTE: APIEndpointPath.DOSTK_ETF,
    KiwoomAPIID.ETF_HOURLY_TREND: APIEndpointPath.DOSTK_ETF,
    KiwoomAPIID.ETF_HOURLY_EXECUTION: APIEndpointPath.DOSTK_ETF,
    KiwoomAPIID.ETF_DAILY_EXECUTION: APIEndpointPath.DOSTK_ETF,
    KiwoomAPIID.ETF_HOURLY_EXECUTION2: APIEndpointPath.DOSTK_ETF,
    KiwoomAPIID.ETF_HOURLY_TREND2: APIEndpointPath.DOSTK_ETF,
    # 테마 (THME)
    KiwoomAPIID.THEME_GROUP: APIEndpointPath.DOSTK_THME,
    KiwoomAPIID.THEME_STOCKS: APIEndpointPath.DOSTK_THME,
    # 주문 (ORDR)
    KiwoomAPIID.STOCK_BUY_ORDER: APIEndpointPath.DOSTK_ORDR,
    KiwoomAPIID.STOCK_SELL_ORDER: APIEndpointPath.DOSTK_ORDR,
    KiwoomAPIID.STOCK_MODIFY_ORDER: APIEndpointPath.DOSTK_ORDR,
    KiwoomAPIID.STOCK_CANCEL_ORDER: APIEndpointPath.DOSTK_ORDR,
    # 신용주문 (CRDORDR)
    KiwoomAPIID.CREDIT_BUY_ORDER: APIEndpointPath.DOSTK_CRDORDR,
    KiwoomAPIID.CREDIT_SELL_ORDER: APIEndpointPath.DOSTK_CRDORDR,
    KiwoomAPIID.CREDIT_MODIFY_ORDER: APIEndpointPath.DOSTK_CRDORDR,
    KiwoomAPIID.CREDIT_CANCEL_ORDER: APIEndpointPath.DOSTK_CRDORDR,
    # WebSocket
    KiwoomAPIID.WS_ORDER_EXECUTION: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_BALANCE: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_STOCK_QUOTE: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_STOCK_EXECUTION: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_STOCK_PRIORITY: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_STOCK_ORDERBOOK: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_AFTER_HOURS_QUOTE: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_TODAY_TRADER: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_ETF_NAV: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_EXPECTED_EXECUTION: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_SECTOR_INDEX: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_SECTOR_CHANGE: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_STOCK_INFO: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_ELW_THEORY: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_MARKET_TIME: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_ELW_INDICATOR: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_STOCK_PROGRAM: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.WS_VI_TRIGGER: APIEndpointPath.WEBSOCKET,
    KiwoomAPIID.CONDITION_LIST: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.CONDITION_SEARCH: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.CONDITION_REALTIME: APIEndpointPath.DOSTK_STKINFO,
    KiwoomAPIID.CONDITION_CANCEL: APIEndpointPath.DOSTK_STKINFO,
}
