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
        self.side_pot = False
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
        self.every_all_in_end_flag = False

        self.winner_confirmed = False
        self.user_card_open_first = False
        self.table_card_open_first = False
        self.river_bet_exists = False
        self.river_all_check = False

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
    
    def _live_players_update(self, street_name):
        '''
        현재 접속중인 클라이언트 카운트
        '''
        if street_name == 'pre_flop':          
            self.this_street_players_num = rings - len(self.fold_users)
        else:
            self.this_street_players_num = len(self.survivors) - len(self.fold_users)

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

        def update_values(amount):
            self.LPFB = amount - self.prev_VALID
            self.VALID = amount
            self.prev_TOTAL = self.VALID + self.LPFB

        if street_name == 'pre_flop':
            if self.prev_TOTAL <= self.all_in_amount:
                update_values(self.all_in_amount)
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
                    update_values(self.all_in_amount)
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
        
        # 사이드팟 생성
        self.side_pot = self._multi_pots(street_name)

        # 모든 유저가 올인한 경우로 인한 핸드 종료조건
        if len(self.all_in_users) == len(self.this_street_players_num) and len(self.actioned_queue) == 0:
            self.every_all_in_end_flag = True
            
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

        return True

    def _end_condtion(self, street_name):
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
                    winner : list = self._showdown() # 1 모든 스타팅 카드 오픈 > 커뮤니티 카드 오픈 > 올인 유저 바로 승자처리

                # 올인 유저가 한명있고 콜 또는 폴드한 사람 있는 경우
                elif len(self.all_in_users) == 1 and len(self.fold_users) + len(self.actioned_queue) == self.this_street_players_num - 1:
                    self.user_card_open_first = True
                    winner : list = self._showdown() # 2 모든 스타팅 카드 오픈 > 커뮤니티 카드 오픈 > 랭킹비교 알고리즘으로 승자 처리

        # 핸드 종료조건 _all_in 함수
        # 모든 스트릿에서 모든 유저가 올인한 경우 (이전 스트릿에서 올인 있었든 없었든) 
        if self.every_all_in_end_flag:
            self.user_card_open_first = True
            winner : list = self._showdown() # 3 모든 스타팅 카드 오픈 > 커뮤니티 카드 오픈 > 랭킹비교 알고리즘으로 승자 처리

        # 핸드 종료조건 (현재 스트릿에서 올인이 발생하지 않은 경우) (이전 스트릿에서 올인 있었든 없었든) 
        # 베팅액션에 대해 모든 유저가 폴드한 경우
        if len(self.check_users) == 0 and len(self.actioned_queue) == 1 and len(self.fold_users) == start_member_num - 1:
            self.winner_confirmed = True
            self.table_card_open_first = True
            winner : list = self._showdown() # 4 커뮤니티 카드 오픈 > 베팅 유저 바로 승자처리

        # 핸드 종료조건 (현재 스트릿에서 올인이 발생하지 않은 경우) (이전 스트릿에서 올인 있었든 없었든) 
        if street_name == 'river':
            # 모두 check 한 경우 
            if len(self.check_users) == len(self.this_street_players_num):
                self.river_all_check = True
                winner : list = self._showdown() # 5 커뮤니티 카드 오픈 > 리버에서 액션했던 순서대로 유저 카드오픈
            # 마지막 베팅 액션에 대해 콜한 사람이 있을 경우  
            elif len(self.check_users) == 0 and len(self.actioned_queue) >= 2 and self.this_street_players_num > 1:
                self.river_bet_exists = True
                winner : list = self._showdown() # 6 커뮤니티 카드 오픈 > 리버에서 마지막 액션을 한 사람부터 베팅순서대로 카드 오픈
        
        if len(self.fold_users) == start_member_num:
            pass # 모든 클라이언트 폴드 또는 접속 종료 상태. 게임 기록 제거
    
    def _showdown(self):
        
        all_user = self.all_in_users + self.actioned_queue
        for position in all_user:
            self.players[position]['starting_cards']
        
        if self.winner_confirmed:
             # 1 모든 스타팅 카드 오픈 > 커뮤니티 카드 오픈 > 올인 유저 바로 승자처리, 팟 어워드
            if self.user_card_open_first:
                if self.side_pot:
                    
                    return self.main_pot_confirmed
                elif not self.side_pot: 
                    
                    return self.main_pot
            # 4 커뮤니티 카드 오픈 > 베팅 유저 바로 승자처리, 팟 어워드
            elif self.table_card_open_first:
                if self.side_pot:
                    
                    return self.main_pot_confirmed
                elif not self.side_pot: 
                    
                    return self.main_pot
        else: 
            # 2, 3 모든 스타팅 카드 오픈 > 커뮤니티 카드 오픈 > 랭킹비교 알고리즘으로 승자 처리, 팟 어워드
            if self.user_card_open_first:  
                if self.side_pot:
                    
                    return self.main_pot_confirmed
                elif not self.side_pot: 
                    
                    return self.main_pot
            elif self.table_card_open_first:
                # 5 커뮤니티 카드 오픈 > 리버에서 액션했던 순서대로 유저 카드오픈 > 랭킹비교 알고리즘으로 승자 처리, 팟 어워드
                if self.river_all_check:
                    if self.side_pot:
                        return self.main_pot_confirmed
                    elif not self.side_pot: 
                        return self.main_pot
                # 6 커뮤니티 카드 오픈 > 리버에서 마지막 액션을 한 사람부터 베팅순서대로 카드 오픈 > 랭킹비교 알고리즘으로 승자 처리, 팟 어워드        
                elif self.river_bet_exists:
                    if self.side_pot:
                        return self.main_pot_confirmed
                    elif not self.side_pot: 
                        return self.main_pot    
    


    def preFlop(self):
        
        '''
        프리플롭 메서드 호출시 
        최초로 액션할 유저가 응답 가능한지 확인하고 
        액션큐 등록
        불가능하면 폴드 처리하고 다음 유저에게 물어보는 루프로 바꿀 것
        '''
        if self.start_order:
            self.action_queue.append(self.start_order.popleft())
        else:
            pass # 예외처리
                
        street_name = "pre_flop"

        ######################################################################################################
        ######################################################################################################
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

            # 클라이언트에게 전달받은 응답 처리 끝나면 다음 차례 유저 액션큐 등록
            if self.start_order:
                self.action_queue.append(self.start_order.popleft())
            else:
                pass # 예외처리  

        ######################################################################################################
        ######################################################################################################            
        self._live_players_update(street_name)

        winner = self._end_conditions(street_name)



        # 이하 다음 스트릿으로 넘어갈 준비





        # 다음 스트릿으로 갈 플레이어 survivors 리스트 리턴
        self.log_hand_main_pots[street_name] = self.main_pot
        self.survivors.extend(self.actioned_queue)
        
        self._live_players_update(street_name)  
        self.this_street_players_num = len(self.survivors)

        return
    
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

            self.action_queue.append(self.start_order.popleft())

        self.log_hand_main_pots[street_name] = self.main_pot
        # 다음 스트릿으로 갈 플레이어 survivors 리스트 리턴
        
        self.survivors.extend(self.actioned_queue)

        return
    
    def trun(self):
        pass

    def river(self):
        pass





if __name__ == '__main__':

    dealer = Dealer(user_id_list, stk_size, rings, stakes)
    # 스트릿 루프 진입 전 클라이언트들에게 모두 제자리에 있는지 응답 요청
    dealer._posting_blind() # 호출후 SB와 BB 클라이언트의 스택사이즈를 블라인드 차감된 양으로 렌더링 요청, 메인팟 업데이트 렌더링 요청
    print(dealer.players)
    print(dealer.players["BB"]["actions"]["pre_flop"]["betting_size"])
    print(dealer.players["BB"]["actions"]["pre_flop"]["action_list"])
    print(dealer.players["BB"]['stk_size'])
