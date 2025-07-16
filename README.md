[변경 가능 파일]
- topics.json -> 행동주의 관련 키워드 추가/삭제 (각 topic 당 최대 10개 전송)
- companies.json -> 종목명 추가/삭제 
- newsbot.py -> 종목명 검색 결과 중, ACTIVISM_KEYWORDS 중 하나라도 포함되어야 전송
    -  ACTIVISM_KEYWORDS 리스트 내부만 변경 가능!! 다른 부분 변경 시 작동 안될 수 있음 

[변경 방법]
  1) 파일 선택
  2) 우측 상단 연필모양 눌러서 수정
  3) 수정 후 우측 상단 초록색 버튼 "commit changes"
  4) 팝업창에서 한 번 더 commit changes

    예시: ["삼성", "LG", "현대"]
      - 공백은 인식 안됨
      - 항상 따옴표 안에 텍스트 + 콤마로 분리 (아닐 시 오류)

[관리용 파일]
- subscribers.json : 텔레그램 봇 구독자 명단 
- sent_articles.json : 보낸 기사 링크 기록 
