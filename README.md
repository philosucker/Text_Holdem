# Text_Holdem


## : Description: A text-based application for playing Texas Holdem


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

#### Requirement Skills
1. Python : FastAPI, AsyncIO (for backend)
2. C# and Design : Unity 2022 (for smartphone application)
3. Networking (websocket etc.)
4. Docker (for distribution)

#### How to implement Texas Holdem game? It's so complicated.  
I made reference for you : [Implementation Rules/rule.md](https://github.com/philosucker/Text_Holdem/blob/main/Implementation%20Rules/rule.md)

#### Progress
  
04.24.2024   
   - Began studying the rules of Texas Holdem. 
    
05.14.2024   
   - Started learning FastAPI for backend development  
   - Began developing the backend for the Holdem game.  
  
   - 05.24.2024  
      - Completed integration of FastAPI application with MongoDB.  
   - 05.26.2024  
      - Completed pytest.  
        
06.04.2024  
- Fully mastered the rules of Texas Holdem.  
   
06.08.2024  
   - Started Designing the game architecture.  
   - Conceptualized the core logic for the Holdem game application.  
     
06.10.2024  
- Started learning Unity.  
  
06.19.2024  
- Architecture design completed  
![홀덤-2](https://github.com/philosucker/Text_Holdem/assets/65852355/9219939e-fff9-4f3f-885f-d25b718339c0)

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
  

    

