# Text_Holdem


## : Description: A text-based application for playing Texas Holdem

### 프로젝트 목표
1. 온라인에서 최소 6인 이상이 함께 멀티 플레이가 가능한 Texas Holdem 게임 애플리케이션 개발  
2. Texas Holdem 을 플레이 할 수 있는 AI 에이전트 학습 및 애플리케이션과의 통합  

#### 프로젝트 기획 배경
1. 더 많은 사람들이 친근하고 즐겁게 텍사스 홀덤을 접해볼 수 있는 기회 제공  
   - 현재 플레이가능한 홀덤 애플리케이션의 특징  
         1) 사행성이 짙음 : 단순한 도박이라는 인식  
         2) 진입장벽이 높음 : 게임 룰 숙지가 쉽지 않음  
         3) 혼자서 할 수 없음 : 홀덤 특성상 반드시 최소 3인 이상 필요. 홀덤 AI가 추가된 게임은 아직까지 없음
     
2. 텍사스 홀덤은 LLM과 DRL을 적용해 개발해볼 여지가 많은 분야임  
    - 텍사스 홀덤은 불완전 정보게임으로서 전략시뮬레이션 게임 요소를 가지고 있음  
        1) 스타크래프트(실시간 전략시뮬레이션) : 홍진호, 임요환 등 유명 프로게이머가 현재(2024년 6월 기준) 전문 홀덤 선수로 활약 중  
        2) 바둑(턴제 전략시뮬레이션) : 프로 바둑기사였던 이세돌도 현재(2024년 6월 기준) 홀덤 플레이어로 전향  
    - 텍스트, 이미지, 영상, 소리 등 멀티모달 입력을 바탕으로 제한된 정보만으로 최선의 추론 및 거짓말을 해낼 수 있는 AI 기술이 요구됨  

#### 프로젝트 계획
1. 세련되고 친근한 UI를 가진 텍사스 홀덤 게임 애플리케이션 개발 (아래 진척상황 참고)
2. 최종 목표인 홀덤 AI 에이전트 개발을 위한 준비
   1) 임의로 주어진 확률분포에 따라 홀덤을 플레이하는 고정확률모델 개발
   2) LLM API를 활용해 홀덤을 플레이하는 LLM 모델 개발
   3) 고정확률모델과 LLM 모델을 홀덤 애플리케이션에 넣어 강화학습을 위한 데이터 수집

### Project Objectives
1. Develop a Texas Holdem game application that supports multiplayer with at least 6 players online.  
2. Train AI agents capable of playing Texas Holdem and integrate them into the application.
     
#### Project Background
1. The project aims to provide more people with an accessible and enjoyable way to experience Texas Holdem.  
   - Characteristics of Existing Holdem Applications  
      1) High Risk of Gambling Addiction: Often perceived as mere gambling.  
      2) High Entry Barrier: The rules are not easy to learn.  
      3) Lack of Solo Play Options: Requires at least three players; there are no games yet that include AI players.
         
2. Texas Holdem presents a valuable opportunity for development using Large Language Models (LLM) and Deep Reinforcement Learning (DRL).  
   - Texas Holdem is an imperfect information game with strategic simulation elements:  
      1) Real-Time Strategy Games: Notable Stargraft pro-gamers like Hong Jin-ho and Lim Yo-hwan have transitioned to professional Holdem players as of June 2024.  
      2) Turn-Based Strategy Games: Professional Go player Lee Sedol has also become a Holdem player as of June 2024.  
   - Developing AI capable of making optimal decisions and bluffing with limited information requires advanced techniques in multimodal input processing (text, images, video, sound).  
  
#### Project Plan
1. Develop a Texas Holdem Game Application: Create an application with a sleek and user-friendly UI (see progress below).  
2. Prepare for AI Agent Development:  
1) Develop a fixed-probability model for playing Holdem based on arbitrary probability distributions.  
2) Utilize LLM APIs to create an LLM model for playing Holdem.  
3) Integrate the fixed-probability and LLM models into the Holdem application to collect data for reinforcement learning.  

#### Progress
  
04.24.2024   
   - Began studying the rules of Texas Holdem. 
    
05.14.2024   
   - Started learning FastAPI for backend development  
   - Began developing the backend for the Holdem game.  
  
   05.24.2024  
      - Completed integration of FastAPI application with MongoDB.  
   05.26.2024  
      - Completed pytest.  
        
06.04.2024  
- Fully mastered the rules of Texas Holdem.  
   
06.08.2024  
   - Designed the game architecture.  
   - Conceptualized the core logic for the Holdem game application.  
     
06.10.2024  
- Started learning Unity.  
  
06.19.2024  
![홀덤-2](https://github.com/philosucker/Text_Holdem/assets/65852355/f6e62c2d-26bc-4b8f-b940-0d1dc0f67742)

### Current Directory Structure

./app  
├── main.py  
├── mongod.conf  
├── .env  
├── auth  
│   └── authenticate.py  
│   └── hash_password.py  
│   └── jwt_handler.py  
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
- 04.24.2024  
  - 홀덤 게임 룰 공부 시작  
    
- 05.14.2024  
  - FastAPI 공부 시작
  - 홀덤 백엔드 개발 시작  
  
    - 05.24.2024  
      - FastAPI 애플리케이션-mongoDB 연동 완료  
    - 05.26.2024  
      - pytest 완료  
          
- 06.04.2024
  - 홀덤 게임 룰 완전 숙지
  
- 06.08.2024
  - 게임 아키텍쳐 구상 
  - 홀덤 게임 애플리케이션 핵심 로직 구상 
  
- 06.10.2024
  - Unity 공부 시작
    

