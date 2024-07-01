from src import Base
from collections import deque, OrderedDict

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


        self.this_street_players_num = rings

        self.fold_users = []

        self.main_pot = 0
        self.pot_change = [self.main_pot]
        self.all_in_counter = 0
        self.side_pot = False
        self.main_pot_confirmed = OrderedDict()

        self.survivors = [] # 다음 스트릿으로 갈 생존자 리스트

        self.burned_cards = []
        self.flop_cards = []
        self.turn_cards = []
        self.river_cards = []

        self._initialize_betting_state()
        self._initialize_action_state()
        self._initialize_condition()      

    def _initialize_betting_state(self):
        self.raised_total = 0 # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
        self.all_in_amount = 0   # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
        self.bet_amount = 0 # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신

        self.LPFB = self.BB # the largest prior full bet
        self.prev_VALID = self.BB  # 콜시 유저의 스택에 남아 있어야 하는 최소 스택 사이즈의 기준
        self.prev_TOTAL = self.prev_VALID + self.LPFB # 레이즈시 유저의 스택에 남아있어야 하는 최소 스택 사이즈의 기준

    def _initialize_action_state(self):
        self.action_queue = deque([])
        self.actioned_queue = deque([])

        self.all_in_users = []
        self.check_users = []

        self.attack_flag = False # only only and just once bet, raise, all-in is True  # 플롭부터는 False로 초기화
        self.raise_counter = 0 # 5가 되면 Possible action 에서 raise 삭제. 구현 필요
        self.reorder_flag = False # 현재 액션 유저를 기준으로 actioned_queue에 있는 유저들을 start_order 리스트 뒤에 붙이는 reorder를 금지시키기 위한 플래그

    def _initialize_condition(self):
        self.deep_stack_user_counter = 0
        self.short_stack_end_flag = False # 올인 발생시 딥스택 유저 수 부족으로 바로 핸드 종료시키는 조건
        self.every_all_in_end_flag = False

        self.winner_confirmed = False
        self.user_card_open_first = False
        self.table_card_open_first = False
        self.river_bet_exists = False
        self.river_all_check = False

    def _fold(self, street_name):
        for position in self.fold_users: 
            self.players[position]["actions"][street_name]["action_list"].append("fold'")
        self.fold_users.append(self.action_queue.popleft())

    def _call(self, street_name, current_player):

        if current_player in self.check_users:
            self.check_users.remove(current_player)

        action_list = self.players[current_player]["actions"][street_name]["action_list"]
        betting_size = self.players[current_player]["actions"][street_name]["betting_size"]

        # 현재 액션이 첫번째 액션이 아닌 경우
        if action_list:
            last_action = action_list[-1]
        # 현재 액션 콜이 첫번째 액션인 경우
        else:
            last_action = None

        # 현재 스트리트가 프리플롭이거나 (모든 스트리트에서 현재 액션이 첫 액션이 아니고 마지막 액션이 체크가 아닌 경우)
        if street_name == 'pre_flop' or (action_list and last_action != 'check'):
            if last_action:
                call_amount = self.prev_VALID - betting_size[last_action]
            else:
                call_amount = self.prev_VALID
            
            self.players[current_player]["stk_size"] -= call_amount
            self.main_pot += call_amount
            betting_size["call"].append(self.prev_VALID)
        # 현재 스트리트가 프리플롭이 아니고 (액션리스트가 비어있거나 마지막 액션이 체크인 경우) 
        # 플롭, 턴, 리버에서 현재 액션 콜이 첫 액션인 경우 또는 첫 액션이 체크였고 자기 차례로 돌아와 콜을 한 경우
        else:
            call_amount = self.prev_VALID
            self.main_pot += call_amount
            betting_size["call"].append(call_amount)

        action_list.append("call")
        self.pot_change.append(call_amount)  # 팟 변화량 업데이트
        self.actioned_queue.append(self.action_queue.popleft())

        '''
        모든 클라이언트들에게 다음을 요청
        콜한 클라이언트의 스택 사이즈를 self.prev_VALID 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 prev_VALID을 더한 결과로 렌더링
        '''

    def _raise(self, street_name, current_player, answer):

        if current_player in self.check_users:
            self.check_users.remove(current_player)

        # raised_total : 클라이언트에게서 전달받은 레이즈 액수 (레이즈 액수는 total을 의미)
        self.raised_total = answer["raise"]

        self.LPFB = self.raised_total - self.prev_VALID
        self.prev_VALID = self.raised_total
        self.prev_TOTAL = self.LPFB + self.prev_VALID

        action_list = self.players[current_player]["actions"][street_name]["action_list"]
        betting_size = self.players[current_player]["actions"][street_name]["betting_size"]

        # 현재 액션이 첫번째 액션이 아닌 경우
        if action_list:
            last_action = action_list[-1]
            # 프리플롭, 플롭, 턴, 리버에서  벳 or 레이즈 or 콜을 앞서 했었고 
            # 이후 올인이나 레이즈가 일어나서 다시 자기 차례에 레이즈를 한 경우
            if last_action != 'check':
                raise_amount = self.raised_total - betting_size[last_action]
            # 플롭, 턴, 리버에서 자신이 체크 레이즈를 하는 경우
            else:
                raise_amount = self.raised_total
        # 현재 액션이 첫번째 액션인 경우
        else:
            last_action = "raise"
            raise_amount = self.raised_total

        self.players[current_player]["stk_size"] -= raise_amount
        self.main_pot += raise_amount

        action_list.append("raise")
        betting_size["raise"].append(self.raised_total)

        self.pot_change.append(self.raised_total)  # 팟 변화량 업데이트
        self.attack_flag = True
        self.raise_counter += 1

        # 액션큐 처리
        if self.actioned_queue:
            self.start_order.extend(self.actioned_queue)
            self.actioned_queue.clear()

        self.actioned_queue.append(self.action_queue.popleft())

        '''
        모든 클라이언트들에게 다음을 요청
        레이즈한 클라이언트의 스택 사이즈를 raised_total 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 raised_total을 더한 결과로 렌더링
        '''
    
    def _all_in(self, street_name, current_player, answer):

        if current_player in self.check_users:
            self.check_users.remove(current_player)

        '''
        모든 클라이언트들에게 다음을 요청
        올인한 클라이언트에게 올인 버튼 렌더링(지속형 이벤트)
        '''
        # all_in_amount : 클라이언트에게서 전달받은 올인액수 (total을 의미)
        self.all_in_amount = answer['all-in']

        def _update_values(amount):
            self.LPFB = amount - self.prev_VALID
            self.prev_VALID = amount
            self.prev_TOTAL = self.prev_VALID + self.LPFB

        if street_name == 'pre_flop':
            if self.prev_TOTAL <= self.all_in_amount:
                _update_values(self.all_in_amount)
            elif self.prev_VALID <= self.all_in_amount < self.prev_TOTAL:
                self.prev_VALID = self.all_in_amount
                self.prev_TOTAL = self.prev_VALID + self.LPFB
            elif self.all_in_amount < self.prev_VALID:
                self.reorder_flag = False
        else:
             # 해당 올인이 open-bet인 경우
            if not self.attack_flag: 
                if self.prev_VALID <= self.all_in_amount:
                    self.LPFB = self.all_in_amount
                    self.prev_VALID = self.all_in_amount
                    self.prev_TOTAL = self.prev_VALID + self.LPFB
            # 해당 올인이 open-bet이 아닌 경우
            else:   
                if self.prev_TOTAL <= self.all_in_amount:
                    _update_values(self.all_in_amount)
                elif self.prev_VALID <= self.all_in_amount < self.prev_TOTAL:
                    self.prev_VALID = self.all_in_amount
                    self.prev_TOTAL = self.prev_VALID + self.LPFB

        action_list = self.players[current_player]["actions"][street_name]["action_list"]
        betting_size = self.players[current_player]["actions"][street_name]["betting_size"]

        # 현재 올인 액션이 첫번째 액션이 아니고, 마지막으로 한 액션이 check가 아닌 경우
        if action_list and action_list[-1] != 'check':
            last_action = action_list[-1]
            self.players[current_player]["stk_size"] -= (self.prev_VALID - betting_size[last_action])
            self.main_pot += (self.all_in_amount - betting_size[last_action])
        # 현재 올인 액션이 첫번째 액션이거나 마지막으로 했던 액션이 check 였던 경우
        else:
            last_action = "all-in"
            self.players[current_player]["stk_size"] -= self.all_in_amount
            self.main_pot += self.all_in_amount

        action_list.append("all_in")
        betting_size["all-in"].append(self.all_in_amount)

        self.pot_change.append(self.all_in_amount)  # 팟 변화량 업데이트
        self.attack_flag = True

        # 액션큐 처리
        if self.reorder_flag and self.actioned_queue:
            self.start_order.extend(self.actioned_queue)
            self.actioned_queue.clear()
        elif not self.reorder_flag or not self.actioned_queue:
            self.reorder_flag = True

        self.all_in_users.append(self.action_queue.popleft())

        '''
        모든 클라이언트들에게 다음을 요청
        올인한 클라이언트의 스택 사이즈를 self.all_in_amount 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 self.all_in_amount을 더한 결과로 렌더링
        '''

        # 딥스택 유저 수 부족으로 인한 핸드 종료조건
        for position in self.start_order:
            if self.prev_VALID <= self.players[position]['stk_size']:
                self.deep_stack_user_counter += 1

        # 올인 유저 제외 남은 라이브 플레이어들 중 딥스택 유저가 한명 이하인 경우
        # 딥스택 유저 : 현재 올인에 콜할 수 있는 유저
        if self.deep_stack_user_counter < 2:
            self.short_stack_end_flag == True
        
        self.all_in_counter += 1
        # 사이드팟 생성
        self.side_pot = self._multi_pots(street_name)

        # 모든 유저가 올인한 경우로 인한 핸드 종료조건
        if len(self.all_in_users) == len(self.this_street_players_num) and len(self.actioned_queue) == 0:
            self.every_all_in_end_flag = True
    
    def _multi_pots(self, street_name):  # 사이드팟 생성함수

        all_user : list = self.actioned_queue + self.all_in_users + self.fold_users

        for all_in_position in self.all_in_users:
            all_in_size = self.players[all_in_position]["actions"][street_name]["betting_size"]["all-in"]
            stake = 0  # 개별 올인 유저의 해당 스트릿에서의 메인팟에 대한 지분

            for position in all_user:
                action_list = self.players[position]["actions"][street_name]["action_list"]
                if action_list and action_list[-1] != 'fold':
                    last_action = action_list[-1]
                    last_betting_size = self.players[position]["actions"][street_name]["betting_size"][last_action]
                    stake += min(last_betting_size, all_in_size)
                # 올인 유저가 없거나, 폴드한 경우 예외처리
                else:
                    pass

            self.main_pot_confirmed[all_in_position] = stake
            
            if self.all_in_counter >= 2:
                return True
            else: 
                return False
              
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
        self.prev_VALID = self.bet_amount
        self.prev_TOTAL = self.prev_VALID + self.LPFB

        # bet은 항상 첫번째 액션
        last_action = "bet"
        self.players[current_player]["stk_size"] -= self.bet_amount
        self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
        self.players[current_player]["actions"][street_name]["betting_size"]["bet"].append(self.bet_amount)

        self.main_pot += self.bet_amount # 메인팟 업데이트
        self.pot_change.append(self.bet_amount) # 팟 변화량 업데이트

        self.attack_flag = True 

        # 액션큐 처리. 올인/레이즈 동일
        if self.actioned_queue:
            self.start_order.extend(self.actioned_queue)
            self.actioned_queue.clear()

        self.actioned_queue.append(self.action_queue.popleft())

        '''
        모든 클라이언트들에게 다음을 요청
        베팅한 클라이언트의 스택 사이즈를 self.bet_amount 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 self.bet_amount을 더한 결과로 렌더링
        '''

    def _posting_blind(self):
        if self.stakes == "low":
            self.players["SB"]["stk_size"] -= self.SB
            self.players["BB"]["stk_size"] -= self.BB
            self.players["SB"]["actions"]["pre_flop"]["betting_size"]["bet"].append(self.SB)
            self.players["SB"]["actions"]["pre_flop"]["action_list"].append("bet")
            self.players["BB"]["actions"]["pre_flop"]["betting_size"]["bet"].append(self.BB)
            self.players["BB"]["actions"]["pre_flop"]["action_list"].append("bet")
            self.main_pot += (self.SB + self.BB)

    def _check_connection(self, on_user_list):
        connected_users = []
        if on_user_list:
            for on_user in on_user_list:
                connected_users.append(self.user2pos[on_user])
            for position in self.start_order:
                if position not in connected_users:
                    self.fold_users.append(self.start_order.popleft())   

    def _live_players_update(self, street_name):
        '''
        현재 접속중인 클라이언트 카운트
        '''
        if street_name == 'pre_flop':          
            self.this_street_players_num = rings - len(self.fold_users)
        else:
            self.this_street_players_num = len(self.survivors) - len(self.fold_users)

    def _reorder_start_member(self):
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

    def _face_up_community_cards(self, street_name : str): 
        self.log_hand_cards['burned'].append(self.stub.pop(0)) # 버닝
        if street_name == 'flop':
            for _ in range(3):
                self.log_hand_cards[street_name].append(self.stub.pop(0))
        else:
            self.log_hand_cards[street_name].append(self.stub.pop(0))

        return self.log_hand_cards[street_name]
    
    def _face_up_community_cards_for_showdown(self, street_name :str) -> list :

        if street_name == 'pre_flop':
            self._face_up_community_cards('flop')
            self._face_up_community_cards('turn')
            self._face_up_community_cards('river')
        elif street_name == 'flop':
            self._face_up_community_cards('turn')
            self._face_up_community_cards('river')
        elif street_name == 'turn':
            self._face_up_community_cards('river')

        self.log_hand_cards["table_cards"] = self.log_hand_cards["flop"] + self.log_hand_cards["turn"] + self.log_hand_cards["river"]
        community_cards: list = self.log_hand_cards["table_cards"]

        return community_cards
    
    def _face_up_user_hand(self):
        user_hand = dict()
        all_user = self.all_in_users + self.actioned_queue
        for position in all_user:
            starting_cards = self.players[position]['starting_cards']
            user_hand[position] = starting_cards
        return user_hand
            
    def _prep_preFlop(self, street_name, on_user_list):

        self._posting_blind()
        '''
        서버에 요청
        on_user_list 변수에 접속 중인 클라이언트의 유저 아이디 요청
        모든 클라이언트에게 스택사이즈 렌더링 요청
        '''
        self._check_connection(on_user_list)
        self._live_players_update(street_name)

        '''
        서버에 요청
        스타팅 카드 전송 후 렌더링
        start_order 에 있는 유저만 남기고 나머지 유저들 삭제 렌더링
        '''

        if self.start_order:
            self.action_queue.append(self.start_order.popleft())
        else:
            pass # 예외처리      

    def _prep_street(self, street_name, on_user_list):
        
        self._initialize_betting_state()
        self._initialize_action_state()
        self._initialize_condition()

        self._reorder_start_member()
        cards = self._face_up_community_cards()
        '''
        서버에 요청
        on_user_list 변수에 접속 중인 클라이언트의 유저 아이디 요청
        모든 클라이언트에게 cards 전달, 렌더링 요청
        '''
        self._check_connection(on_user_list)
        self._live_players_update(street_name)
        '''
        서버에 요청
        스타팅 카드 전송 후 렌더링
        start_order 에 있는 유저만 남기고 나머지 유저들 삭제 렌더링
        '''
        if self.start_order:
            self.action_queue.append(self.start_order.popleft())
        else:
            pass # 예외처리        

    def _possible_actions(self, street_name, current_player):

        player_stack = self.players[current_player]['stk_size']

        if street_name == 'pre_flop':
            # 프리플롭에서 첫 바퀴를 돌고 BB 차례가 되었을 때, 모두 콜 or 폴드만 한 경우 BB option 및 check 구현
            if self.raised_total == 0 and len(self.all_in_users) == 0:
                if self.prev_TOTAL <= player_stack:
                    possible_actions = ["check", "raise", "fold", "all-in"]
                elif self.prev_VALID <= player_stack < self.prev_TOTAL:
                    possible_actions = ["check", "fold", "all-in"] # short-all-in
                elif player_stack < self.prev_VALID:
                    possible_actions = ["fold", "all-in"] # short-all-in
            else:
                if self.prev_TOTAL <= player_stack:
                    possible_actions = ["call", "raise", "fold", "all-in"]
                elif self.prev_VALID <= player_stack < self.prev_TOTAL:
                    possible_actions = ["call", "fold", "all-in"] # short-all-in
                elif player_stack < self.prev_VALID:
                    possible_actions = ["fold", "all-in"] # short-all-in
        else:
            if not self.attack_flag:  # not attacked
                if self.prev_VALID <= player_stack:
                    possible_actions = ["bet", "check", "fold", "all-in"]
                elif player_stack < self.prev_VALID:
                    possible_actions = ["check", "fold", "all-in"] # short-all-in
            elif self.attack_flag:  # attacked
                if player_stack >= self.prev_TOTAL:
                    if self.raise_counter <= 5:
                        possible_actions = ["call", "raise", "fold", "all-in"]
                    else:
                        possible_actions = ["call", "fold", "all-in"]
                elif self.prev_VALID <= player_stack < self.prev_TOTAL:
                    possible_actions = ["call", "fold", "all-in"] # short-all-in
                elif player_stack < self.prev_VALID:
                    possible_actions = ["fold", "all-in"] # short-all-in

        return possible_actions

    def _play_street(self, street_name):
        while self.action_queue:

            current_player = self.action_queue[0]
                                                    
            possible_actions : list = self._possible_actions(street_name, current_player)
            
            '''
            서버에 요청
            current_player에 해당하는 클라이언트에게 possible_actions 전달, 응답 요청
            '''

            # answer : 클라이언트의 응답이 담기는 변수       
            answer : dict = input() # 레이즈는 {"raise" : raised_total} 올인은 {"all-in" : all_in_amount} 벳은 {"bet" : bet_amount}
            self.log_hand_actions[street_name].append((current_player, answer)) # 유저 액션 기록    
            
            # 클라이언트에게 전달 받은 응답이 call 이면
            if answer == "call":
                self._call(street_name, current_player)

            # 클라이언트에게 전달 받은 응답이 fold 면 
            elif answer == "fold":
                self._fold(street_name)

            # 클라이언트로부터 전달 받은 응답이 answer = {"raise" : raised_total} 이면
            elif next(iter(answer)) == "raise":
                self._raise(street_name, current_player, answer)

            # 클라이언트로부터 전달 받은 응답이 answer = {"all-in" : all_in_amount} 이면
            elif next(iter(answer)) == "all-in":
                self._all_in(street_name, current_player, answer)

            # 클라이언트에게 전달 받은 응답이 check 면      
            elif answer == "check":  # BB 만 가능
                self._check(current_player)

            # 클라이언트로부터 전달 받은 응답이 answer = {"bet" : bet_amount} 이면
            elif next(iter(answer)) == "bet": # 플롭부터 가능
                self._bet(street_name, current_player, answer)

            # 클라이언트에게 전달받은 응답 처리 끝나면 다음 차례 유저 액션큐 등록
            if self.start_order:
                self.action_queue.append(self.start_order.popleft())
            else:
                pass # 예외처리  

    def _end_conditions(self, street_name):
        if street_name == "pre_flop":
            start_member_num = rings
        else:
            start_member_num = len(self.survivors)
        start_member_num - len(self.fold_users) == len(self.this_street_players_num)

        # 핸드 종료조건 _all_in 함수
        # 모든 스트릿에서 최초 올인 이후 딥스택 유저가 1명 이하인 경우 (이전 스트릿에서 올인 있었든 없었든) 
        if self.short_stack_end_flag:
            self._live_players_update(street_name)
            
            if len(self.all_in_users) == 1:
                # 올인 유저가 한명있고 모두 폴드한 경우
                if len(self.fold_users) == self.this_street_players_num - 1:
                    self.winner_confirmed = True
                    self.user_card_open_first = True
                    winner = self._showdown(street_name) # 1 모든 스타팅 카드 오픈 > 커뮤니티 카드 오픈 > 올인 유저 바로 승자처리

                # 올인 유저가 한명있고 콜 또는 폴드한 사람 있는 경우
                elif len(self.all_in_users) == 1 and len(self.fold_users) + len(self.actioned_queue) == self.this_street_players_num - 1:
                    self.user_card_open_first = True
                    winner = self._showdown(street_name) # 2 모든 스타팅 카드 오픈 > 커뮤니티 카드 오픈 > 랭킹비교 알고리즘으로 승자 처리

        # 핸드 종료조건 _all_in 함수
        # 모든 스트릿에서 모든 유저가 올인한 경우 (이전 스트릿에서 올인 있었든 없었든) 
        if self.every_all_in_end_flag:
            self.user_card_open_first = True
            winner = self._showdown(street_name) # 3 모든 스타팅 카드 오픈 > 커뮤니티 카드 오픈 > 랭킹비교 알고리즘으로 승자 처리

        # 핸드 종료조건 (현재 스트릿에서 올인이 발생하지 않은 경우) (이전 스트릿에서 올인 있었든 없었든) 
        # 모든 스트릿에서 베팅액션에 대해 모든 유저가 폴드한 경우
        if len(self.check_users) == 0 and len(self.actioned_queue) == 1 and len(self.fold_users) == start_member_num - 1:
            self.winner_confirmed = True
            self.table_card_open_first = True
            winner = self._showdown(street_name) # 4 커뮤니티 카드 오픈 > 베팅 유저 바로 승자처리

        # 핸드 종료조건 (현재 스트릿에서 올인이 발생하지 않은 경우) (이전 스트릿에서 올인 있었든 없었든) 
        if street_name == 'river':
            # 모두 check 한 경우 
            if len(self.check_users) == len(self.this_street_players_num):
                self.river_all_check = True
                winner : list = self._showdown(street_name) # 5 커뮤니티 카드 오픈 > 리버에서 액션했던 순서대로 유저 카드오픈
            # 마지막 베팅 액션에 대해 콜한 사람이 있을 경우  
            elif len(self.check_users) == 0 and len(self.actioned_queue) >= 2 and self.this_street_players_num > 1:
                self.river_bet_exists = True
                winner = self._showdown(street_name) # 6 커뮤니티 카드 오픈 > 리버에서 마지막 액션을 한 사람부터 베팅순서대로 카드 오픈
        
        if len(self.fold_users) == start_member_num:
            pass # 모든 클라이언트 폴드 또는 접속 종료 상태. 게임 기록 제거

    def _compare_rank(self, user_cards : dict, community_cards : list) -> dict:

        for position in user_cards:
            pocket_cards = user_cards[position]
            best_hands = self._make_best_hands(pocket_cards, community_cards)
            self.log_best_hands[position] = best_hands

        best_rank = 0
        nuts_positions = []
        for position, best_hands_dict in self.log_best_hands.items():
            for rank, hand in best_hands_dict.items():
                current_rank = self.hand_power.get(rank, 0)
                if current_rank > best_rank:
                    best_rank = current_rank
                    nuts_positions = [position]
                elif current_rank == best_rank:
                    nuts_positions.append(position)

        # 타이가 발생하는 경우 카드 랭크와 키커로 넛츠 판별. 무승부시 복수 넛츠 허용
        if len(nuts_positions) > 1:
            final_nuts_positions = self._resolve_ties(nuts_positions)
            nuts_positions = final_nuts_positions

        for position in nuts_positions:
            self.log_nuts[position] = self.log_best_hands[position]

        # 유저의 베스트 핸드를 랭크 순위대로 정렬하여 users_ranking 리스트 작성
        self._users_ranking()

        return self.log_nuts

    def _showdown(self, street_name):
        
        community_cards : list = self._face_up_community_cards_for_showdown()
        user_cards : dict = self._face_up_user_hand()

        if self.winner_confirmed:
             # 1 모든 스타팅 카드 오픈 > 커뮤니티 카드 오픈 > 올인 유저 바로 승자처리, 팟 어워드
            if self.user_card_open_first:

                if street_name == 'pre_flop':
                    user_cards
                    self.log_hand_cards["burned"][0]
                    self.log_hand_cards["flop"]
                    self.log_hand_cards["burned"][1]
                    self.log_hand_cards["turn"]
                    self.log_hand_cards["burned"][2]
                    self.log_hand_cards["river"]
                    '''
                    서버에 요청
                    모든 클라이언트에게 유저카드 먼저 오픈 후 
                    커뮤니티 카드 버닝, 플롭, 버닝, 턴, 버닝, 리버 순서로 렌더링 요청
                    '''
                elif street_name == 'flop':
                    user_cards
                    self.log_hand_cards["burned"][1]
                    self.log_hand_cards["turn"]
                    self.log_hand_cards["burned"][2]
                    self.log_hand_cards["river"]                    
                    '''
                    서버에 요청
                    모든 클라이언트에게 유저카드 먼저 오픈 후 
                    커뮤니티 카드 버닝, 턴, 버닝, 리버 순서로 렌더링 요청
                    '''                   
                elif street_name == 'turn':
                    user_cards
                    self.log_hand_cards["burned"][2]
                    self.log_hand_cards["river"]     
                    '''
                    서버에 요청
                    모든 클라이언트에게 유저카드 먼저 오픈 후 
                    커뮤니티 카드 버닝, 리버 순서로 렌더링 요청
                    '''                    
                elif street_name == 'river':
                    user_cards
                    '''
                    서버에 요청
                    모든 클라이언트에게 유저카드 오픈 렌더링
                    '''          
                if self.side_pot:
                    # 랭크 비교 알고리즘 실행
                    winner = self._compare_rank(user_cards, community_cards)
                    winner = self._pot_award(self.main_pot_confirmed, winner)
                    return winner
                # 1의 경우 사이드 팟이 없으면 승자는 마지막 베팅 유저로 바로 확정
                elif not self.side_pot: 
                    winner = self._pot_award(pot = self.main_pot, winner = self.all_in_users)
                    return winner
                
            # 4 커뮤니티 카드 오픈 > 베팅 유저 바로 승자처리, 팟 어워드
            elif self.table_card_open_first:
                if street_name == 'pre_flop':
                    self.log_hand_cards["burned"][0]
                    self.log_hand_cards["flop"]
                    self.log_hand_cards["burned"][1]
                    self.log_hand_cards["turn"]
                    self.log_hand_cards["burned"][2]
                    self.log_hand_cards["river"]
                    
                    if self.side_pot == True:
                        user_cards
                        card_open_order = self.actioned_queue
                        '''
                        서버에 요청
                        모든 클라이언트에게 커뮤니티 카드 버닝, 플롭, 버닝, 턴, 버닝, 리버 순서로 오픈후
                        모든 유저카드 오픈 렌더링 요청 (이전 스트릿에서 올인이 있었으므로. 오픈 순서는 마지막 스트릿의 베팅 유저부터)
                        '''
                        pass
                    else:
                        '''
                        서버에 요청
                        모든 클라이언트에게 커뮤니티 카드 버닝, 플롭, 버닝, 턴, 버닝, 리버 순서로 오픈 렌더링 요청
                        유저 카드는 오픈하지 않음 (이전 스트릿에서 올인이 없었으므로)
                        '''
                        pass
                elif street_name == 'flop':
                    self.log_hand_cards["burned"][1]
                    self.log_hand_cards["turn"]
                    self.log_hand_cards["burned"][2]
                    self.log_hand_cards["river"]
                                       
                    if self.side_pot == True:
                        user_cards
                        '''
                        서버에 요청
                        모든 클라이언트에게 커뮤니티 카드 버닝, 턴, 버닝, 리버 순서로 오픈후
                        모든 유저카드 오픈 렌더링 요청 (이전 스트릿에서 올인이 있었으므로. 오픈 순서는 마지막 스트릿의 베팅 유저부터)
                        '''
                        pass
                    else:
                        '''
                        서버에 요청
                        모든 클라이언트에게 커뮤니티 카드 버닝, 턴, 버닝, 리버 순서로 오픈 렌더링 요청
                        유저 카드는 오픈하지 않음 (이전 스트릿에서 올인이 없었으므로)
                        '''
                        pass               
                elif street_name == 'turn':
                    user_cards
                    self.log_hand_cards["burned"][2]
                    self.log_hand_cards["river"]     
                    if self.side_pot == True:
                        user_cards
                        '''
                        서버에 요청
                        모든 클라이언트에게 커뮤니티 카드 버닝, 리버 순서로 오픈후
                        모든 유저카드 오픈 렌더링 요청 (이전 스트릿에서 올인이 있었으므로. 오픈 순서는 마지막 스트릿의 베팅 유저부터)
                        '''
                        pass
                    else:
                        '''
                        서버에 요청
                        모든 클라이언트에게 커뮤니티 카드 버닝, 리버 순서로 오픈 렌더링 요청
                        유저 카드는 오픈하지 않음 (이전 스트릿에서 올인이 없었으므로)
                        '''
                        pass              
                elif street_name == 'river':
                    user_cards
                    if self.side_pot == True:
                        user_cards
                        '''
                        서버에 요청
                        모든 유저카드 오픈 렌더링 요청 (이전 스트릿에서 올인이 있었으므로. 오픈 순서는 마지막 스트릿의 베팅 유저부터)
                        '''
                        pass
                    else:
                        '''
                        유저 카드는 오픈하지 않음 (이전 스트릿에서 올인이 없었으므로)
                        '''
                        pass
                if self.side_pot:
                    # 랭크 비교 알고리즘 실행
                    winner = self._compare_rank(user_cards, community_cards)
                    winner = self._pot_award(self.main_pot_confirmed, winner)
                    return winner
                # 4의 경우 사이드 팟이 없으면 승자는 마지막 베팅 유저로 바로 확정
                elif not self.side_pot: 
                    winner = self._pot_award(pot = self.main_pot, winner = self.actioned_queue)
                    return winner
        else: 
            # 2, 3 모든 스타팅 카드 오픈 > 커뮤니티 카드 오픈 > 랭킹비교 알고리즘으로 승자 처리, 팟 어워드
            if self.user_card_open_first:  
                if street_name == 'pre_flop':
                    user_cards
                    self.log_hand_cards["burned"][0]
                    self.log_hand_cards["flop"]
                    self.log_hand_cards["burned"][1]
                    self.log_hand_cards["turn"]
                    self.log_hand_cards["burned"][2]
                    self.log_hand_cards["river"]
                    '''
                    서버에 요청
                    모든 클라이언트에게 유저카드 먼저 오픈 후 
                    커뮤니티 카드 버닝, 플롭, 버닝, 턴, 버닝, 리버 순서로 렌더링 요청
                    '''
                elif street_name == 'flop':
                    user_cards
                    self.log_hand_cards["burned"][1]
                    self.log_hand_cards["turn"]
                    self.log_hand_cards["burned"][2]
                    self.log_hand_cards["river"]                    
                    '''
                    서버에 요청
                    모든 클라이언트에게 유저카드 먼저 오픈 후 
                    커뮤니티 카드 버닝, 턴, 버닝, 리버 순서로 렌더링 요청
                    '''          
                elif street_name == 'turn':
                    user_cards
                    self.log_hand_cards["burned"][2]
                    self.log_hand_cards["river"]     
                    '''
                    서버에 요청
                    모든 클라이언트에게 유저카드 먼저 오픈 후 
                    커뮤니티 카드 버닝, 리버 순서로 렌더링 요청
                    '''           
                elif street_name == 'river':
                    user_cards
                    '''
                    서버에 요청
                    모든 클라이언트에게 유저카드 오픈 렌더링
                    '''                  
                # 랭크 비교 알고리즘 실행
                # 2, 3 의 경우 사이드팟이 있건 없건 스트릿 종료후 라이브 플레이어가 둘 이상이므로 랭킹 비교 실행 필요
                winner = self._compare_rank(user_cards, community_cards)
                if self.side_pot:
                    winner = self._pot_award(self.main_pot_confirmed, winner= winner)
                    return winner
                elif not self.side_pot: 
                    winner = self._pot_award(pot = self.main_pot, winner = winner)
                    return winner
            elif self.table_card_open_first:
                # 5 커뮤니티 카드 오픈 > 리버에서 액션했던 순서대로 유저 카드오픈 > 랭킹비교 알고리즘으로 승자 처리, 팟 어워드
                if self.river_all_check: 
                    user_cards
                    card_open_order = self.check_users                   
                    '''
                    서버에 요청 self.actioned_queue
                    리버에서 먼저 체크 액션을 한 사람부터 카드 오픈
                    '''
                    # 랭크 비교 알고리즘 실행
                    winner = self._compare_rank(user_cards, community_cards)      

                    if self.side_pot:
                        winner = self._pot_award(pot = self.main_pot_confirmed, winner = winner)
                        return winner
                    elif not self.side_pot: 
                        winner = self._pot_award(pot = self.main_pot, winner = winner)
                        return winner
                # 6 커뮤니티 카드 오픈 > 리버에서 마지막 액션을 한 사람부터 베팅순서대로 카드 오픈 > 랭킹비교 알고리즘으로 승자 처리, 팟 어워드        
                elif self.river_bet_exists:
                    user_cards
                    card_open_order = self.actioned_queue                    
                    '''
                    서버에 요청 
                    모든 클라이언트에게 커뮤니티 카드 먼저 오픈 후, 리버에서 마지막 베팅 액션을 한 사람부터 카드 오픈
                    '''
                    # 랭크 비교 알고리즘 실행
                    winner = self._compare_rank(user_cards, community_cards)      

                    if self.side_pot:
                        winner = self._pot_award(pot = self.main_pot_confirmed, winner = winner)
                        return winner
                    elif not self.side_pot: 
                        winner = self._pot_award(pot = self.main_pot, winner = winner)
                        return winner
    
    def _pot_award(self, pot, winner):

        if winner > 1:
            '''
            승자가 현재 스트릿에서 이긴 유저인 경우

            승자가 이전 스트릿에서 올인 한 유저인 경우
            '''
            for position in winner:
                self.players[position]['stk_size'] += self.main_pot_confirmed[position]
        else:
            '''
            승자가 현재 스트릿에서 이긴 유저인 경우
                메인팟을 승자가 모두 가져간다.
                self.players[winner[0]]['stk_size'] += pot

            승자가 이전 스트릿에서 올인 한 유저인 경우
                해당 스트릿에서 만들어진 메인팟만 가져가고
                self.players[winner[0]]['stk_size'] += self.main_pot_confirmed[winner[0]]
                현재 스트릿에서 쇼다운 2위 랭킹부터  
            '''
            
        '''
        서버에 요청
        승자 연출 렌더링 winner 딕셔너리의 키가 winner의 포지션
        모든 클라이언트에게 승자의 업데이트 된 스택사이즈 렌더링
        '''


    def _finishing_street(self, street_name):
        self.log_hand_main_pots[street_name] = self.main_pot
        self._live_players_update(street_name)
        self.survivors.clear()
        self.survivors.extend(self.actioned_queue)
        

    def preFlop(self):
        
        street_name = "pre_flop"
        self._prep_preFlop(street_name)
        self._play_street(street_name)
        winner = self._end_conditions(street_name)
        self._finishing_street(street_name)
    
    def flop(self):
    
        street_name = "flop"
        self._prep_street(street_name)
        self._play_street(street_name)
        winner = self._end_conditions(street_name)
        self._finishing_street(street_name)
    
    def trun(self):

        street_name = "turn"
        self._prep_street(street_name)
        self._play_street(street_name)
        winner = self._end_conditions(street_name)
        self._finishing_street(street_name)
    
    def river(self):

        street_name = "river"
        self._prep_street(street_name)
        self._play_street(street_name)
        winner = self._end_conditions(street_name)
        self._finishing_street(street_name)


if __name__ == '__main__':

    dealer = Dealer(user_id_list, stk_size, rings, stakes)
    # 스트릿 루프 진입 전 클라이언트들에게 모두 제자리에 있는지 응답 요청
    dealer._posting_blind() # 호출후 SB와 BB 클라이언트의 스택사이즈를 블라인드 차감된 양으로 렌더링 요청, 메인팟 업데이트 렌더링 요청
    print(dealer.players)
    print(dealer.players["BB"]["actions"]["pre_flop"]["betting_size"])
    print(dealer.players["BB"]["actions"]["pre_flop"]["action_list"])
    print(dealer.players["BB"]['stk_size'])
