# <물리 계층>
    <데이터 링크 계층 (Data Link Layer)> 에서 IP 패킷은 이더넷 프레임으로 캡슐화
    이더넷 헤더:
    - 목적지 MAC 주소: 00:1A:2B:3C:4D:5E
    - 출발지 MAC 주소: 01:2B:3C:4D:5E:6F
    - 유형: 0x0800 (IPv4)

        <네트워크 계층 (Network Layer)> 에서 TCP 세그먼트는 IP 패킷으로 캡슐화 : 이더넷 프레임의 페이로드 
        IP 헤더:
        - 버전: 4 (IPv4)
        - 헤더 길이: 20 bytes
        - 서비스 유형: 0
        - 전체 길이: 1500 bytes
        - 식별자: 54321
        - 플래그: 0
        - 프래그먼트 오프셋: 0
        - TTL: 64
        - 프로토콜: 6 (TCP)
        - 헤더 체크섬: 0x5678
        - 출발지 IP 주소: 192.0.2.1
        - 목적지 IP 주소: 203.0.113.1

            <전송 계층 (Transport Layer)> 에서 <응용 계층의 데이터(HTTP 요청)>는 TCP 세그먼트로 캡슐화 : IP 패킷의 페이로드
            TCP 헤더:                         
            - 출발지 포트: 12345
            - 목적지 포트: 80
            - 순서 번호: 123456789
            - 확인 응답 번호: 987654321
            - 플래그: SYN, ACK 등
            - 윈도우 크기: 8192
            - 체크섬: 0x1234
            - 긴급 포인터: 0
            - 옵션: (예: 최대 세그먼트 크기)
                                                                                    
                <응용 계층 (Application Layer)>  : TCP 세그먼트의 페이로드
                                                        응용계층만 암호화. 이 위로는 라우팅에 필요한 정보들이기 때문에 암호화하지 않음
                응용계층 예시1 HTTP 프로토콜                                        
                GET /users/123?details=full HTTP/1.1   : 요청 메서드(GET), URL 경로, 쿼리 파라미터, HTTP 버전(HTTP/1.1)
                Host: example.com           : 요청 헤더 = Host, Authorization, Content-Type 
                Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
                Content-Type: application/json

                {                                       : 요청바디 = JSON, XML, HTML, 폼 데이터 등 다양한 형식
                  "email": "user@example.com",
                  "password": "securepassword"
                }
                응용계층 예시2 웹소켓 프로토콜 : : TCP 세그먼트의 페이로드
                웹소켓 프레임:
                 FIN, RSV1-3, Opcode, Mask (웹소켓 헤더 필드)
                    페이로드 길이
                    마스킹 키 (클라이언트가 서버로 보내는 경우)
                    페이로드 데이터 (메시지 데이터)


    이더넷 트레일러 (FCS):
    - 프레임 체크 시퀀스 (FCS): 0x9A7C (데이터의 무결성을 확인하기 위한)
    

  
  
# 응용계층 HTTP와 웹소켓 차이점 요약
    상태 관리:
    HTTP: 비연결성 프로토콜로, 각 요청마다 별도의 연결이 생성되고 종료됩니다. 
    상태 유지가 필요하면 쿠키나 세션, JWT 토큰 등을 사용해야 합니다.
    웹소켓: 지속적인 연결을 유지하며, 상태를 유지하면서 양방향 통신이 가능합니다.

    데이터 전송 방식:
    HTTP: 주로 요청-응답 주기에 따른 요청 바디를 사용하여 데이터를 전송합니다.
    웹소켓: 지속적인 연결을 통해 JSON 등의 형식으로 메시지를 전송하며, 실시간 통신이 가능합니다.

    헤더와 메타데이터:
    HTTP: 요청과 응답에 메타데이터를 포함할 수 있는 HTTP 헤더를 사용합니다
    웹소켓: 웹소켓 연결 시 초기 HTTP 요청에서만 헤더가 사용되며, 이후에는 데이터 전송에 주로 메시지 바디만 사용됩니다.

    사용 사례:
    HTTP: 주로 RESTful API 호출, 페이지 로드, 데이터 제출 등에 사용됩니다.
    웹소켓: 실시간 채팅, 실시간 게임, 주식 가격 업데이트 등 지속적이고 양방향이 필요한 경우에 사용됩니다.
    
    
# HTTP 요청 헤더 : JWT 토큰(이메일, 닉네임, 세션 만료시간, 권한 정보)
비밀번호와 같은 민감한 정보는 절대 토큰에 포함되지 않습니다.

  - 토큰에 서명(signature)이 포함되어 있어, 데이터의 무결성과 출처를 검증할 수 있습니다. 
  이는 데이터가 변조되지 않았음을 확인할 수 있는 중요한 보안 기능입니다.
  - 토큰 기반 인증과 권한 부여를 쉽게 구현할 수 있습니다. 토큰에 사용자의 권한 정보, 세션 상태 등을 포함할 수 있습니다.
  - 여러 API 간의 통신에서 인증 정보를 쉽게 전달할 수 있습니다.

  - 토큰이 클라이언트 측에 저장되기 때문에, 클라이언트에서의 관리가 중요합니다. 예를 들어, 로컬 스토리지나 세션 스토리지에 저장할 때 보안에 신경 써야 합니다.
  - JWT 토큰은 보통 일정한 만료 시간을 가지며, 만료된 토큰을 갱신하는 메커니즘이 필요합니다.
  - 토큰 자체의 크기가 클 경우, 네트워크 성능에 영향을 미칠 수 있습니다.
  
# HTTP 요청바디 : 이메일, 비번, 닉네임
  - 데이터의 크기나 형식에 제한이 적습니다.
  - HTTP 메서드(POST, PUT 등)와 함께 사용하여 데이터를 생성하거나 업데이트하는 데 자연스럽습니다.
  - 요청과 응답이 명확하게 구분되어, 상태 변화 작업을 수행할 때 직관적입니다.
   - 민감한 정보가 포함된 경우, 서버와 클라이언트 모두에서 보안 관리를 철저히 해야 합니다.
  - 서버 로그나 네트워크 로그에 요청 바디의 내용이 기록되지 않도록 주의해야 합니다.
  
# HTTP 경로파라미터 또는 쿼리 파라미터 : 웹소켓 연결신청
 클라이언트가 웹소켓 연결을 시도할 때, 필요한 정보가 table_id와 client_id뿐이라면, 
 이를 경로 파라미터나 쿼리 파라미터로 전달할 수 있습니다. 이렇게 하면 웹소켓 연결이 수립될 때 
 서버는 해당 정보를 경로 또는 쿼리에서 바로 추출할 수 있습니다.

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws/{table_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, table_id: int, client_id: int):
    await websocket.accept()
    print(f"Client {client_id} connected to table {table_id}")
    try:
        while True:
            data = await websocket.receive_text()
            # 받은 데이터를 처리
            print(f"Received data from client {client_id} at table {table_id}: {data}")
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected from table {table_id}")
```

# 웹소켓 메시지 내의 JSON 데이터 : 클라이언트-서버 데이터 송수신




