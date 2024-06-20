# 1번 Manager 인스턴스
pass  

# 2번 Floor 인스턴스
    1. 회원 가입 후 로그인시 스택 100으로 초기화
    2. 1/2 달러 게임, 스택 100 이상 참여 가능 기능
    3. 5/10 달러 게임, 스택 500 이상 참여 가능 기능
        (later) 
        4. 바이인 기능 
  
# 3번 Dealer 인스턴스 
## 한 핸드의 진행과정
### 1. 초기화
    1) 유저 플레이 순서 설정 : 랜덤
        (later)
        a. dealer 인스턴스의 초기화 함수에서 해당 게임을 위해 계산했던 플레이 순서 정보와,
           게임 종료 직전 남아 있던 라이브 유저 명단을 floor 인스턴스로 넘기고,
           기존 방에서 게임이 계속 될 때 새로운 dealer 인스턴스에게 위 두 데이터를 전달
        b. 기존 게임방에 이어서 플레이 하는 유저의 포지션 변경. 포지션 순서가 시계방향으로 한칸씩 이동
        c. 기존 게임방에 참여 대기한 유저는 SB, 딜러를 제외한 포지션 배정
    
    3) 유저별 stack 설정 : 랜덤
    
    4) main pot 설정 : 0
    
    5) Low Stakes : SB 1$, BB 2$ 블라인드 포스팅, 각각 스택에서 차감,
    
    6) 카드 셔플 및 딜링 : 랜덤, 각 유저의 스타팅 카드 정보 따로 기록


### 2. 프리플롭 루프
    UTG 부터 액션 시작
    BB에 한해 옵션 구현
      옵션 : BB 이후로 UTG부터 다시 BB차례가 되기 전까지 
            모두 수비형 액션을 한 경우(short all-in 포함) 공격형 액션이 하나도 없었던 경우에만 
            BB에게 자기자신의 오픈에 대해 레이즈 할 수 있는 기회 제공. 
            여기서 minimum raise는 open bet
            (자신이 오픈한 레이즈에 대해 리레이즈 할 수 있는 유일한 예외)
            
### 3. 플롭 루프
    딜러 : 버닝, 플롭(카드 세장 테이블에 오픈)
    SB 부터 액션 시작
      
### 4. 턴 루프
    딜러 : 버닝, 턴(카드 네장 테이블에 오픈)
    SB 부터 액션 시작
    
### 5. 리버 루프
    딜러 : 버닝, 리버(카드 다섯장 테이블에 오픈)
    SB 부터 액션 시작 
    
### 6. 쇼다운  루프
    활성화된 플레이어들만 스타팅 카드 오픈 
    핸드 오픈 순서 : (아래 참고)
    핸드비교 :
        랭크 비교 알고리즘 실행,  승자결정
            랭크 비교 알고리즘
            
            9 Ranks
            하이카드
            원페어
            투페어
            쓰리오브어카인드
            스트레이트
            플러쉬
            풀하우스
            포오브어카인드
            스트레이트플러쉬
             
            1.
            테이블링한 플레이어들의 각 스타팅카드 2장과 홀카드 5장을 합쳐
            위 9개에 해당하는 것이 있는 지 확인해
            내림차순 정렬
             
            2.
            플레이어중 겹치는 랭크가 있는 경우
            랭크마다 승자를 가리는 기준을 적용해 내림차순 정렬
             
            원페어끼리 붙는 경우
            1. 내림차순 정렬
            2. 숫자가 높은 카드가 있는 쪽이 승
            3. 숫자가 모두 같을 경우, 나머지 세장의 키커를 하나씩 비교해 숫자가 높은쪽이 승
            (무승부 가능)
             
            투페어끼리 붙는 경우
            1. 내림차순 정렬
            2. 숫자가 높은 페어가 있는 쪽이 승
            3. 두 페어 모두 숫자가 같을 경우, 남은 한장의 키커를 비교해 숫자가 높은 쪽이 승
            (무승부 가능)
             
            쓰리오브어카인드 끼리 붙는 경우
            Set : 핸드2 커뮤니티1
            Trips : 핸드1 커뮤니티2
            셋인 경우, 셋 끼리 붙는 경우는 불가
            셋보다 낮은 랭크는 무조건 셋 승, 셋보다 높은 랭크는 무조건 셋 패
            (무승부 불가)
             
            트립스인경우, 
            1. 내림차순 정렬
            2. 숫자가 높은 카드가 있는 쪽이 승
            3. 두 트립스의 숫자가 모두 같을 경우, 남은 두 장의 키커를 비교해 숫자가 높은쪽이 승
            (무승부 가능)
             
            스트레이트끼리 붙는 경우
            1. 내림차순 정렬
            2. 숫자가 높은 카드가 있는 쪽이 승
             
            플러쉬끼리 붙는 경우
            1. 내림차순 정렬
            2. 숫자가 높은 카드가 있는 쪽이 승
             
            풀하우스끼리 붙는 경우
            1. 내림차순 정렬
            2. 숫자가 높은 카드가 있는 쪽이 승
             
            포오브어카인드끼리 붙는 경우
            1. 내림차순 정렬
            2. 숫자가 높은 카드가 있는 쪽이 승
            보드에 네개가 깔린 경우 스타팅 핸드의 키커로 승부
             
            스트레이트플러쉬끼리 붙는 경우
            1. 내림차순 정렬
            2. 숫자가 높은 카드가 있는 쪽이 승
### 7. End
    팟 분배

# (now)
## 종료조건
### 1.라운드 종료조건 
    A. 프리플롭 종료조건 (플롭으로 넘어가기 위한 조건)
        1. 마지막으로 일어난 bet, raise 에 모든 라이브 플레이어가 call, fold 로 응답. 
            최소 1명 이상의 라이브 플레이어는 call을 해야함.
        2. all-in 발생 시
          ㄱ. 해당 올인이 언더콜일 경우(short 올인)
          ㄴ. 해당 올인이 직전 베팅의 콜 금액 이상, LPFB 이하일 경우 (short 올인)
          ㄷ. 해당 올인이 직전 베팅의 콜 금액 + LPFB 이상일 경우
 
            ㄱ : 올인을 한 유저를 제외하고 남은 두 명 이상의 라이브 플레이어들의 각 stack에 
                해당 올인 직전 valid total bet을 full call하고, 
                해당 라운드의 LPB 이상 raise 할만큼의 금액이 남아 있으면서, 
                해당 올인 직전 valid total bet에 모두 call 로 응답한 경우 
            ㄴ, ㄷ : 올인을 한 유저를 제외하고 남은 두 명 이상의 라이브 플레이어들의 각 stack에 
                해당 올인 금액을 full call 하고, 
                해당 라운드의 LPFB 이상 raise 할만큼의 금액이 남아 있으면서, 
                해당 올인 금액에 모두 call로 응답한 경우
 
    B. 플롭, 턴 종료조건 (플롭일 경우 턴으로 넘어가고, 턴일 경우 리버로 넘어가기 위한 조건)
        1. 모든 라이브 플레이어가  check
        2. 마지막으로 일어난 bet, raise 에 모든 라이브 플레이어가 call, fold 로 응답. 
            최소 1명 이상의 라이브 플레이어는 call을 해야함.
        3. all-in 발생 시
          ㄱ. 해당 올인이 언더콜일 경우(short 올인)
          ㄴ. 해당 올인이 직전 베팅의 콜 금액 이상, LPFB 이하일 경우 (short 올인)
          ㄷ. 해당 올인이 직전 베팅의 콜 금액 + LPFB 이상일 경우
 
            ㄱ : 올인을 한 유저를 제외하고 남은 두 명 이상의 라이브 플레이어들의 각 stack에 
                해당 올인 직전 valid total bet을 full call하고, 
                해당 라운드의 LPB 이상 raise 할만큼의 금액이 남아 있으면서, 
                해당 올인 직전 valid total bet에 모두 call 로 응답한 경우 
            ㄴ, ㄷ : 올인을 한 유저를 제외하고 남은 두 명 이상의 라이브 플레이어들의 각 stack에 
                해당 올인 금액을 full call 하고, 
                해당 라운드의 LPFB 이상 raise 할만큼의 금액이 남아 있으면서, 
                해당 올인 금액에 모두 call로 응답한 경우
 
    C. 리버 종료 조건 (쇼다운으로 넘어가기 위한 조건)
        1. 모든 라이브 플레이어가  check
        2. 마지막으로 일어난 bet, raise 에 모든 라이브 플레이어가 call, fold 로 응답. 
            최소 1명 이상의 라이브 플레이어는 call을 해야함.
        3. all-in 발생 시
          ㄱ. 해당 올인이 언더콜일 경우(short 올인)
          ㄴ. 해당 올인이 직전 베팅의 콜 금액 이상, LPFB 이하일 경우 (short 올인)
          ㄷ. 해당 올인이 직전 베팅의 콜 금액 + LPFB 이상일 경우
 
        마지막 올인에 대해 모든 유저가 올인 또는 콜 또는 폴드로 대답한 경우
 
