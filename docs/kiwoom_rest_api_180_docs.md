# **키움증권 REST & WebSocket API 전체 명세 (Input 파라미터 포함)**

제공된 공식 문서를 기반으로 180개의 전체 API를 기능 및 분류에 따라 체계적으로 정리한 문서입니다. 각 API는 고유 ID, 기능명, 호출 URL 및 필수 입력 파라미터 정보로 구성되어 있어 개발 시 편리하게 참조할 수 있습니다.

* **공통 Header**: 모든 REST API 요청에는 api-id, authorization 헤더가 필수로 포함되어야 합니다.  
* **필수 파라미터**: Body 항목 중 필수**(Required=Y)**인 파라미터를 명시했습니다.

## **1\. OAuth 인증 API**

API 사용을 위한 접근 토큰을 발급받거나 폐기하는 인증 관련 API입니다.

| API ID | API 명 | URL | Input Parameters (Request Body) |
| :---- | :---- | :---- | :---- |
| au10001 | 접근토큰 발급 | /oauth2/token | grant\_type(Y), appkey(Y), secretkey(Y) |
| au10002 | 접근토큰 폐기 | /oauth2/revoke | appkey(Y), secretkey(Y), token(Y) |

## **2\. 국내주식 조회 및 주문 API**

국내 주식의 시세, 종목 정보, 계좌 조회 및 실제 주문 실행과 관련된 REST API 그룹입니다.

