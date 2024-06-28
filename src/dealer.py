from src import Base
from collections import deque
from collections import OrderedDict

rings = 6  # robby 에서 전달 받음
user_id_list = ['1', '2', '3', '4', '5', '6'] # robby 에서 전달 받음
stakes = "low"   # robby 에서 전달 받음
stk_size = {'1' : 110, '2' : 120, '3' : 130, '4' : 140, '5' : 150, '6' : 160}  # SQL DB에서 전달 받음


class Dealer(Base):

    def __init__(self, user_id_list, stk_size, rings, stakes):
        super().__init__(user_id_list, stk_size, rings, stakes)
        
        if self.rings == 6:
            self.start_order = deque(["UTG", "HJ", "CO", "D", "SB", "BB"])
        elif self.rings == 9:
            self.start_order = deque(['UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D', 'SB', 'BB'])

        self.main_pot = 0
        self.pot_change = [self.main_pot]
        self.main_pot_confirmed = OrderedDict()

        self.action_queue = deque([])
        self.actioned_queue = deque([])
        self.all_in_users = []
        self.fold_users = []
        self.check_users = []

        self.attack_flag = True # only only and just once bet, raise, all-in is True  # 플롭부터는 False로 초기화
        self.raise_counter = 0 # 5가 되면 Possible action 에서 raise 삭제. 구현 필요
        self.reorder_flag = False # 현재 액션 유저를 기준으로 actioned_queue에 있는 유저들을 start_order 리스트 뒤에 붙이는 reorder를 금지시키기 위한 플래그

        self.survivors = [] # 다음 스트릿으로 갈 생존자 리스트
        self.this_street_players_num = rings
        self.deep_stack_user_counter = 0

        self.raised_total = 0 # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
        self.all_in_amount = 0   # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
        self.bet_amount = 0 # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
         
        self.LPFB = self.BB # the largest prior full bet
        self.prev_VALID = self.BB  # 콜시 유저의 스택에 남아 있어야 하는 최소 스택 사이즈의 기준
        self.prev_TOTAL = self.prev_VALID + self.LPFB # 레이즈시 유저의 스택에 남아있어야 하는 최소 스택 사이즈의 기준

        self.short_stack_end_flag = False # 올인 발생시 딥스택 유저 수 부족으로 바로 핸드 종료시키는 조건
        self.deep_stack_end_flag = False 
        self.no_all_in_end_flag = False
        self.all_check_end_flag = False
        self.deep_stack_continue_flag = False

        self.burned_cards = []
        self.flop_cards = []
        self.turn_cards = []
        self.river_cards = []

    def _posting_blind(self):
        if self.stakes == "low":
            self.players["SB"]["stk_size"] -= self.SB
            self.players["BB"]["stk_size"] -= self.BB
            self.players["SB"]["actions"]["pre_flop"]["betting_size"]["bet"].append(self.SB)
            self.players["SB"]["actions"]["pre_flop"]["action_list"].append("bet")
            self.players["BB"]["actions"]["pre_flop"]["betting_size"]["bet"].append(self.BB)
            self.players["BB"]["actions"]["pre_flop"]["action_list"].append("bet")
            self.main_pot += (self.SB + self.BB)

    def _possible_actions(self, street_name, current_player):

        player_stack = self.players[current_player]['stk_size']

        if street_name == 'pre_flop':
            # BB 옵션 구현 및 BB check 구현, 프리플롭에서만 사용
            if len(self.actioned_queue) + len(self.fold_users) == rings - 1 and self.raised_total == 0:
                if self.prev_TOTAL <= player_stack:
                    possible_actions = ["check", "raise", "fold", "all-in"]
                elif self.prev_VALID <= player_stack < self.prev_TOTAL:
                    possible_actions = ["check", "fold", "short-all-in"]
                elif player_stack < self.prev_VALID:
                    possible_actions = ["fold", "short-all-in"]
                else:
                    pass
            else:
                if self.prev_TOTAL <= player_stack:
                    possible_actions = ["call", "raise", "fold", "all-in"]
                elif self.prev_VALID <= player_stack < self.prev_TOTAL:
                    possible_actions = ["call", "fold", "short-all-in"]
                elif player_stack < self.prev_VALID:
                    possible_actions = ["fold", "short-all-in"]
                else:
                    pass

        else:
            if not self.attack_flag:  # not attacked
                if self.prev_VALID <= player_stack:
                    possible_actions = ["bet", "check", "fold", "all-in"]
                elif player_stack < self.prev_VALID:
                    possible_actions = ["check", "fold", "short-all-in"]
                else:
                    pass
            elif self.attack_flag:  # attacked
                if player_stack >= self.prev_TOTAL:
                    if self.raise_counter <= 5:
                        possible_actions = ["call", "raise", "fold", "all-in"]
                    else:
                        possible_actions = ["call", "fold", "all-in"]
                elif self.prev_VALID <= player_stack < self.prev_TOTAL:
                    possible_actions = ["call", "fold", "short-all-in"]
                elif player_stack < self.prev_VALID:
                    possible_actions = ["fold", "short-all-in"]
                else:
                    pass
            else:
                pass


        return possible_actions
    
    def _live_players_update(self, street_name):
        '''
        현재 접속중인 클라이언트 카운트
        '''
        if street_name == 'pre_flop':          
            self.this_street_players_num = rings - len(self.fold_users)
        else:
            self.this_street_players_num = len(self.survivors) - len(self.fold_users)

    def _call(self, street_name, current_player):

        if current_player in self.check_users:
            self.check_users.remove(current_player)      

        if street_name == 'pre_flop':
            # 현재 액션이 첫번째 액션이 아닌 경우
            if self.players[current_player]["actions"][street_name]["action_list"]:
                last_action = self.players[current_player]["actions"][street_name]["action_list"][-1]
                self.players[current_player]["stk_size"] -= (self.prev_VALID - self.players[current_player]["actions"][street_name]["betting_size"][last_action])
                self.players[current_player]["actions"][street_name]["action_list"].append("call")
                self.players[current_player]["actions"][street_name]["betting_size"]["call"].append(self.prev_VALID)

                self.main_pot += (self.prev_VALID - self.players[current_player]["actions"][street_name]["betting_size"][last_action])
            # 현재 액션 콜이 첫번째 액션인 경우
            else:
                last_action = "call"
                self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
                self.players[current_player]["actions"][street_name]["betting_size"]["call"].append(self.prev_VALID)

                self.main_pot += self.prev_VALID
        else:
            # 현재 액션이 첫번째 액션이 아니고 마지막으로 한 액션이 check이 아닌 경우
            if self.players[current_player]["actions"][street_name]["action_list"] and self.players[current_player]["actions"][street_name]["action_list"][-1] != 'check':
                last_action = self.players[current_player]["actions"][street_name]["action_list"][-1]
                self.players[current_player]["stk_size"] -= (self.prev_VALID - self.players[current_player]["actions"][street_name]["betting_size"][last_action])
                self.players[current_player]["actions"][street_name]["action_list"].append("call")
                self.players[current_player]["actions"][street_name]["betting_size"]["call"].append(self.prev_VALID)

                self.main_pot += (self.prev_VALID - self.players[current_player]["actions"][street_name]["betting_size"][last_action])
            # 현재 액션 콜이 첫번째 액션인 경우 또는 마지막으로 했던 액션이 체크였던 경우
            else:
                last_action = "call"
                self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
                self.players[current_player]["actions"][street_name]["betting_size"]["call"].append(self.prev_VALID)

                self.main_pot += self.prev_VALID                    


        self.pot_change.append(self.prev_VALID) # 팟 변화량 업데이트

        self.actioned_queue.append(self.action_queue.popleft())

        '''
        모든 클라이언트들에게 다음을 요청
        콜한 클라이언트의 스택 사이즈를 self.prev_VALID 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 prev_VALID을 더한 결과로 렌더링
        '''

    def _raise(self, street_name, current_player, answer):

        if current_player in self.check_users:
            self.check_users.remove(current_player)      

        # raised_total : 클라이언트에게서 전달받은 레이즈 액수 (레이즈 액수는 total을 의미.)
        self.raised_total = answer["raise"]

        self.LPFB = self.raised_total - self.prev_VALID # LPFB 업데이트
        self.prev_VALID = self.raised_total # prev_VALID 업데이트
        self.prev_TOTAL = self.LPFB + self.prev_VALID # prev_TOTAL 업데이트

        if street_name == 'pre_flop':
        # 현재 액션이 첫번째 액션이 아닌 경우
            if self.players[current_player]["actions"][street_name]["action_list"]:
                last_action = self.players[current_player]["actions"][street_name]["action_list"][-1]
                self.players[current_player]["stk_size"] -= (self.raised_total - self.players[current_player]["actions"][street_name]["betting_size"][last_action])
                self.players[current_player]["actions"][street_name]["action_list"].append("raise")
                self.players[current_player]["actions"][street_name]["betting_size"]["raise"].append(self.raised_total)
            
                self.main_pot += (self.raised_total - self.players[current_player]["actions"][street_name]["betting_size"][last_action])
            # 현재 액션 레이즈가 첫번째 액션인 경우
            else:
                last_action = "raise"
                self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
                self.players[current_player]["actions"][street_name]["betting_size"]["raise"].append(self.raised_total)

                self.main_pot += self.raised_total # 메인팟 업데이트
        else:
        # 현재 액션이 첫번째 액션이 아니고 마지막으로 한 액션이 check이 아닌 경우
            if self.players[current_player]["actions"][street_name]["action_list"] and self.players[current_player]["actions"][street_name]["action_list"][-1] != 'check':
                last_action = self.players[current_player]["actions"][street_name]["action_list"][-1]
                self.players[current_player]["stk_size"] -= (self.raised_total - self.players[current_player]["actions"][street_name]["betting_size"][last_action])
                self.players[current_player]["actions"][street_name]["action_list"].append("raise")
                self.players[current_player]["actions"][street_name]["betting_size"]["raise"].append(self.raised_total)
            
                self.main_pot += (self.raised_total - self.players[current_player]["actions"][street_name]["betting_size"][last_action])        
                # 현재 액션 레이즈가 첫번째 액션인 경우 또는 마지막으로 했던 액션이 체크였던 경우
            else:
                last_action = "raise"
                self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
                self.players[current_player]["actions"][street_name]["betting_size"]["raise"].append(self.raised_total)

                self.main_pot += self.raised_total # 메인팟 업데이트
            

        self.pot_change.append(self.raised_total) # 팟 변화량 업데이트

        self.attack_flag = True

        self.raise_counter += 1

        # 액션큐 처리. 올인/벳 동일
        if self.actioned_queue is not None:
            for actor in self.actioned_queue:
                self.start_order.append(actor)
            self.actioned_queue = deque([])
            self.actioned_queue.append(self.action_queue.popleft())
        else:
            self.actioned_queue.append(self.action_queue.popleft())

        '''
        모든 클라이언트들에게 다음을 요청
        레이즈한 클라이언트의 스택 사이즈를 raised_total 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 raised_total을 더한 결과로 렌더링
        '''
    
    def _all_in(self, street_name, current_player, answer, side_pot):

        if current_player in self.check_users:
            self.check_users.remove(current_player)      

        '''
        모든 클라이언트들에게 다음을 요청
        올인한 클라이언트에게 올인 버튼 렌더링(지속형 이벤트)
        '''
        # all_in_amount : 클라이언트에게서 전달받은 올인액수 (total을 의미)
        self.all_in_amount = answer['all-in']

        if street_name == 'pre_flop':
            if self.prev_TOTAL <= self.all_in_amount:
                self.LPFB = self.all_in_amount - self.prev_VALID
                self.VALID = self.all_in_amount
                self.prev_TOTAL = self.VALID + self.LPFB

            elif self.prev_VALID <= self.all_in_amount < self.prev_TOTAL:
                self.prev_VALID = self.all_in_amount
                self.prev_TOTAL = self.prev_VALID + self.LPFB

            elif self.all_in_amount < self.prev_VALID:
                self.reorder_flag = False
                pass # 구현 불필요
        
        else:
            if self.attack_flag == False: # 해당 올인이 open-bet인 경우
                if self.prev_TOTAL <= self.all_in_amount:
                    self.LPFB = self.all_in_amount
                    self.VALID = self.all_in_amount
                    self.prev_TOTAL = self.VALID + self.LPFB

                elif self.prev_VALID <= self.all_in_amount < self.prev_TOTAL:
                    self.LPFB = self.all_in_amount
                    self.prev_VALID = self.all_in_amount
                    self.prev_TOTAL = self.prev_VALID + self.LPFB
                
                elif self.all_in_amount < self.prev_VALID:
                    pass # 구현 불필요

            else:  # 해당 올인이 open-bet이 아닌 경우
                if self.prev_TOTAL <= self.all_in_amount:
                    self.LPFB = self.all_in_amount - self.prev_VALID
                    self.VALID = self.all_in_amount
                    self.prev_TOTAL = self.VALID + self.LPFB

                elif self.prev_VALID <= self.all_in_amount < self.prev_TOTAL:
                    self.prev_VALID = self.all_in_amount
                    self.prev_TOTAL = self.prev_VALID + self.LPFB

                elif self.all_in_amount < self.prev_VALID:
                    pass # 구현 불필요

        if street_name == 'pre_flop':
            # 현재 액션이 첫번째 액션이 아닌 경우
            if self.players[current_player]["actions"][street_name]["action_list"]:
                last_action = self.players[current_player]["actions"][street_name]["action_list"][-1]
                self.players[current_player]["stk_size"] -= (self.prev_VALID - self.players[current_player]["actions"][street_name]["betting_size"][last_action])
                self.players[current_player]["actions"][street_name]["action_list"].append("all_in")
                self.players[current_player]["actions"][street_name]["betting_size"]["all-in"].append(self.all_in_amount)
                
                self.main_pot += (self.all_in_amount - self.players[current_player]["actions"][street_name]["betting_size"][last_action])
            # 현재 액션 올인이 첫번째 액션인 경우
            else:
                last_action = "all-in"
                self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
                self.players[current_player]["actions"][street_name]["betting_size"]["all-in"].append(self.all_in_amount)

                self.main_pot += self.all_in_amount # 메인팟 업데이트
        else:
            # 현재 액션이 첫번째 액션이 아니고 마지막으로 한 액션이 check이 아닌 경우
            if self.players[current_player]["actions"][street_name]["action_list"] and self.players[current_player]["actions"][street_name]["action_list"][-1] != 'check':
                last_action = self.players[current_player]["actions"][street_name]["action_list"][-1]
                self.players[current_player]["stk_size"] -= (self.prev_VALID - self.players[current_player]["actions"][street_name]["betting_size"][last_action])
                self.players[current_player]["actions"][street_name]["action_list"].append("all_in")
                self.players[current_player]["actions"][street_name]["betting_size"]["all-in"].append(self.all_in_amount)
            
                self.main_pot += (self.all_in_amount - self.players[current_player]["actions"][street_name]["betting_size"][last_action])                
            # 현재 액션 올인이 첫번째 액션인 경우 또는 마지막으로 했던 액션이 체크였던 경우
            else:
                last_action = "all-in"
                self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
                self.players[current_player]["actions"][street_name]["betting_size"]["all-in"].append(self.all_in_amount)

                self.main_pot += self.all_in_amount # 메인팟 업데이트

        self.pot_change.append(self.all_in_amount) # 팟 변화량 업데이트

        self.attack_flag = True

        # 액션큐 처리. 레이즈/벳 동일
        if self.reorder_flag == True and self.actioned_queue is not None:
            for actor in self.actioned_queue:
                self.start_order.append(actor)
            self.actioned_queue = deque([])
            self.all_in_users.append(self.action_queue.popleft())
        elif self.reorder_flag == False or len(self.actioned_queue) == 0:  # code_explanation.MD 참고
            self.all_in_users.append(self.action_queue.popleft())
            self.reorder_flag = True

        '''
        모든 클라이언트들에게 다음을 요청
        올인한 클라이언트의 스택 사이즈를 self.all_in_amount 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 self.all_in_amount을 더한 결과로 렌더링
        '''
        # 프리플롭, 플롭, 턴에서 올인 발생시 딥스택 유저 수 부족으로 인한 핸드 종료조건
        if not street_name == 'river':
            for position in self.start_order:
                if self.prev_TOTAL < self.players[position]['stk_size']:
                    self.deep_stack_user_counter += 1

            # 올인 유저 제외 남은 라이브 플레이어들 중 한명 이하만 (올인에 콜하고 나아가 레이즈 까지 할 수 있는)딥스택인 경우
            # 핸드 종료 showdown3 호출, main_pot 만 사용해 pot awarding
            if self.deep_stack_user_counter < 2:
                self.short_stack_end_flag == True
            
            # 올인 유저 제외 남은 라이브 플레이어들 중 2명 이상이 딥스택인 경우, 스트릿 계속 진행
            else:
                pass

        # 리버에서 올인 발생시 곧바로 showdown
        else:
            self._showdown_all_in(side_pot)
            if side_pot == False:
                self.main_pot

            elif side_pot == True:
                self.main_pot_confirmed
            
    def _check(self, street_name, current_player):
        last_action = "check"
        self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
        self.check_users.append(current_player)
        self.actioned_queue.append(self.action_queue.popleft())
        '''
        모든 클라이언트들에게 다음을 요청
        체크한 플레이어가 체크했음을 렌더링       
        '''

    def _bet(self, street_name, current_player, answer):

        if current_player in self.check_users:
            self.check_users.remove(current_player)      

        # bet_amount : 클라이언트에게서 전달받은 베팅액수
        self.bet_amount = answer['bet']

        self.LPFB = self.bet_amount
        self.VALID = self.bet_amount
        self.prev_TOTAL = self.VALID + self.LPFB

        # bet은 항상 첫번째 액션
        last_action = "bet"
        self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
        self.players[current_player]["actions"][street_name]["betting_size"]["bet"].append(self.bet_amount)

        self.main_pot += self.bet_amount # 메인팟 업데이트
        self.pot_change.append(self.bet_amount) # 팟 변화량 업데이트

        self.attack_flag = True 

        # 액션큐 처리. 올인/레이즈 동일
        if self.actioned_queue is not None:
            for actor in self.actioned_queue:
                self.start_order.append(actor)
            self.actioned_queue = deque([])
            self.actioned_queue.append(self.action_queue.popleft())
        else:
            self.actioned_queue.append(self.action_queue.popleft())

        '''
        모든 클라이언트들에게 다음을 요청
        베팅한 클라이언트의 스택 사이즈를 self.bet_amount 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 self.bet_amount을 더한 결과로 렌더링
        '''
    
    def _short_stack_end(self, street_name):
        '''
        남은 라이브 클라이언트 모두에게 액션 요청 (call, fold 버튼만 활성화)
        '''
        self.action_queue.append(self.start_order.popleft())

        while self.action_queue: 
            current_player = self.action_queue[0]
            possible_actions = ["call", "fold"]           
            answer = input()                 
            if answer == "call":
                self._call_preFlop(self, current_player)

            elif answer == "fold": 
                self.fold_users.append(self.action_queue.popleft())

            self.action_queue.append(self.start_order.popleft())
        
        self._live_players_update(street_name)
        # 올인 유저가 한명있고 모두 폴드한 경우
        if len(self.all_in_users) == 1 and len(self.fold_users) == self.this_street_players_num - 1:
            side_pot = False
            winner_confirmed = True
            return side_pot, winner_confirmed

        # 올인 유저가 한명있고 콜 또는 폴드한 사람 있는 경우
        elif len(self.all_in_users) == 1 and len(self.fold_users) + len(self.actioned_queue) == self.this_street_players_num - 1:
            side_pot = False
            winner_confirmed = False
            return side_pot, winner_confirmed


    def _deep_stack_end(self, street_name):
        
        # main_pot_confirmed 계산
        all_user = []
        for position in self.actioned_queue:
            all_user.append(position)
        for position in self.all_in_users:
            all_user.append(position)
        for position in self.fold_users:
            all_user.append(position)

        main_pot_sum = 0
        
        for all_in_position in self.all_in_users:
            all_in_size = self.players[all_in_position]["actions"][street_name]["betting_size"]["all-in"]
            for position in all_user:
                last_action = self.players[position]["actions"][street_name]["action_list"][-1]
                last_betting_size = self.players[position]["actions"][street_name]["betting_size"][last_action]
                if last_betting_size >= all_in_size:
                    main_pot_sum += all_in_size
                else:
                    main_pot_sum += last_betting_size
            self.main_pot_confirmed[all_in_position] = main_pot_sum

        side_pot = True

        return side_pot

    def preFlop(self):
        
        '''
        프리플롭 메서드 호출시 
        최초로 액션할 유저가 응답 가능한지 확인하고 
        액션큐 등록
        불가능하면 폴드 처리하고 다음 유저에게 물어보는 루프로 바꿀 것
        '''
        self.action_queue.append(self.start_order.popleft())
        street_name = "pre_flop"

        while self.action_queue:

            '''
            while문 진입시마다, start_order에 있는 모든 클라이언트들 접속 중인지 응답 요청, 
            접종된 유저는 모두 fold_users 처리
            '''
            self._live_players_update(street_name)

            self._posting_blind()

            '''
            모든 클라이언트들에게 다음을 요청
            1. 스타팅 카드 전송 후 렌더링
            2. start_order 에 있는 유저만 남기고 나머지 유저들 삭제 렌더링
            '''

            current_player = self.action_queue[0]
                     
            possible_actions : list = self._possible_actions(street_name, current_player)
            
            '''
            current_player에 해당하는 클라이언트에게 possible_actions 전달, 응답 요청
            '''
            
            '''
            클라이언트의 응답 
            anwer 딕셔너리
            '''
                   
            answer = input() # 레이즈는 {"raise" : raised_total} 올인은 {"all-in" : all_in_amount} 벳은 {"bet" : bet_amount}

            self.log_hand_actions[street_name].append((current_player, answer)) # 유저 액션 기록    

            # 클라이언트에게 전달 받은 응답이 call 이면
            if answer == "call":
                self._call(street_name, current_player)

            # 클라이언트에게 전달 받은 응답이 fold 면 
            elif answer == "fold":
                self.fold_users.append(self.action_queue.popleft())

            # 클라이언트로부터 전달 받은 응답이 answer = {"raise" : raised_total} 이면
            elif next(iter(answer)) == "raise":
                self._raise(street_name, current_player, answer)

            # 클라이언트로부터 전달 받은 응답이 answer = {"all-in" : all_in_amount} 이면
            elif next(iter(answer)) == "all-in":
                self._all_in(street_name, current_player, answer)

            # 클라이언트에게 전달 받은 응답이 check 면      
            elif answer == "check":  # BB 만 가능
                self._check(current_player)


            self._live_players_update(street_name)

            # 핸드 종료조건 (올인이 일어난 경우) 최초 올인 이후 다른 유저들의 액션 불가능해서 main_pot으로 award 하는 경우    
            if self.short_stack_end_flag == True: # main_pot으로 pot award
                break # 검토 완료.

            # 핸드 종료조건 (올인이 일어난 경우) 모든 유저가 올인한 경우
            if self.all_in_users == len(self.this_street_players_num) and len(self.actioned_queue) == 0:
                self.deep_stack_end_flag = True
                break

                
            # 스트릿 종료조건 (올인이 일어난 경우) 올인 유저가 여러 명 가능해서 main_pot_confirmed로 award 하는 경우
            if self.start_order == 0 and len(self.all_in_users) > 1:
                self.deep_stack_continue_flag = True
                break
            
            # 스트릿 종료조건 (올인이 일어나지 않은 경우)
            # 모두 check 한 경우
            if len(self.check_users) == len(self.this_street_players_num):
                if street_name == 'river':
                    self.all_check_end_flag = True
                    break
                else:
                    pass # 다음 스트릿으로 이동                

            # 핸드/스트릿 종료 조건 (올인이 일어나지 않은 경우)
            # 마지막 스트릿에 베팅이 있었던 경우
            if len(self.start_order) == 0 and len(self.all_in_users) == 0 and len(self.check_users) == 0 : 

                # 한명만 남기고 모두 fold한 경우 : 핸드 종료, main_pot으로 pot award
                self._live_players_update(street_name)
                if self.this_street_players_num == 1 and len(self.check_users) == 0:
                    self.no_all_in_end_flag = True
                    break

                # call 한 사람이 있는 경우 : 스트릿 종료, 다음 스트릿으로 이동, main_pot 승계
                elif self.this_street_players_num > 1:
                    if street_name == 'river':
                        self.no_all_in_end_flag = True
                        break
                    else:
                        break # 다음 스트릿으로

            self.action_queue.append(self.start_order.popleft())

        if self.short_stack_end_flag == True:
            side_pot, winner_confirmed = self._short_stack_end(self)
            self._showdown_all_in(side_pot, winner_confirmed) # self.main_pot 사용
        
        if self.deep_stack_end_flag == True:
            side_pot = self._deep_stack_end(self)
            self._showdown_all_in(side_pot, winner_confirmed)

        if self.all_check_end_flag == True:
            self._showdown_all_check(self)

        if self.no_all_in_end_flag == True:
            self._showdown_no_all_in(self)

        if self.deep_stack_continue_flag == True:
            side_pot = self._deep_stack_end(self)

        # 다음 스트릿으로 갈 플레이어 survivors 리스트 리턴
        self.log_hand_main_pots[street_name] = self.main_pot
        self.survivors.extend(self.actioned_queue)
        
        self._live_players_update(street_name)  
        self.this_street_players_num = len(self.survivors)

        return side_pot
    
    def flop(self, side_pot):
        
        '''
        초기화 해줘야 할 인스턴스 변수들 초기화
        self.all_in_users 초기화 해줄 것.
        self.fold_users 는 그대로 

        '''

        self.attack_flag = False # 플롭 이후부터는 attack_flag = False 가 디폴트

        self.burned_cards.append(self.stub.pop(0)) # 플롭 버닝
        for _ in range(3):
            self.flop_cards.append(self.stub.pop(0))

        if self.rings == 6:
            self.start_order = deque(["SB", "BB","UTG", "HJ", "CO", "D"])
            for position in self.start_order:
                if position not in self.survivors:
                    self.start_order.popleft()
            
        elif self.rings == 9:
            self.start_order = deque(['SB', 'BB', 'UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D'])
            for position in self.start_order:
                if position not in self.survivors:
                    self.start_order.popleft()

        '''
        플롭 메서드 호출시 
        최초로 액션할 유저가 응답 가능한지 확인하고 
        액션큐 등록
        불가능하면 폴드 처리하고 다음 유저에게 물어보는 루프로 바꿀 것
        '''
        self.action_queue.append(self.start_order.popleft())

        street_name = "flop"

        while self.action_queue:

            '''
            while문 진입시마다, start_order에 있는 모든 클라이언트들 접속 중인지 응답 요청, 
            접종된 유저는 모두 fold_users 처리
            '''
            self._live_players_update(street_name)

            '''
            모든 클라이언트들에게 다음을 요청
            1. 플롭 카드 전송 후 렌더링
            2. start_order 에 있는 유저만 남기고 나머지 유저들 삭제 렌더링
            '''

            current_player = self.action_queue[0]             

            possible_actions : list = self._possible_actions(street_name, current_player)
            
            '''
            current_player에 해당하는 클라이언트에게 possible_actions 전달, 응답 요청
            '''
            
            '''
            클라이언트의 응답 
            anwer 딕셔너리
            '''

            answer = input() 

            self.log_hand_actions[street_name].append((current_player, answer)) # 유저 액션 기록    

            # 클라이언트에게 전달 받은 응답이 call 이면
            if answer == "call":
                self._call(street_name, current_player)
            
            # 클라이언트에게 전달 받은 응답이 fold 면 
            elif answer == "fold":
                self.fold_users.append(self.action_queue.popleft())

            # 클라이언트로부터 전달 받은 응답이 answer = {"raise" : raised_total} 이면
            elif next(iter(answer)) == "raise":
                self._raise(street_name, current_player, answer)

            # 클라이언트로부터 전달 받은 응답이 answer = {"all-in" : all_in_amount} 이면
            elif next(iter(answer)) == "all-in":
                self._all_in(street_name, current_player, answer)
            
             # 클라이언트로부터 전달 받은 응답이 check 면
            elif answer == "check":
                self._check(street_name, current_player)

            # 클라이언트로부터 전달 받은 응답이 answer = {"bet" : bet_amount} 이면
            elif next(iter(answer)) == "bet":
                self._bet(street_name, current_player, answer)

            if self.short_stack_end_flag == True: # 핸드 종료, main_pot으로 pot award
                self._short_stack_end(self)

            # 리버 종료 조건 (올인이 일어난 경우) 마지막 올인에 대해 모든 유저가 올인 또는 콜 또는 폴드로 대답한 경우만 따지면 끝
            # 바꿔 말하면 리버에서 쓰이는 올인만 따로 구현하면 된다.

            # 플롭, 턴, 리버 종료조건 (올인이 일어나지 않은 경우)
            # main_pot 만 사용해 pot awarding
            if len(self.all_in_users) == 0 and len(self.start_order) == 0: 
                # 올인이 일어나지 않은 쇼다운
                # 마지막 스트릿에 베팅이 있었던 경우
                # 한명만 남기고 모두 fold한 경우 : 핸드 종료
                if len(self.fold_users) == self.survivors - 1:
                    return  # showdown1 으로
                # call 한 사람이 있는 경우 : 스트릿 종료
                elif len(self.fold_users) + len(self.actioned_queue) == self.survivors - 1:
                    return # 다음 스트릿으로, 리버인 경우 showdown1 으로
                # 마지막 스트릿에 베팅이 없었던 경우 : 스트릿 종료
                elif len(self.actioned_queue) == self.survivors: 
                    return # 다음 스트릿으로, 리버인 경우 showdown2 로

            self.action_queue.append(self.start_order.popleft())

        self.log_hand_main_pots[street_name] = self.main_pot
        # 다음 스트릿으로 갈 플레이어 survivors 리스트 리턴
        
        self.survivors.extend(self.actioned_queue)

        return
    
    def trun(self):
        pass

    def river(self):
        pass

    '''
    쇼다운 구현 ㄱ,ㄴ,ㄷ,ㄹ 4개 필요
    1. 올인이 아닌 쇼다운
        a. 남은 커뮤니티 카드들을 하나씩 모두 오픈하고 
            1) 마지막 스트릿에 베팅이 있었던 경우 (bet, 또는 raise가 있었고 모두 콜 또는 폴드한 경우) : showdown1
                ㄱ. 라스트 어그레서부터 딜링방향으로 모두 오픈 후(폴드 유저 제외) 승자 판정 
                ㄴ. 모두 폴드한 경우엔 아무도 테이블링 하지 않는다. 베팅한 사람 바로 승자 판정
            2) 마지막 스트릿에 베팅이 없었던 경우 (모두 check한 경우) : showdown2
                ㄷ. 마지막 스트릿의 첫번째 액션 차례였던 플레이어부터 딜링방향으로 모두 오픈 후 승자 판정
    2. 올인이 있었던 쇼다운 : showdown3
        b. 플레이어의 모든 스타팅 카드가 먼저 테이블링 되고 (폴드 유저 제외)
            ㄹ. 남은 커뮤니티 카드들 하나씩 모두 오픈 후 승자 판정
                main_pot으로 팟 어워딩
    '''
    def _showdown_no_all_in(self):
        self.main_pot # 리버에서 올인 없이 마지막으로 베팅한 사람이 있고 콜한 사람이 있는 경우 호출되거나, 
        # 마지막으로 베팅한 사람 빼고 모두 폴드한 스트릿에서 호출
        return
    
    def _showdown_all_check(self, side_pot):
        if side_pot == False:
            self.main_pot 

        elif side_pot == True:
            self.main_pot_confirmed        
        
        return
    
    def _showdown_all_in(self, side_pot, winner_confirmed = True): 
        if winner_confirmed:
            if not side_pot:  # _short_stack_end 함수에서 호출
                return self.main_pot
            elif side_pot:
                pass
        if side_pot == False and winner_confirmed: # _short_stack_end 함수에서 호출
            self.main_pot 

        elif side_pot == True and winner_confirmed:
            self.main_pot_confirmed

        # 메인 팟 생성 로직에서 last_action이 폴드인 경우 에러가 나므로 여기서 따로 처리
        for position in self.fold_users: 
            self.players[position]["actions"]["flop"]["action_list"].append("fold'")

        return
    


    def award_pot(self):
        pass


if __name__ == '__main__':

    dealer = Dealer(user_id_list, stk_size, rings, stakes)
    # 스트릿 루프 진입 전 클라이언트들에게 모두 제자리에 있는지 응답 요청
    dealer._posting_blind() # 호출후 SB와 BB 클라이언트의 스택사이즈를 블라인드 차감된 양으로 렌더링 요청, 메인팟 업데이트 렌더링 요청
    print(dealer.players)
    print(dealer.players["BB"]["actions"]["pre_flop"]["betting_size"])
    print(dealer.players["BB"]["actions"]["pre_flop"]["action_list"])
    print(dealer.players["BB"]['stk_size'])