### 2.핸드 종료조건
        1. 한 명의 라이브 플레이어만 남기고 모두 fold 
        (헤즈업 상황에서 한 명이 fold 하는 상황 포함됨) 
            : 프리플롭 종료조건 1번 / 플롭, 턴 종료조건 2번 / 리버 종료조건 2번 구현시 
            해당 조건문의 조건문으로 구현
     
        2. all-in 발생 시 
            : 프리플롭 종료조건 2번 / 플롭, 턴 종료조건 3번 / 리버 종료조건 3번 구현시 
            해당 조건문의 조건문으로 구현
            
        ㄱ. 해당 올인이 언더콜일 경우(short 올인)
        ㄴ. 해당 올인이 직전 베팅의 콜 금액 이상, LPFB 이하일 경우 (short 올인)
        ㄷ. 해당 올인이 직전 베팅의 콜 금액 + LPFB 이상일 경우
 
          ㄱ, ㄴ, ㄷ : 올인을 한 유저를 제외하고 
          남은 모든 라이브 플레이어들의 각 stack에 있는 금액이 
            해당 올인 직전 valid total bet 액수 이하이면서  
            해당 올인에 모두 call 또는 fold로 응답한 경우, 이때 
                1) 모두 fold로 응답하면, 모든 플레이어의 스타팅 카드 즉시 테이블링, 
                    쇼다운 후 올인 유저 승리 판정.
                2) 한 명 이상 call로 응답하면, 모든 플레이어의 스타팅 카드 즉시 테이블링, 
                    쇼다운 후 유저 승리 판정.

### 3.쇼다운
    올인이 일어난 후 쇼다운 (핸드종료조건 2번 참고)
    올인이 일어나지 않은 쇼다운

# (now)  
매 라운드마다, 각 라이브 플레이어들의 액션이 끝날 때마다  
해당 라운드 종료조건을 확인하고 다음 라이브 플레이어의 액션 조건을 계산  
먼저 아래 액션 조건을 구현하고 TDA 규칙으로 업그레이드  
  
-----------------------------------------------------------
#### 베팅 구현 방법 
    1-1. 구현 난이도 하, 게임 난이도 하 : 
        마우스로 액션버튼 클릭. 최소 베팅금액 슬라이드 바, 레이즈 불가시 자동 올인 기능
    1-2. 구현 난이도 중, 게임 난이도 상 : 
        마우스로 액션버튼 클릭. 마우스로 칩 직접 선택. 
    1-3. 구현 난이도 상, 게임 난이도 상 : 
        마우스로 액션 버튼 클릭 또는 음성으로 액션. 마우스로 칩 직접 선택 또는 음성으로 베팅금액 선언.

    프로토 타입은 1-1 로 구현
-----------------------------------------------------------

**액션 조건 = 액션 버튼 활성화 여부 판단 규칙** 
  
#### bet : 플롭, 턴, 리버에서만 구현 
    if (조건1) and (조건2)
       (조건1) 자기 차례일 때, (테이블 상 유저 기준 이하 자기 오른쪽편에) 
               bet, raise, all-in 이 없었고 (액션조건 check과 같음) 
       (조건2) 스택에 BB 이상 남아 있으면 bet 버튼 활성화 
 
### check :  플롭, 턴, 리버에서만 구현
    if (조건1)
       (조건1) 자기 차례일 때, 
              자기 오른쪽편에 bet, raise, all-in 이 없었을 경우에만 가능 (액션 조건 bet과 같음)
 
### 50% 룰 : 직전 레이즈의 최소레이즈 50% 미만 이면 콜, 50%이상이면 리레이즈 판정
#### 게임에선 50% 룰을 직접 구현하지 않는다. 
 
### raise : raise는 무조건 자기 오른쪽 편에 bet, raise, all-in 이 있었어야만 할 수 있다. 
    (액션 조건 콜과 같음)
    
    프리플롭에서는 자기 오른쪽 편에 bet이 없었어도 raise 할 수 있다. (예외 조건)
        레이즈/리레이즈의 최소레이즈는 
        다른 플레이어의 직전 풀벳 또는 직전 풀레이즈의 최소레이즈와 같거나 그보다 커야 한다.
        
    이전의 올인이나 multiple short all-in 들의 누적합이 
    the largest prior full bet이나 raise에 도달하면
        이미 행동을 했고 아직 다른 플레이어에 의한 full bet 이나 full raise에 
        직면하지 않은 플레이어들에게 betting을 re-open 해준다
        그때 minimim raise는 the largest prior full bet이나 raise 액수와 같다.
     
    프리플롭에서 if 조건1 and 조건2   또는  if 조건5 and 조건6 또는 if 조건7 and 조건8
        (조건1) 자기 차례일 때, 자기 오른쪽 편에 full raise가 없었고
        (조건2) 스택에 BB의 2배 이상 남아 있으면 raise 버튼 활성화, 
                스크롤은 최소레이즈가 BB 2배 이상부터 되도록 
        (조건5) 자기 차례일 때, 자기 오른쪽 편에 full raise가 있었고
        (조건6) 스택에 직전 total bet + LPFB  이상의 금액이 남아 있으면 raise 버튼 활성화 
                : (re-raise)
        (조건7) short all-in의 increment 누적합이 LPFB 이상이 되었고
        (조건8) 스택에 직전 total bet + LPFB 이상의 금액이 남아 있으면 raise 버튼 활성화 
                : (re-open)
                이 경우 short all-in 카운터 초기화 
    
    플롭, 턴, 리버에서 if 조건3 and 조건4 또는 if 조건5 and 조건6 또는 if 조건7 and 조건8
        (조건3) 자기 차례일 때, 자기 오른쪽편에 open bet이 있었고, 이 open bet이 full bet이었고, 
        (조건4) 스택에 직전 full bet의 2배 이상의 금액이 남아 있으면 raise 버튼 활성화
        (조건5) 자기 차례일 때, 자기 오른쪽 편에 full raise가 있었고
        (조건6) 스택에 직전 total bet + LPFB  이상의 금액이 남아 있으면 raise 버튼 활성화 
                : (re-raise)
        (조건7) short all-in의 increment 누적합이 LPFB 이상이 되었고
        (조건8) 스택에 직전 total bet + LPFB 이상의 금액이 남아 있으면 raise 버튼 활성화 
                : (re-open)
                이 경우 short all-in 카운터 초기화
    
    
    따라서 컴퓨터가 기억해야 하는 것들은
    1. 라이브 플레이어들의 액션이
      1) full-bet 이었는지 (bet 버튼이 활성화돼서 눌렀다는건 그 bet이 full-bet이라는걸 의미)
      2) full-raise 였는지 (raise 버튼이 활성화돼서 눌렀다는 건 그 raise가 full-raise라는걸 의미)
      3) all- in 이었는지 (all-in 버튼은 스택이 1 이상이면 무조건 활성화되므로, 
         all-in 버튼을 눌렀다면 
            그 all-in이 full-bet인지, full-raise인지, call인지 short인지 판단 필요, 
            short였다면 
            몇번째 short였는지, 해당 short에서 increment 된 금액 기억 필요)
      4) 직전 total-bet, 전전 total-bet, LPFB
      5) call 인지
      6) fold인지
      7) check인지
 