### **2.1. 종목정보 (/api/dostk/stkinfo)**

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| ka10001 | 주식기본정보요청 | stk\_cd(Y) |
| ka10002 | 주식거래원요청 | stk\_cd(Y) |
| ka10003 | 체결정보요청 | stk\_cd(Y) |
| ka10013 | 신용매매동향요청 | stk\_cd(Y), dt(Y), qry\_tp(Y) |
| ka10015 | 일별거래상세요청 | stk\_cd(Y), strt\_dt(Y) |
| ka10016 | 신고저가요청 | mrkt\_tp(Y), ntl\_tp(Y), high\_low\_close\_tp(Y), stk\_cnd(Y), trde\_qty\_tp(Y), crd\_cnd(Y), updown\_incls(Y), dt(Y), stex\_tp(Y) |
| ka10017 | 상하한가요청 | mrkt\_tp(Y), updown\_tp(Y), sort\_tp(Y), stk\_cnd(Y), trde\_qty\_tp(Y), crd\_cnd(Y), trde\_gold\_tp(Y), stex\_tp(Y) |
| ka10018 | 고저가근접요청 | high\_low\_tp(Y), alacc\_rt(Y), mrkt\_tp(Y), trde\_qty\_tp(Y), stk\_cnd(Y), crd\_cnd(Y), stex\_tp(Y) |
| ka10019 | 가격급등락요청 | mrkt\_tp(Y), flu\_tp(Y), tm\_tp(Y), tm(Y), trde\_qty\_tp(Y), stk\_cnd(Y), crd\_cnd(Y), pric\_cnd(Y), updown\_incls(Y), stex\_tp(Y) |
| ka10024 | 거래량갱신요청 | mrkt\_tp(Y), cycle\_tp(Y), trde\_qty\_tp(Y), stex\_tp(Y) |
| ka10025 | 매물대집중요청 | mrkt\_tp(Y), prps\_cnctr\_rt(Y), cur\_prc\_entry(Y), prpscnt(Y), cycle\_tp(Y), stex\_tp(Y) |
| ka10026 | 고저PER요청 | pertp(Y), stex\_tp(Y) |
| ka10028 | 시가대비등락률요청 | sort\_tp(Y), trde\_qty\_cnd(Y), mrkt\_tp(Y), updown\_incls(Y), stk\_cnd(Y), crd\_cnd(Y), trde\_prica\_cnd(Y), flu\_cnd(Y), stex\_tp(Y) |
| ka10043 | 거래원매물대분석요청 | stk\_cd(Y), strt\_dt(Y), end\_dt(Y), qry\_dt\_tp(Y), pot\_tp(Y), dt(Y), sort\_base(Y), mmcm\_cd(Y), stex\_tp(Y) |
| ka10052 | 거래원순간거래량요청 | mmcm\_cd(Y), mrkt\_tp(Y), qty\_tp(Y), pric\_tp(Y), stex\_tp(Y), stk\_cd(N) |
| ka10054 | 변동성완화장치발동종목요청 | mrkt\_tp(Y), bf\_mkrt\_tp(Y), motn\_tp(Y), skip\_stk(Y), trde\_qty\_tp(Y), min\_trde\_qty(Y), max\_trde\_qty(Y), trde\_prica\_tp(Y), min\_trde\_prica(Y), max\_trde\_prica(Y), motn\_drc(Y), stex\_tp(Y), stk\_cd(N) |
| ka10055 | 당일전일체결량요청 | stk\_cd(Y), tdy\_pred(Y) |
| ka10058 | 투자자별일별매매종목요청 | strt\_dt(Y), end\_dt(Y), trde\_tp(Y), mrkt\_tp(Y), invsr\_tp(Y), stex\_tp(Y) |
| ka10059 | 종목별투자자기관별요청 | dt(Y), stk\_cd(Y), amt\_qty\_tp(Y), trde\_tp(Y), unit\_tp(Y) |
| ka10061 | 종목별투자자기관별합계요청 | stk\_cd(Y), strt\_dt(Y), end\_dt(Y), amt\_qty\_tp(Y), trde\_tp(Y), unit\_tp(Y) |
| ka10084 | 당일전일체결요청 | stk\_cd(Y), tdy\_pred(Y), tic\_min(Y), tm(N) |
| ka10095 | 관심종목정보요청 | stk\_cd(Y) |
| ka10099 | 종목정보 리스트 | mrkt\_tp(Y) |
| ka10100 | 종목정보 조회 | stk\_cd(Y) |
| ka10101 | 업종코드 리스트 | mrkt\_tp(Y) |
| ka10102 | 회원사 리스트 | 없음 |
| ka90003 | 프로그램순매수상위50요청 | trde\_upper\_tp(Y), amt\_qty\_tp(Y), mrkt\_tp(Y), stex\_tp(Y) |
| ka90004 | 종목별프로그램매매현황요청 | dt(Y), mrkt\_tp(Y), stex\_tp(Y) |
| kt20016 | 신용융자 가능종목요청 | mrkt\_deal\_tp(Y), crd\_stk\_grde\_tp(N), stk\_cd(N) |
| kt20017 | 신용융자 가능문의 | stk\_cd(Y) |

