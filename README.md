# Texture_Holdem

## Description: 
- An application that allows multiplayer play using an artificial intelligence agent  
    while maintaining the realism of throwing and receiving chips in an actual hold'em game.  
---
### Project Objectives
1. Develop a Texas Holdem game application that supports multiplayer with online.  
2. Train AI agents capable of playing Texas Holdem and integrate them into the application.
     
### Project Background
1. The project aims to provide more people with an accessible and enjoyable way to experience Texas Holdem.  
   - **Characteristics of Existing Holdem Applications.**
     
          1) High Risk of Gambling Addiction: Often perceived as mere gambling.  
          2) High Entry Barrier: The rules are not easy to learn.  
          3) Lack of Solo Play Options: There are no holdem game applications yet that include plausible AI agents.
         
2. Texas Holdem presents a valuable opportunity for development  
     using Large Language Models (LLM) and Deep Reinforcement Learning (DRL).  
    
   - Texas Holdem is an **imperfect information game** with strategic simulation elements.  
   - Developing AI capable of making optimal decisions and bluffing with limited information requires  
        advanced techniques in multimodal input processing (text, images, video, sound).  
   
          1) Notable "Starcraft"(Real-Time Strategy Game) pro-gamers like Hong Jin-ho and Lim Yo-hwan
               have transitioned to professional Holdem players as of June 2024.
   
          2) Professional "Go"(Turn-Based Strategy Game) player Lee Sedol
               has also become a Holdem player as of June 2024.  
---
### Project Plan
1. **from April until June in 2024:**
   - Leaning Texas Holdem game.  
   - Studying Python programming, FastAPI and Unity.    
   - Designing overall architecture.    

2. **from June until August in 2024:**    
   - Develop a Texas Holdem Game Application: Create an application with a sleek and user-friendly UI.
      
3. **from september until october in 2024**        
   - Develop an AI Agent for Holdem application:  

     1) Utilize LLM APIs to create an LLM model for playing Holdem.  
     2) Integrate the LLM model into the Holdem application to collect data for reinforcement learning.  
  
### Requirement Skills
1. Domain Knowledge : No Limit Texas Holdem  
2. Programming Language : Python, C#  
3. Backend : FastAPI  
4. Database : MySQL(SQLAlchemy), MongoDB(Beanie)  
5. Application : Unity
7. Network Programming : Nginx, HTTP, Web Socket, Message Broker(RabbitMQ)  
8. Asyncrnous Programming : AsyncIO  
9. Deep Learning : LLM, DRL for AI Holdem Agent  
10. DevOps : Docker, Kubernetes  

### "How to implement Texas Holdem game? It's so complicated;("  
#### I made reference for you:) Please refer to the documents in [docs](https://github.com/philosucker/Text_Holdem/tree/main/docs) directory  
---
## Development Log


08.06.2024  
- completed implementaition of reception, floor, dealer server algorithms  
- completed implementaion of floor server and dealer server connection with message broker  
  
08.03.2024  
- completed implementaion of reception server and floor server connection with message broker  

07.31.2024  
- Completed implementation of floor server and client connection via websocket

07.30.2024    
- Concurrency test for CPU bound / disk I/O bound / CPU + diskI/O bound  
- Planned to additional test for network I/O bound test after back-end development.

07.29.2024  
- Completed implementation of dealer server and client connection via websocket
  
07.24.2024  
- Completed MicroService Architecture design.   
  <img src="https://github.com/user-attachments/assets/0a69cabd-80b6-4262-92fe-d7f274054019" width="1000" />   

### 07.22.2024 Started development of the backend  
    - Implementing reception, floor, and dealer server algorithms  
    - Implementing server-client connections  
    - Implementing communication between servers  
   
07.19.2024   
- Started learning AsyncIO.   

07.18.2024    
- Started learning message broker.  

07.16.2024   
- Started learning socket programming. (WebSocket)


### 07.12.2024 Completed implementation of "dealer algorithm"
  
07.10.2024    
- Completed implementation of "side pot" creation and management algorithm.    
- Completed implementation of  "pot award" algorithm.

07.05.2024  
- Completed implementation of “end condition” algorithm.  
- Implement test case DB and test functions and start dealer logic testing.

07.02.2024  
- Completed implementation of “Showdown” ranking comparison algorithm.

07.01.2024  
- Review of “showdown” and “pot award” connection logic.
  
06.28.2024  
- Review “end condition” and “showdown” connection logic.

06.27.2024  
- Review “pot creation and management” logic.  
  
06.26.2024  
- Review “end condition” logic.  
  
06.25.2024  
- Completed implementation of “bet”, “raise”, “all-in”, “call”, “check”, and “fold action” algorithms.  
  
### 06.24.2024 Started development of texas holdem dealer algorithm.  
    - Implementing an algorithm that acts as a dealer in a Texas Hold'em game
    - Implementing calculations of the types of actions a user can make each turn
    - Implementing calculations of conditions for ending each street and hand
    - Implementing calculations of main pot and side pot
    - Implementing showdown
    - Implementing pot distribution
    
06.19.2024  
- Completed Monolithic Architecture design.  
- Planned to upgrade to MicroService Architecture after development of texas holdem dealer algorithm.  
  <img src="https://github.com/user-attachments/assets/12189a16-e15f-4cc3-abf6-865843d3a721" width="600" />  
  
06.10.2024  
- Started learning Unity.  
  
06.08.2024  
- Started Designing the game architecture.   
- Conceptualized the core logic for the Holdem game application.  
    
06.04.2024  
- Fully mastered the rules of Texas Holdem.  
  
05.14.2024   
- Started studying FastAPI for backend development  
  
04.24.2024   
- Started learning the rules of Texas Holdem.  