### call : 콜은 자기 오른쪽 편에서 bet, raise, all-in이 있었어야만 할 수 있다 
    (액션조건 레이즈와 같음) 
    
    If (조건1 and 조건2) or (조건3 and 조건4) or (조건5 and 조건6)
        (조건1) 자기 차례일 때, 자기 오른쪽 편에서 full-bet 이 있었을 경우
        (조건2) 스택에 full-bet 이상 있으면 call 버튼 활성화
        (조건3) 자기 차례일 때, 자기 오른쪽 편에서 full-raise 가 있었을 경우
        (조건4) 스택에 total bet 이상 있으면 call 버튼 활성화
        (조건5) 자기 차례일 때, 자기 오른쪽 편에서 all-in 이 있었을 경우
        (조건6) 스택에 all-in 금액 이상 있으면 call 버튼 활성화
 
### fold : 
    (조건1) 자기 차례일 때, 이전에 올인을 한적이 없으면 fold 버튼 활성화
 
### all-in : 
    (조건1) 유저 스택이 0이 아니고 이전에 all-in 버튼을 누른 적이 없었으면  All-in 버튼 활성화 
    
    (클라이언트 쪽에선 all-in 버튼을 누르면 이후 모든 액션버튼 비활성화처리)
    (서버쪽에선 all-in 액션을한 유저는 해당 루프에서 out 처리)
    short 올인일 경우 short 올인 카운터 시작 (short 올인 횟수, increment 누적합)
    
    클라이언트로부터 올인 액션을 전달받았을때,
    
    모든 라운드에서
    이전에 full bet이 없었고
    유저의 올인 금액이  BB 미만인 경우 
    short 처리(이하 현재 라운드 루프에서 아웃, 팟 사이즈 업데이트, increment 금액 누적합 업데이트), 
    이 경우 LPFB는 0
    현재 total bet은 그대로 BB
    
    프리플롭에서
    이전에 full bet이 없었고
    유저의 올인 금액이  BB + BB미만 인 경우
    short 처리
    이 경우 LPFB는 그대로 BB
    현재 total bet은 현재 올인 금액으로 업데이트
    
    플롭, 턴, 리버에서
    이전에 full bet이 없었고
    유저의 올인 금액이  BB + BB미만 인 경우 (즉 지금 올인이 오픈 벳)
    short 처리
    full-bet 처리, 
    이 경우 LPFB는 현재 올인 금액 
    현재 total bet은 현재 올인 금액으로 업데이트
    프리플롭에서
    이전에 full bet이 없었고
    유저의 올인 금액이  BB + BB이상 인 경우
    full-raise 처리, 
    이 경우 LPFB는 현재 올인 금액 - 직전 total bet(BB)  
    total bet을 현재 올인 금액으로 업데이트
    
    플롭, 턴, 리버에서
    이전에 full bet이 없었고
    유저의 올인 금액이  BB + BB이상 인 경우 (즉 지금 올인이 오픈 벳)
    full-bet 처리, 
    이 경우 LPFB는 현재 올인 금액 - 직전 total bet(BB)  
    total bet을 현재 올인 금액으로 업데이트
    
    모든 라운드에서
    이전에 full bet이 있었고(프리플롭의 경우 이전의 full bet은 BB)
    유저의 올인 금액이 직전 total bet 미만인 경우
    short 처리, 
    이경우 LPFB 그대로, (프리플롭의 경우 0)
    total bet도 그대로 (프리플롭의 경우 BB)
    
    모든 라운드에서
    이전에 full bet이 있었고(프리플롭의 경우 이전의 full bet은 BB)
    유저의 올인 금액이 직전 total bet 이상, 직전 total bet + LPFB 미만인 경우
    short 처리, 
    이 경우 LPFB 그대로, (프리플롭의 경우 BB 그대로)
    total bet은 현재 올인 금액으로 업데이트
    
    모든 라운드에서
    이전에 full bet이 있었고 (프리플롭의 경우 이전의 full bet은 BB)
    유저의 올인 금액이 직전 total bet + LPFB 이상인 경우
    full-raise 처리, 이 경우 LPFB는 현재 올인 금액 - 직전 total bet
    total bet은 현재 올인 금액으로 업데이트
    
    ---
    
    모든 라운드에서
    이전에 full raise가 있었고
    유저의 올인 금액이  직전 total bet 미만인 경우
    short 처리, 
    이경우 LPFB는 그대로, 
    현재 total bet도 그대로
    
    모든 라운드에서
    이전에 full raise가 있었고
    유저의 올인 금액이 직전 total bet 이상, 직전 total bet + LPFB 미만인 경우
    short 처리, 
    이 경우 LPFB는 그대로
    total bet은 현재 올인 금액으로 업데이트
    
    모든 라운드에서
    이전에 full raise가 있었고
    유저의 올인 금액이 직전 total bet + LPFB 이상인 경우
    full raise 처리,
    이 경우 LPFB는 현재 올인 금액 - 직전 total bet
    total bet은 현재 올인 금액으로 업데이트
     
    플롭, 턴, 리버에서
    이전에 full raise가 없었고
    유저의 올인 금액이 직전 total bet 미만인 경우
    short 처리
    
    플롭, 턴, 리버에서
    이전에 full raise가 없었고
    유저의 올인 금액이 직전 total bet 이상 LPFB미만인 경우
    short 처리, 
    이 경우 LPFB 그대로, 
    total bet은 현재 올인 금액으로 업데이트
    
    플롭, 턴, 리버에서
    이전에 full raise가 없었고
    유저의 올인 금액이 직전 total bet + LPFB 이상인 경우
    full raise 처리, 이 경우 LPFB는 현재 올인 금액 - 직전 total bet
    total bet은 현재 올인금액으로 업데이트

 