### **2.2. 시세 (/api/dostk/mrkcond)**

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| ka10004 | 주식호가요청 | stk\_cd(Y) |
| ka10005 | 주식일주월시분요청 | stk\_cd(Y) |
| ka10006 | 주식시분요청 | stk\_cd(Y) |
| ka10007 | 시세표성정보요청 | stk\_cd(Y) |
| ka10011 | 신주인수권전체시세요청 | newstk\_recvrht\_tp(Y) |
| ka10044 | 일별기관매매종목요청 | strt\_dt(Y), end\_dt(Y), trde\_tp(Y), mrkt\_tp(Y), stex\_tp(Y) |
| ka10045 | 종목별기관매매추이요청 | stk\_cd(Y), strt\_dt(Y), end\_dt(Y), orgn\_prsm\_unp\_tp(Y), for\_prsm\_unp\_tp(Y) |
| ka10046 | 체결강도추이시간별요청 | stk\_cd(Y) |
| ka10047 | 체결강도추이일별요청 | stk\_cd(Y) |
| ka10063 | 장중투자자별매매요청 | mrkt\_tp(Y), amt\_qty\_tp(Y), invsr(Y), frgn\_all(Y), smtm\_netprps\_tp(Y), stex\_tp(Y) |
| ka10066 | 장마감후투자자별매매요청 | mrkt\_tp(Y), amt\_qty\_tp(Y), trde\_tp(Y), stex\_tp(Y) |
| ka10078 | 증권사별종목매매동향요청 | mmcm\_cd(Y), stk\_cd(Y), strt\_dt(Y), end\_dt(Y) |
| ka10086 | 일별주가요청 | stk\_cd(Y), qry\_dt(Y), indc\_tp(Y) |
| ka10087 | 시간외단일가요청 | stk\_cd(Y) |
| ka90005 | 프로그램매매추이요청 시간대별 | date(Y), amt\_qty\_tp(Y), mrkt\_tp(Y), min\_tic\_tp(Y), stex\_tp(Y) |
| ka90006 | 프로그램매매차익잔고추이요청 | date(Y), stex\_tp(Y) |
| ka90007 | 프로그램매매누적추이요청 | date(Y), amt\_qty\_tp(Y), mrkt\_tp(Y), stex\_tp(Y) |
| ka90008 | 종목시간별프로그램매매추이요청 | amt\_qty\_tp(Y), stk\_cd(Y), date(Y) |
| ka90010 | 프로그램매매추이요청 일자별 | date(Y), amt\_qty\_tp(Y), mrkt\_tp(Y), min\_tic\_tp(Y), stex\_tp(Y) |
| ka90013 | 종목일별프로그램매매추이요청 | stk\_cd(Y), amt\_qty\_tp(N), date(N) |

### **2.3. 기관/외국인 (/api/dostk/frgnistt)**

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| ka10008 | 주식외국인종목별매매동향 | stk\_cd(Y) |
| ka10009 | 주식기관요청 | stk\_cd(Y) |
| ka10131 | 기관외국인연속매매현황요청 | dt(Y), mrkt\_tp(Y), netslmt\_tp(Y), stk\_inds\_tp(Y), amt\_qty\_tp(Y), stex\_tp(Y), strt\_dt(N), end\_dt(N) |

### **2.4. 업종 (/api/dostk/sect)**

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| ka10010 | 업종프로그램요청 | stk\_cd(Y) |
| ka10051 | 업종별투자자순매수요청 | mrkt\_tp(Y), amt\_qty\_tp(Y), stex\_tp(Y), base\_dt(N) |
| ka20001 | 업종현재가요청 | mrkt\_tp(Y), inds\_cd(Y) |
| ka20002 | 업종별주가요청 | mrkt\_tp(Y), inds\_cd(Y), stex\_tp(Y) |
| ka20003 | 전업종지수요청 | inds\_cd(Y) |
| ka20009 | 업종현재가일별요청 | mrkt\_tp(Y), inds\_cd(Y) |

### **2.5. 공매도 (/api/dostk/shsa)**

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| ka10014 | 공매도추이요청 | stk\_cd(Y), strt\_dt(Y), end\_dt(Y), tm\_tp(N) |

