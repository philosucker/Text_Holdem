# Text_Holdem


## test application for Texas Holdem game Text version

### 현재 디렉토리 구조

./testapp  
├── main.py  
├── database  
│   └── connection.py  
│   └── crud.py  
├── models  
│   ├── events.py  
│   └── users.py  
├── routes  
│   ├── events.py  
│   └── users.py  
└── tests  
    ├── test_app1.py  
    └── test_app2.py  
  
#### 진척상황 
- 05.24.2024
  - FastAPI 애플리케이션-mongoDB 연동
  - 클라이언트 측에서 필요한 일부 기능 구현
    - 유저 등록, 유저 로그인, 유저 이벤트 생성/변경/삭제,조회
- 05.26.2024  
  - pytest 완료  