--------------------------
# (now) 
## 딜러 클래스의 역할
    모든 라운드에서, 모든 플레이어의 매턴마다, 어떤 액션버튼이 활성화되어야 하는지 결정, 
    현재 라이브 플레이어를 액션큐에서 뺄지, 남길지 결정 (일단 액션을 하면 뺀다?)
    액션큐를 현재 플레이어 기준으로 새로 만들지 결정 (bet, raise, all-in 시)
    메인 팟, 사이드 팟을 만들고 각 팟에 지분이 있는 플레이어를 관리


### 액션 큐(라이브 플레이어를 요소로 가지는 덱) 
    활성화된 플레이어 숫자를 매 플레이어 차례마다 확인한다. 
    플레이어들은 공격형 액션을 하면 공격플래그를 만들고, 수비형 액션을 하면 수비플래그를 만든다.
    플레이어들은 액션을 하면 플래그를 액션큐로 보낸다. 
    9명이라면 처음 공격플래그가 액션큐에 들어온 이후로 수비플래그가 8개 들어오면 루프 종료. 
        다음 라운드로 이동
    처음 큐에 공격 플래그가 들어오다가 이후에 공격플래그가 들어오면 그 앞에 있는 요소들 전부 leftpop
    활성화된 플레이어 숫자-1 만큼 수비플래그가 들어올때까지 반복
    활성화된 플레이어 숫자가 한명이면 루프 종료+핸드종료
    리버 라운드에서 액션큐가 정상종료되면 쇼다운으로 넘어감
 
    액션큐를 활용해서 매 턴에 플레이어들이 어떤 액션을 할 수 있는지(어떤 액션버튼이 활성화되어야 하는지) 
    클라이언트 모델이 알 수 있을 듯.
        자기 차례에 액션큐에 공격플래그가 없었으면 bet, check, all-in, fold 가능
        자기 차례에 액션큐에 공격플래그가 있었으면 call, raise, all-in, fold 가능
 
    각 플레이어 클래스는 라운드마다 자기 액션 리스트를 갖는다.
    자기가 올인을 했으면, 다음 라운드부터는 fold가 불가능하게
 
    딜러 클래스는 올인 플레이어가 나오면 
    그 플레이어를 해당 라운드 루프에서 아웃시키고 다음 루프에 참여시킨다. 
        이때 스택이 남아 있는 경우는 루프에 남겨두고 사이드팟 처리한다. 
    딜러 클래스는 각 포지션에 누가 오든 상관이 없다. 
    딜러 클래스의 연산에서 연산되는 연산항은 포지션명만 쓰인다.
 

# (now)
### 팟 생성 로직 
    1. 폴드할 때 팟에 합산
    2. 라운드별로 필요시 사이드팟을 만들어줘야 한다.
    3. 라운드가 종료되면 다음 라운드로 승계
    
    구현시,
    폴드한 유저가 있는 경우, 해당 유저의 베팅금액은 팟에 귀속
    라운드가 종료되면, 각 유저들의 스택에서 차감된 총액을 합사하여 팟에 귀속
    
    ㄱ. 올인 유저 발생시, 해당 라운드를 마지막으로 핸드가 종료되었을 때, 
        올인에 대한 레이즈가 없었으면 해당 라운드 까지의 메인 팟만 계산, 
        올인에 대한 레이즈 또는 올인 발생으로 최초 올인보다 높은 베팅금액 발생시 사이드팟 생성.
    ㄴ. 올인 유저 발생시, 다음 라운드로 넘어가면 
        해당 라운드의 메인팟과 별도로 사이드팟 1을 새로 생성해 
        다음 라운드부터 발생하는 벳, 레이즈, 올인에 의해 스택에서 차감된 총액의 합계를 사이드 팟에 귀속. 
    프리플롭, 플롭, 턴에서 ㄱ, ㄴ 반복
    
    올인이 여러명이면
        딜러는 가장 적은 올인 금액을 기준으로 메인 팟을 만든다. 
        나머지 올인(레이즈)에서 메인팟 올인 금액을 뺀 액수 x 올인 인원으로 사이드 팟 생성. 
        이런 식으로 올인 인원이 2명이 될 때까지 반복.
    
    1. 모두 올인한 경우
     가장 적은 올인 금액을 기준으로 메인팟을 먼저 만든다
    
    2. 올인한 사람도 있고 안한 사람도 있는 경우
 

# (now)
    자신이 베팅, 레이즈를 하면 스택에서 그만큼을 차감한다. 

# (now)  
새로운 게임방에 참여한 사람들은 모든 포지션에서 플레이 가능(랜덤 배정) 

    (later)
    기존 게임방에 참여해 대기하는 사람은 SB, Button 포지션을 제외하고 랜덤 배정 

# (now)
    팟 만드는 로직으로 라운드 종료되는 조건을 검증한다.
    라운드가 종료되려면 폴드를 제외하고 남은 플레이어들의 최종 베팅금액이 모두 일치해야 한다.
    (진행선에서 해당 라운드의 최종 활성화 플레이어 수로 해당 라운드의 최종 팟을 나누면 
    각 플레이어의 최종 베팅금액이 나와야 하고,
    이 금액이 실제로 각 플레이어들의 해당 라운드 최종 베팅 금액과 일치하는 지 검증)
        이 검증 로직이 옳지 않은 경우가 있을 수 있다. short 올인이 일어났던 경우.

 
 
 
 
 
# TDA 규정

-----------------------------------------------------------------------------
### 베팅룰

# (now)
    rule 40: Methods of Betting: Verbal and Chips
    A: Bets are by verbal declaration and/or pushing out chips. 
    If a player does both, whichever is first defines the bet. 
    If simultaneous, a clear and reasonable verbal declaration takes precedence, otherwise the chips play. 
    In unclear situations or where verbal and chips are contradictory, 
    the TD(Tournament Directors) will determine the bet based on the circumstances and Rule 1. 
    See Illustration Addendum. See also Rule 57.


    betting은 플레이어가 액션 버튼을 누르는 것으로 실행한다 
    (2022 TDA rule 40에서 verbal declaration과 상응. 
    오프라인과 똑같으려면 모든 경우 betting 버튼이 활성화 되어야 할 것이다. 
    게임을 쉽게 만들기 위해 현재 betting이 가능한 상황에서만  betting버튼을 활성화시키는게 목표다)
 
    rule 41: Methods of Calling
    calling도 마찬가지. 
     
    rule 42: Methods of Raising
    raising도 마찬가지 

# (now)
    rule 43: Raise Amounts 
    A: A raise must be at least equal to the largest prior full bet or raise of the current betting round. 
     
    raise가 가능한 조건 하에 raise를 하려고 할 때, 
    (최소)raise 금액은
        현재 라운드에서 
        앞서 있었던 가장 큰  full bet 금액 이상 또는 
        앞서 있었던 가장 큰 full raise 금액 이상 이다.
            여기서 'full bet' 또는 'full raise' 의 full 의 의미는 
                유효한 (valid, legal) 베팅 또는 레이즈를 의미한다.
            여기서 '가장 큰 full bet 금액 또는 가장 큰 raise 금액' (이하 LPFB)은 
                total bet이 아닌 last legal increment을 가리킨다. 
                (last legal increment  = 직전 total bet - 전전 total bet)
    
    full bet 조건 : 해당 라운드에서 최초 베팅시 BB 이상 금액 베팅
    
    full raise 조건 : 최초 레이즈 시 직전에 이뤄진 full bet(BB)에 대해 콜을 하고, 
        BB 이상의 액수를 레이즈

        이후 레이즈는, 직전 total bet을 콜하고, 
            직전 total bet-전전 total bet 이상의 액수를 레이즈  
    
    따라서 the largest prior full bet or raise = minimum raise = last legal increment
    
    full call :
    예시
    SB 500 (스택 -500)
    BB 1000 (스택 -1000)
    UTG 250 올인 (스택 -250) (이 경우 UTG의 올인은 short 올인이자 언더콜임)
    SB 1000 콜 (스택 -500) (이 경우 SB의 콜은 BB에 대한 콜임, UTG의 올인/언더콜은 자동으로 콜한게 됨)
    