### **2.6. 순위정보 (/api/dostk/rkinfo)**

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| ka10020 | 호가잔량상위요청 | mrkt\_tp(Y), sort\_tp(Y), trde\_qty\_tp(Y), stk\_cnd(Y), crd\_cnd(Y), stex\_tp(Y) |
| ka10021 | 호가잔량급증요청 | mrkt\_tp(Y), trde\_tp(Y), sort\_tp(Y), tm\_tp(Y), trde\_qty\_tp(Y), stk\_cnd(Y), stex\_tp(Y) |
| ka10022 | 잔량율급증요청 | mrkt\_tp(Y), rt\_tp(Y), tm\_tp(Y), trde\_qty\_tp(Y), stk\_cnd(Y), stex\_tp(Y) |
| ka10023 | 거래량급증요청 | mrkt\_tp(Y), sort\_tp(Y), tm\_tp(Y), trde\_qty\_tp(Y), stk\_cnd(Y), pric\_tp(Y), stex\_tp(Y), tm(N) |
| ka10027 | 전일대비등락률상위요청 | mrkt\_tp(Y), sort\_tp(Y), trde\_qty\_cnd(Y), stk\_cnd(Y), crd\_cnd(Y), updown\_incls(Y), pric\_cnd(Y), trde\_prica\_cnd(Y), stex\_tp(Y) |
| ka10029 | 예상체결등락률상위요청 | mrkt\_tp(Y), sort\_tp(Y), trde\_qty\_cnd(Y), stk\_cnd(Y), crd\_cnd(Y), pric\_cnd(Y), stex\_tp(Y) |
| ka10030 | 당일거래량상위요청 | mrkt\_tp(Y), sort\_tp(Y), mang\_stk\_incls(Y), crd\_tp(Y), trde\_qty\_tp(Y), pric\_tp(Y), trde\_prica\_tp(Y), mrkt\_open\_tp(Y), stex\_tp(Y) |
| ka10031 | 전일거래량상위요청 | mrkt\_tp(Y), qry\_tp(Y), rank\_strt(Y), rank\_end(Y), stex\_tp(Y) |
| ka10032 | 거래대금상위요청 | mrkt\_tp(Y), mang\_stk\_incls(Y), stex\_tp(Y) |
| ka10033 | 신용비율상위요청 | mrkt\_tp(Y), trde\_qty\_tp(Y), stk\_cnd(Y), updown\_incls(Y), crd\_cnd(Y), stex\_tp(Y) |
| ka10034 | 외인기간별매매상위요청 | mrkt\_tp(Y), trde\_tp(Y), dt(Y), stex\_tp(Y) |
| ka10035 | 외인연속순매매상위요청 | mrkt\_tp(Y), trde\_tp(Y), base\_dt\_tp(Y), stex\_tp(Y) |
| ka10036 | 외인한도소진율증가상위 | mrkt\_tp(Y), dt(Y), stex\_tp(Y) |
| ka10037 | 외국계창구매매상위요청 | mrkt\_tp(Y), dt(Y), trde\_tp(Y), sort\_tp(Y), stex\_tp(Y) |
| ka10038 | 종목별증권사순위요청 | stk\_cd(Y), strt\_dt(Y), end\_dt(Y), qry\_tp(Y), dt(Y) |
| ka10039 | 증권사별매매상위요청 | mmcm\_cd(Y), trde\_qty\_tp(Y), trde\_tp(Y), dt(Y), stex\_tp(Y) |
| ka10040 | 당일주요거래원요청 | stk\_cd(Y) |
| ka10042 | 순매수거래원순위요청 | stk\_cd(Y), qry\_dt\_tp(Y), pot\_tp(Y), sort\_base(Y), strt\_dt(N), end\_dt(N), dt(N) |
| ka10053 | 당일상위이탈원요청 | stk\_cd(Y) |
| ka10062 | 동일순매매순위요청 | strt\_dt(Y), mrkt\_tp(Y), trde\_tp(Y), sort\_cnd(Y), unit\_tp(Y), stex\_tp(Y), end\_dt(N) |
| ka10065 | 장중투자자별매매상위요청 | trde\_tp(Y), mrkt\_tp(Y), orgn\_tp(Y) |
| ka10098 | 시간외단일가등락율순위요청 | mrkt\_tp(Y), sort\_base(Y), stk\_cnd(Y), trde\_qty\_cnd(Y), crd\_cnd(Y), trde\_prica(Y) |
| ka90009 | 외국인기관매매상위요청 | mrkt\_tp(Y), amt\_qty\_tp(Y), qry\_dt\_tp(Y), stex\_tp(Y), date(N) |