# (now)
    플레이어의 스택 >= the largest prior full bet(raise) 이면 
    call/raise/all-in 버튼을 활성화 시킨다.
    이때 raise 스크롤의 min value 는 the largest prior full bet(raise) 이다.
     
    A player who raises 50% or more of the largest prior bet but 
    less than a minimum raise must make a full minimum raise. 
     
    50% 룰과 최소 레이즈 (minimum raise) : 
        현재 raise 액수(현재 레이즈 액수(total bet) - 직전 total bet)가
        현재 라운드에서 앞서 있었던 가장 큰 full bet의 50% 이상 ~ full bet 미만 또는 
        앞서 있었던 가장 큰 full raise의 50% 이상, full raise 미만을 낸 경우, 
        minimum raise를 해야 한다.
            여기서 minimum raise란
            현재 라운드에서 앞서 있었던 가장 큰 full bet 액수만큼 또는 
            앞서 있었던 full raise 금액 내지 그 액수 만큼의 raise 행위를 말한다.
     
# (now)
    the largest prior full bet(raise) 의 50%  <= 플레이어의 스택 < the largest prior full bet(raise) 이면
        minimum raise를 할 수 없으므로 
        all-in/fold 버튼만 활성화시킨다. 
            (이 경우 all-in 시 not full raise 플래그를 붙여야 한다. 
            즉 콜로 간주한다. 필요할까? 고민 필요)
     
    If less than 50% it is a call unless “raise” is first declared or the player is all-in (Rule 45-B).
    Declaring an amount or pushing out the same amount of chips is treated the same (Rule 40-C). 
     
    50% 미만이면 모두 콜로 판정한다. (예외 : 던질 때 먼저 레이즈라고 말했거나, 올인한 경우)
# (now)
    플레이어의 스택 < the largest prior full bet(raise) 의 50% 이면, 
    바로 위의 경우에 포함되므로
        call/raise 버튼은 비활성화, all-in/fold 버튼만 활성화 시켜야 한다 
        (이 경우 all-in 시 not full raise 플래그를 붙여야 한다. 
        즉 콜로 간주한다. 필요할까? 고민 필요)
     
    B: Without other clarifying information, declaring raise and an amount is the total bet.
    Ex: A opens for 2000, B declares “Raise, eight thousand.” The total bet is 8000.
    
# (now)
    특별히 따로 언급하지 않는다면, 레이즈를 선언할 때 언급하는 금액은 total bet을 의미한다 
     
# (now)   
    raise를 누르면
        콜해야하는 액수가 뜨고, 스택에서 이 액수가 차감된 상태에서
        스크롤 min value인 the largest prior full bet(raise) 부터 
        max value 스택 총액까지 선택할 수 있다.
        이때 max value까지 올리면 자동으로 all-in 처리 된다.

--------------------------------------
# Illustration Addendum
### example 1.
    1.100/200 게임 플랍에서
    SB 600 open bet
    BB 1600 레이즈
    UTG 3600 레이즈
    HJ 는 최소 레이즈 2000 이상. 즉 3600 콜하고 최소레이즈 minimum raise 2000 이상
    다시 말해 최소 5600 이상을 레이즈 해야 한다.
 
### example 2.
    프리플랍에서
    SB 50
    BB 100
    UTG 150 올인
    HJ 가 레이즈 하려면 150 받고 최소레이즈 100 해서 250을 내야한다.
    UTG 는 50% 룰에 따라 미니멈 레이즈를 해야하는 대상이지만 올인을 했고 이 올인은 유효한 full bet(raise)가 아니므로
    HJ의 minimum raise는 직전 유효한 full bet 이었던 BB를 기준으로 100이 된다.
    따라서 HJ가 레이즈를 하려면 직전 올인 150을 받고 최소레이즈 100을 더해서 250을 레이즈 해야한다. (TDA 규정 설명)
    HJ는 BB 2배 200에 우수리 50 더해서 250 (책 설명)
 
 
### example 3.
    100/200 게임
    턴에서
    SB 300 (최소 벳 200 이상이니까 300 벳 괜찮음)
    BB 1000 레이즈
    UTG 가 레이즈 하려면 최소 total 1700. 최소레이즈 miinimum raise는 700
 
### example 4-a.
    25/50 게임에서
    SB 25
    BB 50 (blind bet)
    UTG 125 레이즈. (프리플랍이라면 최초 레이즈시 BB의 2배 이상만 내면 되니까 기준 충족. 
    BB의 베팅을 기준으로 보면 BB의 50베팅에서 75를 레이즈 시킨것. 그러면 최소레이즈는 75가 됨.
    HJ 200. 레이즈 HJ는 최소레이즈 75만큼 레이즈 한 것. 
    CO 500 레이즈
    Button이 여기서 레이즈 하려면 800 이상 내야한다. 즉 최소 레이즈 300.
 
### example 4-b.
    25/50 게임에서 
    SB 25
    BB 50 (blind bet)
    UTG 500 레이즈
    HJ 500 콜
    CO 500 콜 따라서 현재 시점에서 최소레이즈는 450
    Button 이 레이즈 하려면 500 받고 450 더해서 950 레이즈 해야한다.
 
 
 
    Rule 45: Multiple Chip Betting.
    A: If facing a bet, unless raise or all-in is declared first, 
    a multiple-chip bet (including a bet of your last chips) is a call 
    if every chip is needed to make the call; 
    i.e. removal of just one of the smallest chips leaves less than the call amount
    B: If every chip is not needed to make the call; 
    i.e. removal of just one of the smallest chips leaves the call amount or more
    1) if the player has chips remaining, the bet is governed by the 50% standard in Rule 43
    2) if the player’s last chips are bet he or she is all-in whether reaching the 50% threshold or not.”
     
    Rule 45 :  Multiple chips betting 
        베팅 상황에서
        레이즈나 올인을 선언하지 않고
        칩을 여러개 던졌을 때
        A : 던진 칩들 중 가장 작은 금액의 칩 하나를 뺐을 때 콜금액보다 모자르면
        콜 판정
     
        B : 던진 칩들 중 가장 작은 금액의 칩 하나를 빼도 콜 금액 이상이라면
        스택이 충분할시
        50%룰 적용해 레이즈인지 콜인지 판정
         
        C: 던진 칩들 중 가장 작은 금액의 칩 하나를 빼도 콜 금액 이상이라면
        스택을 전부 걸었을 시
        50%룰 상관없이 올인
 
     
    Rule 45 : Multiple Chip Betting
     
    예시
    1.
    A 오픈 400
    B 레이즈 1100 (700 raised)
    C 1500을 내면 콜. 
    1000칩 하나, 500칩 하나를 내면 콜이다. 
    500을 제거했을 때 필요한 콜금액인 1100에 미달하므로 (TDA 설명)
    (필요한 콜금액인 1100에 맞게 칩을 냈다면 (1000칩 하나, 100칩 5개) 
    1500-1100 = 400 은 이전 레이즈 700의 50%인 350보다 크므로 미니멈 레이즈를 해야한다)
 