### **2.7. 차트 (/api/dostk/chart)**

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| ka10079 | 주식틱차트조회요청 | stk\_cd(Y), tic\_scope(Y), upd\_stkpc\_tp(Y) |
| ka10080 | 주식분봉차트조회요청 | stk\_cd(Y), tic\_scope(Y), upd\_stkpc\_tp(Y) |
| ka10081 | 주식일봉차트조회요청 | stk\_cd(Y), base\_dt(Y), upd\_stkpc\_tp(Y) |
| ka10082 | 주식주봉차트조회요청 | stk\_cd(Y), base\_dt(Y), upd\_stkpc\_tp(Y) |
| ka10083 | 주식월봉차트조회요청 | stk\_cd(Y), base\_dt(Y), upd\_stkpc\_tp(Y) |
| ka10094 | 주식년봉차트조회요청 | stk\_cd(Y), base\_dt(Y), upd\_stkpc\_tp(Y) |
| ka20004 | 업종틱차트조회요청 | inds\_cd(Y), tic\_scope(Y) |
| ka20005 | 업종분봉조회요청 | inds\_cd(Y), tic\_scope(Y) |
| ka20006 | 업종일봉조회요청 | inds\_cd(Y), base\_dt(Y) |
| ka20007 | 업종주봉조회요청 | inds\_cd(Y), base\_dt(Y) |
| ka20008 | 업종월봉조회요청 | inds\_cd(Y), base\_dt(Y) |
| ka20019 | 업종년봉조회요청 | inds\_cd(Y), base\_dt(Y) |

### **2.8. 대차거래 (/api/dostk/slb)**

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| ka10068 | 대차거래추이요청 | all\_tp(Y), strt\_dt(N), end\_dt(N) |
| ka10069 | 대차거래상위10종목요청 | strt\_dt(Y), mrkt\_tp(Y), end\_dt(N) |
| ka20068 | 대차거래추이요청(종목별) | stk\_cd(Y), all\_tp(N), strt\_dt(N), end\_dt(N) |
| ka90012 | 대차거래내역요청 | dt(Y), mrkt\_tp(Y) |

### **2.9. 계좌 (/api/dostk/acnt)**

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| ka10072 | 일자별종목별실현손익요청\_일자 | stk\_cd(Y), strt\_dt(Y) |
| ka10073 | 일자별종목별실현손익요청\_기간 | stk\_cd(Y), strt\_dt(Y), end\_dt(Y) |
| ka10074 | 일자별실현손익요청 | strt\_dt(Y), end\_dt(Y) |
| ka10075 | 미체결요청 | all\_stk\_tp(Y), trde\_tp(Y), stex\_tp(Y), stk\_cd(N) |
| ka10076 | 체결요청 | qry\_tp(Y), sell\_tp(Y), stex\_tp(Y), stk\_cd(N), ord\_no(N) |
| ka10077 | 당일실현손익상세요청 | stk\_cd(Y) |
| ka10085 | 계좌수익률요청 | stex\_tp(Y) |
| ka10088 | 미체결 분할주문 상세 | ord\_no(Y) |
| ka10170 | 당일매매일지요청 | ottks\_tp(Y), ch\_crd\_tp(Y), base\_dt(N) |
| kt00001 | 예수금상세현황요청 | qry\_tp(Y) |
| kt00002 | 일별추정예탁자산현황요청 | start\_dt(Y), end\_dt(Y) |
| kt00003 | 추정자산조회요청 | qry\_tp(Y) |
| kt00004 | 계좌평가현황요청 | qry\_tp(Y), dmst\_stex\_tp(Y) |
| kt00005 | 체결잔고요청 | dmst\_stex\_tp(Y) |
| kt00007 | 계좌별주문체결내역상세요청 | qry\_tp(Y), stk\_bond\_tp(Y), sell\_tp(Y), dmst\_stex\_tp(Y), ord\_dt(N), stk\_cd(N), fr\_ord\_no(N) |
| kt00008 | 계좌별익일결제예정내역요청 | strt\_dcd\_seq(N) |
| kt00009 | 계좌별주문체결현황요청 | stk\_bond\_tp(Y), mrkt\_tp(Y), sell\_tp(Y), qry\_tp(Y), dmst\_stex\_tp(Y), ord\_dt(N), stk\_cd(N), fr\_ord\_no(N) |
| kt00010 | 주문인출가능금액요청 | stk\_cd(Y), trde\_tp(Y), uv(Y), io\_amt(N), trde\_qty(N), exp\_buy\_unp(N) |
| kt00011 | 증거금율별주문가능수량조회요청 | stk\_cd(Y), uv(N) |
| kt00012 | 신용보증금율별주문가능수량조회요청 | stk\_cd(Y), uv(N) |
| kt00013 | 증거금세부내역조회요청 | 없음 |
| kt00015 | 위탁종합거래내역요청 | strt\_dt(Y), end\_dt(Y), tp(Y), gds\_tp(Y), dmst\_stex\_tp(Y), stk\_cd(N), crnc\_cd(N), frgn\_stex\_code(N) |
| kt00016 | 일별계좌수익률상세현황요청 | fr\_dt(Y), to\_dt(Y) |
| kt00017 | 계좌별당일현황요청 | 없음 |
| kt00018 | 계좌평가잔고내역요청 | qry\_tp(Y), dmst\_stex\_tp(Y) |

### **2.10. ELW (/api/dostk/elw)**

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| ka10048 | ELW일별민감도지표요청 | stk\_cd(Y) |
| ka10050 | ELW민감도지표요청 | stk\_cd(Y) |
| ka30001 | ELW가격급등락요청 | flu\_tp(Y), tm\_tp(Y), tm(Y), trde\_qty\_tp(Y), isscomp\_cd(Y), bsis\_aset\_cd(Y), rght\_tp(Y), lpcd(Y), trde\_end\_elwskip(Y) |
| ka30002 | 거래원별ELW순매매상위요청 | isscomp\_cd(Y), trde\_qty\_tp(Y), trde\_tp(Y), dt(Y), trde\_end\_elwskip(Y) |
| ka30003 | ELWLP보유일별추이요청 | bsis\_aset\_cd(Y), base\_dt(Y) |
| ka30004 | ELW괴리율요청 | isscomp\_cd(Y), bsis\_aset\_cd(Y), rght\_tp(Y), lpcd(Y), trde\_end\_elwskip(Y) |
| ka30005 | ELW조건검색요청 | isscomp\_cd(Y), bsis\_aset\_cd(Y), rght\_tp(Y), lpcd(Y), sort\_tp(Y) |
| ka30009 | ELW등락율순위요청 | sort\_tp(Y), rght\_tp(Y), trde\_end\_skip(Y) |
| ka30010 | ELW잔량순위요청 | sort\_tp(Y), rght\_tp(Y), trde\_end\_skip(Y) |
| ka30011 | ELW근접율요청 | stk\_cd(Y) |
| ka30012 | ELW종목상세정보요청 | stk\_cd(Y) |

### **2.11. ETF (/api/dostk/etf)**

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| ka40001 | ETF수익율요청 | stk\_cd(Y), etfobjt\_idex\_cd(Y), dt(Y) |
| ka40002 | ETF종목정보요청 | stk\_cd(Y) |
| ka40003 | ETF일별추이요청 | stk\_cd(Y) |
| ka40004 | ETF전체시세요청 | txon\_type(Y), navpre(Y), mngmcomp(Y), txon\_yn(Y), trace\_idex(Y), stex\_tp(Y) |
| ka40006 | ETF시간대별추이요청 | stk\_cd(Y) |
| ka40007 | ETF시간대별체결요청 | stk\_cd(Y) |
| ka40008 | ETF일자별체결요청 | stk\_cd(Y) |
| ka40009 | ETF시간대별체결요청 | stk\_cd(Y) |
| ka40010 | ETF시간대별추이요청 | stk\_cd(Y) |