# (now)
    1-1:
    C의 스택이 1800이상이면 C의 레이즈 버튼 활성화. 1800 미만이면 C의 올인 버튼 활성화
    두 경우 모두 콜/폴드 버튼 활성화
    이게 가능하려면 B의 total bet이 1100이라는 것과, raise to total이 700 이라는 사실을 알고, 이 둘의 합계를 C의 스택과 비교해야 한다.
   
    2. 
    플롭, 
    A 오픈 1050
    B 2000을 내면 콜.
    1000칩 2개를 냈을 때, 이게 B의 스택전부라고 해도, 올인 또는 레이즈를 선언하지 않으면 콜이다. 
    왜냐면 1000을 제거했을 때 필요한 콜금액 1050에 미달하므로
    (필요한 콜금액에 맞게 칩을 냈다면 (1000칩1 25칩 4개 100칩 9개)  
    2000-1050=950 은 이전 베팅 1050의 50%인 525보다 크므로 미니멈 레이즈를 해야한다)
 
# (now)
    1-1:
    B의 스택이 2100 이상이면 B의 레이즈 버튼 활성화. 2100 미만이면 올인 버튼 활성화
    두 경우 모두 콜/폴드 버튼 활성화
 
# Illustration Addendum
 
### example 1-a
    A 오픈 1200
    B 1000칩 두개 내밈
    이경우 B는 콜. 왜냐면 1000칩 하나를 제거했을 때 
    최소 콜금액 1200이 되지 않기 때문에 50% 룰 미적용
 
### example 1-b
    250/500 게임에서 프리플랍
    SB 250
    BB 500
    UTG 1100 레이즈
    UTG+1 500칩 하나 1000칩 하나 내밈
    이 경우 UTG+1 도 콜. 왜냐면 500칩 하나 제거 했을 때 
    최소 콜금액 1100이 되지 않기 때문에 50% 룰 미적용
 
### example 2
    250/500 게임에서 프리플랍
    SB 250
    BB 500
    UTG 1100 레이즈. 그러면 Minimum raise는 600
    UTG+1 1000칩 하나 100칩 5개 내밈
    UTG+1은 50% 룰 적용. 미니멈 레이즈 대상. 
    full raise를 만드려면 200을 더내서 total 1700을 만들어야 한다.
    UTG+1이 1000칩 하나 1000칩 4개를 냈어도 50% 룰을 만족하므로 레이즈 판정됨.
    그런데 1000칩과 500칩 하나를 낸 경우
    둘 중 하나를 제거해도 콜 요건인 1100을 맞추지 못하므로 50% 룰 미적용. 콜로 판정.
 
### example 3
    250/500 게임에서 프리플랍
    SB 250
    BB 500
    UTG 1100 레이즈. 그러면 Minimum raise는 600
    UTG+1 1000칩 하나 100칩 3개 내밈
    50% 룰 적용. 최소레이즈의 50%인 300에 미달한 200이므로 콜 판정. 200을 돌려준다
 
### example 4-a.
    프리플랍에서 
    SB 700
    BB 1400
    UTG 1000칩 1, 500칩 3개를 낸 경우, 50%룰 적용. 
    1100은 minimum raise 1400의 50%인 700을 넘기므로 
    UTG는 300을 더 내서 2800 레이즈를 맞춰야 한다.
 
# (now)
    현재 플레이어가 레이즈 가능한지 보려면
    직전 total bet + minimum raise 이상의 스택이 현재플레이어에게 있는지 확인해야한다.
    이상이면 레이즈버튼 활성화
 
### example 4-a.
    프리플랍에서 
    SB 700
    BB 1400
    UTG 1000칩 1, 500칩 2개를 낸 경우. 50%룰 적용. 2000-1400 = 600, 
    last legal increment 1400의 50%인 700에 미달하므로 콜판정.
 
 
 
# (now)
    Rule 47 : Re-Opening the Bet. 
     
    A: In no-limit and pot limit, 
    an all-in wager (or cumulative multiple short all-ins) totaling 
    less than a full bet or raise will not reopen betting for players 
    who have already acted and are not facing at least a full bet or raise when the action returns to them. 
     
    If multiple short all-ins re-open the betting, 
    the minimum raise is always the last full valid bet or raise of the round (See also Rule 43).
     
    B: In limit, at least 50% of a full bet or raise is required to re-open betting for players who have already acted. See Illustration Addendum.
 
    full bet 또는 full raise 보다 적은 금액의 올인이나
    multiple short all-in 들의 누적합은
    이미 행동을 했고 full bet 이나 full raise에 직면하지 않은 플레이어들에게 
    betting을 re-open 하지 않는다.
     
    바꿔 말해 이전의 올인이나
    multiple short all-in 들의 누적합이 the largest prior full bet이나 raise에 도달하면
    이미 행동을 했고 아직 다른 플레이어에 의한 full bet 이나 full raise에 직면하지 않은 
    플레이어들에게 betting을 re-open 해준다
    그때 minimim raise는 the largest prior full bet이나 raise 액수와 같다.
 
# Illustration Addendum
### Example 1.
    플롭
    A 100 오픈
    B 125 올인 (+25 increment, not full raise)
    C 125 콜
    D 200 올인 (+75 increment, not full raise) (+100 increment  > full raise) 
    E 200 콜  
 
    A는 full raise 100을 직면하게 되었고, 이경우 '이미 액션을 한' A에게도 레이즈 기회가 주어짐
    왜냐하면 A가 오픈한벳에서 다시 A 차례가 됐을 때 100이 레이즈 된 상황이 됐으므로
 
### Example 1-A:
    플롭
    A 100 오픈
    B 125 올인 (+25 increment, not full raise)
    C 125 콜
    D 200 올인 (+75 increment, not full raise)
    E 200 콜   
     
    A 200 콜. 
    B 는 올인이라 패스
    이미 액션을 한번 한 C 에게는 betting 기회가 re-open 되지 않는다.
    왜냐하면 현재 라운드에서 full valid bet은 A의 open betting 밖에 없었고
    C의 액션 이후로 full valid bet으로 간주될 수 있기 위한 short all 누적합은 
    75밖에 되지 않기 때문이다  
    따라서 200을 콜하거나 폴드할 수 밖에 없다.
    C는 자신의 125콜 이후에 A가 최소 225 이상의 베팅을 했었어야 full raise 100 상황에 직면하게 된다.
    따라서 C는 자신의 기존 콜 125에 더해 75를 더 내서 콜을하거나 폴드를 할 수밖에 없다. 
 
### Example 1-B
    플롭
    A 100 오픈
    B 125 올인 (+25 increment, not full raise)
    C 125 콜
    D 200 올인 (+75 increment, not full raise)
    E 200 콜
     
    A 300 레이즈 (200받고 100 미니멈 레이즈)
    B는 올인이라 팩스
    여기서 C가 콜하려면 175만 더 내면 되고, 그랬을 때 A에 대해레이즈도 할 수 있다.
 
 