### **2.12. 테마 (/api/dostk/thme)**

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| ka90001 | 테마그룹별요청 | qry\_tp(Y), date\_tp(Y), flu\_pl\_amt\_tp(Y), stex\_tp(Y), stk\_cd(N), thema\_nm(N) |
| ka90002 | 테마구성종목요청 | thema\_grp\_cd(Y), stex\_tp(Y), date\_tp(N) |

### **2.13. 주문 (/api/dostk/ordr)**

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| kt10000 | 주식 매수주문 | dmst\_stex\_tp(Y), stk\_cd(Y), ord\_qty(Y), trde\_tp(Y), ord\_uv(N), cond\_uv(N) |
| kt10001 | 주식 매도주문 | dmst\_stex\_tp(Y), stk\_cd(Y), ord\_qty(Y), trde\_tp(Y), ord\_uv(N), cond\_uv(N) |
| kt10002 | 주식 정정주문 | dmst\_stex\_tp(Y), orig\_ord\_no(Y), stk\_cd(Y), mdfy\_qty(Y), mdfy\_uv(Y), mdfy\_cond\_uv(N) |
| kt10003 | 주식 취소주문 | dmst\_stex\_tp(Y), orig\_ord\_no(Y), stk\_cd(Y), cncl\_qty(Y) |

### **2.14. 신용주문 (/api/dostk/crdordr)**

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| kt10006 | 신용 매수주문 | dmst\_stex\_tp(Y), stk\_cd(Y), ord\_qty(Y), trde\_tp(Y), ord\_uv(N), cond\_uv(N) |
| kt10007 | 신용 매도주문 | dmst\_stex\_tp(Y), stk\_cd(Y), ord\_qty(Y), trde\_tp(Y), crd\_deal\_tp(Y), ord\_uv(N), crd\_loan\_dt(N), cond\_uv(N) |
| kt10008 | 신용 정정주문 | dmst\_stex\_tp(Y), orig\_ord\_no(Y), stk\_cd(Y), mdfy\_qty(Y), mdfy\_uv(Y), mdfy\_cond\_uv(N) |
| kt10009 | 신용 취소주문 | dmst\_stex\_tp(Y), orig\_ord\_no(Y), stk\_cd(Y), cncl\_qty(Y) |

## **3\. 실시간 시세 API (WebSocket)**

실시간 데이터 수신을 위한 API 그룹입니다. 모든 실시간 API는 wss://api.kiwoom.com:10000/api/dostk/websocket 주소를 사용하며, 등록(REG) 또는 해지(REMOVE) 요청을 통해 데이터를 수신합니다.

| API ID | API 명 | Input Parameters (Request Body) |
| :---- | :---- | :---- |
| 00 | 주문체결 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 04 | 잔고 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0A | 주식기세 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0B | 주식체결 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0C | 주식우선호가 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0D | 주식호가잔량 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0E | 주식시간외호가 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0F | 주식당일거래원 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0G | ETF NAV | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0H | 주식예상체결 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0J | 업종지수 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0U | 업종등락 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0g | 주식종목정보 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0m | ELW 이론가 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0s | 장시작시간 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0u | ELW 지표 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 0w | 종목프로그램매매 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| 1h | VI발동/해제 | trnm(Y), grp\_no(Y), refresh(Y), data(\[item(N), type(Y)\]) |
| ka10171 | 조건검색 목록조회 | trnm(Y) |
| ka10172 | 조건검색 요청 일반 | trnm(Y), seq(Y), search\_type(Y), stex\_tp(Y), cont\_yn(N), next\_key(N) |
| ka10173 | 조건검색 요청 실시간 | trnm(Y), seq(Y), search\_type(Y), stex\_tp(Y) |
| ka10174 | 조건검색 실시간 해제 | trnm(Y), seq(Y) |