### Example 2.
    50/100, 플롭 게임
    A 오픈 300
    B 올인 500 (+200 increment) short
    C 올인 650 (+150 increment) short 
    D 올인 800 (+150 increment) 여기서 D에게 레이즈 기회가 주어지지만 칩이 부족하므로 
    E 800 콜  여기서도 E에게 레이즈 기회가 주어지지만 콜 선택 
    F 가 레이즈를 하려고 할 때 minimum raise는? 300
    F 는 800을 콜하거나 1100으로 레이즈할 수 있다
 
### Example 3-a.
    프리플롭
    SB 2000
    BB 4000
    UTG 콜 4000
    CO 폴드
    BTN 7500 올인
     
    SB 폴드
    BB는 3500을 더내서 BTN에 대해 콜하거나, 거기에 추가로 4000을 더 내서 옵션을 할 수 있다. 
    BB가 콜 7500 했을 때
    UTG는 3500을 더 내서 BB에 대해 콜하거나 폴드할 수밖에 없다.
 
### Example 3-b.
    프리플롭
    SB 2000
    BB 4000
    UTG 콜 4000
    CO 폴드
    BTN 7500 올인
     
    SB 폴드
    BB가 레이즈 11500
    UTG 이제 레이즈 가능. 이미 냈던 4000에 7500을 더해서 콜을하고 최소 4000 이상부터 레이즈 가능
 
--------------------------------------------------------------------------------
# (now)
betting re-open을 구현하려면  

    모든 플레이어의 매순간 액션과 베팅사이즈를 기록해두었다가 short all in이 일어 났을 때
    누적 합이 the largest prior bet/raise 이상이 되면, 
    이미 액션을 한 플레이어에 한해서 full raise를 직면하는 경우 배팅 버튼을 다시 활성화시켜준다.

# (now)
옵션은 프리플롭에서만. BB에게만.   

    UTG부터 액션시작할 때 맨 처음 한바퀴 돌고 
    다시 BB차례가 되기 전까지 공격형 액션이 하나도 없었던 경우에만. 
    BB에게 자기자신의 오픈에 대해 레이즈 할 수 있는 기회 제공. 
    여기서 minimum raise는 open bet

    (later)  
    51: Binding Declarations / Undercalls in Turn 
     
    어떤 라운드에서건 opening bet이나 헤즈업 상황에서 나온 undercall은 full call이 되어야 한다.
    opening bet : 해당 스트릿에서 처음으로 나온 벳 (프리플랍에선 BB)
 
# (now)
    따라서 모든 라운드에서 open bet이 나왔다면 
    그 다음 최초 레이즈의 minimum raise는 
        (i.e. 최초 레이즈가 full raise가 되기 위해선) 
    (rule 43에 따라) open bet이 full bet이었을 때,
    무조건 open bet과 같아야 한다. 
    바꿔 말해 valid open bet 이후의 최초 레이즈는 open bet의 2배여야 한다.
 
# (now)
    RP-1. All-In Buttons 구현
    구현시, 올인을 한 플레이어는 올인버튼을 띄워놓는다.   
        올인 버튼은 언더콜 빈도를 감소시킨다.

    현재 스트릿에서 일어난 언더콜, 틀린 bet, underbet underraise 는 
    현재 스트릿이 끝나기 전 언제든 올바르게 고칠 수 있다
 


--------------------------------------------------------------------------------
    (later)  
    Rule 10: Breaking Tables, 2-Step Random Process. 
    A 2-step random or “double-blind” process assures that there is no favoritism in distributing new seat assignments. An example of one such process: 1) show players at the breaking table the new seat cards then scramble the cards face down and form a stack; 2) the dealer then deals one playing card face up to each player. The seat cards are then dealt out with the first seat card going to the player with the highest playing card by suit showing.
 
    구현시,
    테이블 밸런싱 알고리즘 위 내용 참고해서 고민해볼것
 
 
---------------------------------------------------------------------------
### showdown
    (later)
    rule 13: Tabling Cards and Killing Winning Hand 
        구현시,
        테이블링은 모든 카드를 화면에 띄워 보여주고
        음성으로 돌아가며 순서대로 읽어줍니다. 
 
     
    rule 15: Showdown and Discarding Irregularities (rule 18 참고)
    어떤 플레이어가 winning hand를 만드는 스타팅 카드 한장을 자발적으로 테이블링하면
    딜러는 그 플레이어의 모든 카드를 테이블링 하도록 권고해야한다. 거절하면 플로어를 호출해야 한다.
 

    모든 종류의 쇼다운에서 플레이어가 자신의 스타팅 카드를 오픈해야하는 경우엔 두장 모두 오픈해야한다.
    플레이어는 올인이 아닌 쇼다운시 자발적으로 자신의 오픈할 수 있고, 
    이 경우 스타팅 카드 두장이 자동으로 오픈된다.
 
# (now) 
    rule 16: Face Up for All-Ins 
        올인 플레이어가 발생하면, 
        그 핸드에서 다른 모든 플레이어의 베팅 액션이 끝난 후
        (i.e. 스택이 충분한 유저가 2명 미만이 되어 더이상 베팅액션 기회를 계산하는 게 의미없을경우. 
        바꿔말하면 2명이상의 유저가 스택이 충분하다면 
        라운드를 진행한다. 
        스택이 충분하다는 판단의 기준은 어떻게 잡을 것인가? 
        올인 유저 발생 후, 올인금액+LPFB <= stack size ?
        모든 플레이어의 핸드는 테이블링된다. 
        (모든 플레이어가 동시에 스타팅 카드를 오픈하고 쇼다운을 한다?)
        이때 모든 라이브 플레이어들은 머킹은 불가능 하다.
 
    예시
    1.
    헤즈업 상황에서 턴 단계일 때
    스택이 작은 한명(the shorter stack)이 올인하고 다른 한명이 콜하면
    두 플레이어는 자신의 스타팅 카드를 모두 동시에 오픈한다.
    그리고 버닝 후 리버카드를 오픈하고 쇼다운을 한다.
 
    2.
    ABC세명이 남은 상황에서 프리플롭 단계일 때
    스택이 가장 작은 한명(the shortest stack) A 이 올인하고 남은 두명이 콜한 경우
    스타팅 카드를 오픈하지 않는다. 
    왜냐면 남은 BC두명이 아직 스택이 많이 남아 있어서 다음 라운드에서 베팅을 더 할 수 있기 때문이다.
    플랍에서 남은 두명이 체크하면 다음 라운드로 간다.
    턴에서 BC중 한명B이 올인하고 남은 한명C이 콜하면 더이상 베팅할 수 있는 사람이 없으므로
    A, B, C 모두 동시에 스타팅 카드 오픈.
    버닝 후 리버 카드 오픈하고 쇼다운을 한다. 
    이때 B와 C의 사이드 팟을 먼저 분배하고
    그 다음 메인팟을 분해한다.
    Notice: you do not keep A’s cards face down
    until the side pot between B and C is awarded
    A가 먹을 못하게 하려고. 올인했으니까
 
    3.
    세명이 남은 프리플랍에서
    A가 700 올인하고 B, C는 콜. 메인팟 최소 2100 형성. 다음 라운드 진행
    플랍에서 B, C 체크. 다음 라운드 진행
    턴에서 B 1000 베팅, C 콜. 사이드팟 2000 형성. 다음 라운드 진행.
    리버에서 B, C 체크.
    이제 A, B, C 모두 스타팅 카드 동시에 오픈. 쇼다운 진행.
    사이드팟 먼저 배분. 그 다음 메인 팟 배분.
 
    Notice: you do not keep A’s cards face down
    until the side pot between B and C is awarded
    A가 먹을 못하게 하려고. 올인했으니까

# (now)
    rule 17: Non All-In Showdowns and Showdown Order (rule 18참고)
        올인이 아닌 쇼다운에서, 플레이어가 카드를 자발적으로 오픈하거나 버리지 않는 경우
        핸드 공개 순서를 강제할 수 있다. 
        마지막 라운드에서 베팅이 있었던 경우, 
            마지막 어그레서의 카드부터 딜링방향으로 오픈
        마지막 라운드에서 베팅이 없었던 경우, 
            가장 먼저 액션을 할 차례였던 플레이어부터 딜링 방향으로 테이블링
        
        올인이 아닌 쇼다운에서 한명을 제외하고 나머지 모든 플레이어가 먹을 한경우, 
        먹을 하지 않은 한 명의 플레이어가 승리하며 이때 카드를 오픈하지 않는다
 
 

    rule 18:  Asking to See a Hand
    
    (later)
    리버에서 베팅이 있었을 경우, 
    쇼다운에서 테이블링한 플레이어들은 마지막 어그레서의 핸드를 테이블링 시킬수 있는 권리를 가진다.
     
    올인이 아닌 쇼다운시,
    플레이어는 자신의 카드를 뒷면인 상태로 버릴수도 있고, 공개하지 않고 그대로 앞으로 밀어 폴드할수도 있다.
    카드를 버린 경우, 딜러는 먹으로 밀어넣어 먹 처리한다.
    여기서 마지막 라운드에 베팅이 없었을 경우, 
    앞으로 밀어 폴드한 플레이어의 카드를 다른 플레이어가 공개요청한 경우 그 판단은 TD의 재량이다.
    마지막 라운드에 베팅이 있었을 경우, 라스트 어그레서가 쇼다운에서 카드를 공개하지 않고 그대로 앞으로 밀어 폴드한 경우
    이미 테이블링한 콜러는 라스트어그레서에게 카드 공개 요청을 할 수 있는 권리가 있다.
    이미 테이블링한 콜러가, 라스트 어그레서는 아니지만 베팅에 콜한 다른 콜러(아직 테이블링 안함)에게 카드 공개 요청을 한 경우 그 판단은 TD의 재량이다
 
# (now)
    올인이 아닌 쇼다운
        마지막 라운드에 베팅이 있었던 경우
                    라스트 어그레서부터 딜링방향으로 오픈                  
        마지막 라운드에 베팅이 없었던 경우
                    마지막 라운드의 첫번째 액션 차례였던 플레이어부터 딜링방향으로 오픈
--------------------------------------------------------------------------------
    (later)
    올인이 아닌 쇼다운
        마지막 라운드에 베팅이 있었던 경우
            플레이어는 자발적으로 카드를 모두 오픈할 수도 있고, 
            카드를 오픈하지 않고 앞으로 밀어 승부를 포기할 수 있다. 
                자발적 오픈이 하나도 없는 경우
                    라스트 어그레서부터 딜링방향으로 오픈  
                    (승부를 포기한 플레이어의 카드 오픈은 딜링방향 오픈을 먼저 하면서 일단 패스하고, 
                    딜링방향 오픈이 다 끝나면 이미 자발적 오픈한 플레이어에게 오픈 요청 의사를 물어,
                    의사가 있는 경우 오픈)
                자발적 오픈이 한명이라도 있는 경우
                    오픈하지 않은 플레이어들 중, 라스트 어그레서 위치부터 딜링방향으로 오픈 
                    (승부를 포기한 플레이어의 카드 오픈은 딜링방향 오픈을 먼저 하면서 일단 패스하고, 
                    딜링방향 오픈이 다 끝나면 이미 자발적 오픈한 플레이어에게 오픈 요청 의사를 물어,
                    의사가 있는 경우 오픈)
                
    마지막 라운드에 베팅이 없었던 경우
        플레이어는 자발적으로 카드를 모두 오픈할 수도 있고, 
        카드를 오픈하지 않고 앞으로 밀어 승부를 포기할 수 있다.
            자발적 오픈이 하나도 없는 경우
                마지막 라운드의 첫번째 액션 차례였던 플레이어부터 딜링방향으로 오픈 
                (승부를 포기한 플레이어의 카드 오픈은 패스) 
            자발적 오픈이 한명이라도 있는 경우
                오픈하지 않은 플레이어들 중, 첫번째 액션 차례였던 플레이어부터 딜링방향으로 오픈 
                (승부를 포기한 플레이어의 카드 오픈은 패스) 
 
--------------------------------------------------------------------------------
 
    rule 29: Calling for a Clock 

# (now)
    액션 타임은 기본 15초.

    (later)
    15초가 지났을 때 플레이어는 라운드 당 2회의 타임을 요청할 수 있다.
    (타임 요청 버튼을 누르지 않으면) 15초가 지났을 때 다음 순서로 넘어간다. 
    그때 어떤 액션버튼도 누르지 않으면 폴드처리된다.
    타임 요청 버튼을 누르면 30초가 주어지고 마지막 5초는 카운트 다운된다. 
 
    플롭 이후에 한해서 
    라운드 당 2회의 타임 요청을 다 썼을 때, 
    해당 라운드에서 추가 타임 요청을 원할 경우 활성화된 플레이어의 과반수 이상이 찬성하면 
    타임이 주어진다.
    이때 추가 타임을 요청 받은 다른 플레이어들은 3초 이내에 찬반을 선택하고 
    선택하지 않으면 찬성으로 자동 처리된다. 

    (later)
    rule 31: At the Table with Action Pending 
        구현시, 
        live hands 를 갖고 있는 플레이어가 게임 도중 무단이탈 2회 이상 하면 페널티를 준다.
         쇼다운시 테이블링 의무가 있는 플레이어의 무단이탈은 1회부터 페널티를 주고, 누적 페널티를 적용한다.  
    (later)
    rule 33: Dodging Blinds
        구현시,
        블라인드 자리에 배정이 되고 난 후 무단 이탈은 2회차부터 페널티를 준다. 누적 페널티 적용한다.

    (later)
    rule 22: Disputed Hands and Pots 
    The reading of a tabled hand may be disputed until the next hand begins (see Rule 23). 
    Accounting errors in calculating and awarding the pot may be disputed until substantial action occurs on the next hand. 
    If a hand finishes during a break, the right to any dispute ends 1 minute after the pot is awarded.
 
        구현시, 
        테이블링에 이의를 제기하고 싶은 경우
        pot이 award된 다음 1분 이내 가능.


    rule 34: Button in Heads-up (구현 불필요)
        각 라운드별 헤즈업 상황에서 두 플레이어의 포지션 및 액션순서
        프리플랍에서 헤즈업 : SB가 버튼 겸한다. SB가 먼저 액션한다.
        플랍, 턴, 리버에서 헤즈업 : SB가 버튼 겸한다. SB가 마지막에 액션한다
        헤즈업에서 한플레이어가 그 핸드에서 연속으로 BB가 되지 않도록 버튼을 조정할 수 있다.
 
 
 
 
 
 
 
 
 
