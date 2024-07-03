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

        self.all_in_users_total = OrderedDict()
        self.fold_users = []

        self.main_pot_cumulative = 0
        self.pot_change = [self.main_pot_cumulative]
        self.side_pot = False # 모든 스트릿 포함 최초 올인 발생시 True
        self.main_pot_confirmed = OrderedDict([("pre_flop", {}), ("flop", {}), ("turn", {}), ("river", {})])
        
        self.street_name = ["pre_flop", "flop", "turn", "river"]

        self._initialize_betting_state()
        self._initialize_action_state()
        self._initialize_conditions()      

    def _initialize_betting_state(self):
        self.raised_total = 0 # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
        self.all_in_amount = 0   # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
        self.bet_amount = 0 # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신

        self.LPFB = self.BB # the largest prior full bet = the last legal increment = minimum raise
        self.prev_VALID = self.BB  # 콜시 유저의 스택에 남아 있어야 하는 최소 스택 사이즈의 기준
        self.prev_TOTAL = self.prev_VALID + self.LPFB # 레이즈시 유저의 스택에 남아있어야 하는 최소 스택 사이즈의 기준

        self.street_pot = 0 # 해당 스트릿에서만 발생한 베팅 총액

    def _initialize_action_state(self):
        self.action_queue = deque([])
        self.actioned_queue = deque([])

        self.all_in_users = []
        
        self.check_users = []

        self.attack_flag = False # only only and just once bet, raise, all-in is True  # 플롭부터는 False로 초기화
        self.raise_counter = 0 # 5가 되면 Possible action 에서 raise 삭제. 구현 필요
        self.reorder_flag = True # 현재 액션 유저를 기준으로 actioned_queue에 있는 유저들을 start_order 리스트 뒤에 붙이는 reorder를 금지시키기 위한 플래그

    def _initialize_conditions(self):
        self.deep_stack_user_counter = 0
        self.short_stack_end_flag = False # 올인 발생시 딥스택 유저 수 부족으로 바로 핸드 종료시키는 조건

        self.winner_confirmed = False
        self.user_card_open_first = False
        self.table_card_open_first = False
        self.table_card_open_only = False

        self.river_all_check = False
        self.river_bet_exists = False

        self.survivors = [] # 다음 스트릿으로 갈 생존자 리스트
##########################################################################
#                              ACTION
##########################################################################
    def _possible_actions(self, street_name, current_player):

        player_stack = self.players[current_player]['stk_size']

        if street_name == 'pre_flop':
            # 프리플롭에서 첫 바퀴를 돌고 BB 차례가 되었을 때, 모두 콜 or 폴드만 한 경우 BB option 및 check 구현
            if self.raised_total == 0 and len(self.all_in_users) == 0:
                if self.prev_TOTAL <= player_stack:
                    possible_actions = ["check", "raise", "fold", "all-in"]
                elif self.prev_VALID <= player_stack < self.prev_TOTAL:
                    possible_actions = ["check", "fold", "all-in"] # short-all-in : after first all-in, under call
                elif player_stack < self.prev_VALID:
                    possible_actions = ["fold", "all-in"] # short-all-in : after first all-in, under call
            else:
                if self.prev_TOTAL <= player_stack:
                    possible_actions = ["call", "raise", "fold", "all-in"]
                elif self.prev_VALID <= player_stack < self.prev_TOTAL:
                    possible_actions = ["call", "fold", "all-in"] # short-all-in : after first all-in, under call
                elif player_stack < self.prev_VALID:
                    possible_actions = ["fold", "all-in"] # short-all-in
        else:
            if not self.attack_flag:  # not attacked
                if self.prev_VALID <= player_stack:
                    possible_actions = ["bet", "check", "fold", "all-in"]
                elif player_stack < self.prev_VALID:
                    possible_actions = ["check", "fold", "all-in"] # short-all-in : under bet
            elif self.attack_flag:  # attacked
                if self.prev_TOTAL <= player_stack:
                    if self.raise_counter <= 5:
                        possible_actions = ["call", "raise", "fold", "all-in"]
                    else:
                        possible_actions = ["call", "fold", "all-in"]
                elif self.prev_VALID <= player_stack < self.prev_TOTAL:
                    possible_actions = ["call", "fold", "all-in"] # short-all-in : after first all-in, under call
                elif player_stack < self.prev_VALID:
                    possible_actions = ["fold", "all-in"] # short-all-in : after first all-in, under call

        return possible_actions
       
    def _bet(self, street_name, current_player, answer):

        if current_player in self.check_users:
            self.check_users.remove(current_player)

        action_list = self.players[current_player]["actions"][street_name]["action_list"]
        betting_size = self.players[current_player]["actions"][street_name]["betting_size"]    

        # bet_amount : 클라이언트에게서 전달받은 베팅액수
        self.bet_amount = answer['bet']

        self.LPFB = self.bet_amount
        self.prev_VALID = self.bet_amount
        self.prev_TOTAL = self.prev_VALID + self.LPFB

        # bet은 항상 첫번째 액션
        self.players[current_player]["stk_size"] -= self.bet_amount # 스택사이즈 업데이트
        self.main_pot_cumulative += self.bet_amount # 메인팟 업데이트
        
        self.pot_change.append(self.prev_VALID) # 팟 변화량 업데이트
        self.street_pot += self.prev_VALID

        # 로그 업데이트
        betting_size["bet"].append(self.prev_VALID)
        action_list.append("bet")

        self.attack_flag = True 

        # 액션큐 처리. 벳의 경우 자기 앞에 액션은 체크를 한 사람 밖에 없다.
        if self.actioned_queue:
            self.start_order.extend(self.actioned_queue)
            self.actioned_queue.clear()

        self.actioned_queue.append(self.action_queue.popleft())

        '''
        모든 클라이언트들에게 다음을 요청
        베팅한 클라이언트의 스택 사이즈를 self.bet_amount 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 self.bet_amount을 더한 결과로 렌더링
        '''
    
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

        # 현재 스트리트가 프리플롭이 아니고 (액션리스트가 비어있거나 마지막 액션이 체크인 경우) 
        # 플롭, 턴, 리버에서 현재 액션 콜이 첫 액션인 경우 또는 첫 액션이 체크였고 자기 차례로 돌아와 콜을 한 경우
        else:
            call_amount = self.prev_VALID
            
        self.players[current_player]["stk_size"] -= call_amount # 스택사이즈 업데이트
        self.main_pot_cumulative += call_amount # 메인팟 업데이트

        self.pot_change.append(self.prev_VALID)  # 팟 변화량 업데이트
        self.street_pot += self.prev_VALID

        # 로그 업데이트
        betting_size["call"].append(self.prev_VALID)
        action_list.append("call")
        
        self.actioned_queue.append(self.action_queue.popleft())

        '''
        모든 클라이언트들에게 다음을 요청
        콜한 클라이언트의 스택 사이즈를 self.prev_VALID 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 prev_VALID을 더한 결과로 렌더링
        '''

    def _raise(self, street_name, current_player, answer):

        if current_player in self.check_users:
            self.check_users.remove(current_player)

        action_list = self.players[current_player]["actions"][street_name]["action_list"]
        betting_size = self.players[current_player]["actions"][street_name]["betting_size"]

        # raised_total : 클라이언트에게서 전달받은 레이즈 액수 (레이즈 액수는 total을 의미)
        self.raised_total = answer["raise"]

        self.LPFB = self.raised_total - self.prev_VALID
        self.prev_VALID = self.raised_total
        self.prev_TOTAL = self.LPFB + self.prev_VALID

        # 현재 액션이 첫번째 액션이 아니고, 마지막으로 한 액션이 check가 아닌 경우
            # 모든 스트릿에서 자신이 현재 레이즈 액션 이전에 벳 or 레이즈 or 콜을 했었고 
            # 이후 올인이나 레이즈가 일어나서 다시 자기 차례에 레이즈를 한 경우        
        if action_list and action_list[-1] != 'check':
            last_action = action_list[-1]
            raise_amount = self.raised_total - betting_size[last_action]
        # 플롭, 턴, 리버에서 자신이 체크 레이즈를 하는 경우
        else:
            raise_amount = self.raised_total

        self.players[current_player]["stk_size"] -= raise_amount # 스택 사이즈 업데이트
        self.main_pot_cumulative += raise_amount # 메인 팟 업데이트

        self.pot_change.append(self.prev_VALID)  # 팟 변화량 업데이트
        self.street_pot += self.prev_VALID

        # 로그 업데이트
        betting_size["raise"].append(self.prev_VALID)
        action_list.append("raise")

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

        action_list = self.players[current_player]["actions"][street_name]["action_list"]
        betting_size = self.players[current_player]["actions"][street_name]["betting_size"]

        '''
        모든 클라이언트들에게 다음을 요청
        올인한 클라이언트에게 올인 버튼 렌더링(지속형 이벤트)
        '''
        # all_in_amount : 클라이언트에게서 전달받은 올인액수 (total을 의미)
        self.all_in_amount = answer['all-in']

        # 해당 올인이 open-bet인 경우
        if not self.attack_flag: 
            if self.prev_VALID <= self.all_in_amount:
                self.LPFB = self.all_in_amount
                self.prev_VALID = self.all_in_amount
                self.prev_TOTAL = self.prev_VALID + self.LPFB
            elif self.all_in_amount < self.prev_VALID:
                self.reorder_flag = False
        # 해당 올인이 open-bet이 아닌 경우
        else:   
            if self.prev_TOTAL <= self.all_in_amount:
                self.LPFB = self.all_in_amount- self.prev_VALID
                self.prev_VALID = self.all_in_amount
                self.prev_TOTAL = self.prev_VALID + self.LPFB
            elif self.prev_VALID <= self.all_in_amount < self.prev_TOTAL:
                self.prev_VALID = self.all_in_amount
                self.prev_TOTAL = self.prev_VALID + self.LPFB
            elif self.all_in_amount < self.prev_VALID:
                self.reorder_flag = False

        # 현재 올인 액션이 첫번째 액션이 아니고, 마지막으로 한 액션이 check가 아닌 경우
        if action_list and action_list[-1] != 'check':
            last_action = action_list[-1]
            all_in_amount = self.all_in_amount - betting_size[last_action]
        # 현재 올인 액션이 첫번째 액션이거나 마지막으로 했던 액션이 check 였던 경우
        else:
            all_in_amount = self.all_in_amount

        self.players[current_player]["stk_size"] -= all_in_amount # 스택 사이즈 업데이트
        self.main_pot_cumulative += all_in_amount # 메인팟 업데이트
      
        self.pot_change.append(self.prev_VALID)  # 팟 변화량 업데이트
        self.street_pot += self.prev_VALID

        # 로그 업데이트            
        betting_size["all-in"].append(self.prev_VALID)
        action_list.append("all_in")
    
        self.attack_flag = True
        self.user_card_open_first = True
        self.side_pot = True

        # 액션큐 처리
        if self.reorder_flag and self.actioned_queue:
            self.start_order.extend(self.actioned_queue)
            self.actioned_queue.clear()
        # 현재 올인 금액이 언더콜인 경우 start_order 유지
        elif not self.reorder_flag:
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

        # 첫 올인에 이 조건이 걸리는 건 게임 진행시간 단축에 의미있음
        # 올인유저 제외 start_order에 남은 인원이 1명 일때 이 조건이 걸리면
        # _end_conditions 에서 (모두 올인 또는 한명빼고 전부올인) 종료조건과 동일한 조건이 됨  
        if self.deep_stack_user_counter < 2:
            self.short_stack_end_flag == True
        
    def _update_pot(self, street_name):
        # 각 스트릿에서의 첫 베팅부터 합산한 팟 크기와 현재 스트리트까지의 팟 총액
        self.main_pot_confirmed[street_name][street_name] = self.main_pot_cumulative

    def _multi_pots(self, street_name):  # 사이드팟 생성함수

        all_user : list = self.actioned_queue + self.all_in_users + self.fold_users

        # 한 명 빼고 모두 폴드한 경우 = 액션을 마친 유저 숫자가 1명 뿐인 경우
        # 이 때 남은 한명은 올인유저일 경우
        if len(self.fold_users) == self.rings - 1 or len(self.actioned_queue) < 2:
            if self.actioned_queue[0] == self.all_in_users[0] or len(self.all_in_users) == 1:
                # 프리플롭에서 올인이 한명이고 나머지 모두 폴드한 경우, 유저의 지분은 블라인드
                user_stake = self.main_pot_confirmed[street_name][self.all_in_users[0]]
                user_stk_size = self.players[self.all_in_users[0]]['stk_size']
                if street_name == "pre_flop":
                    user_stake +=self.SB + self.BB
                    user_stk_size += self.all_in_amount
                    self.main_pot_cumulative -= self.all_in_amount
                # 플롭 이후 올인이 한명이고 나머지 모두 폴드한 경우, 올인 유저의 지분은 직전 스트릿까지의 팟 총액
                else:
                    prev_street = self.street_name[self.street_name.index(street_name) - 1]
                    prev_whole_pot = self.main_pot_confirmed[prev_street][prev_street]
                    user_stake += prev_whole_pot
                    user_stk_size += self.all_in_amount
                    self.main_pot_cumulative -= self.all_in_amount
        
        for all_in_position in self.all_in_users:
            all_in_size = self.players[all_in_position]["actions"][street_name]["betting_size"]["all-in"]
            stake = 0  # 개별 올인 유저의 "해당 스트릿에서의" 메인팟에 대한 지분

            for position in all_user:
                action_list = self.players[position]["actions"][street_name]["action_list"]
                if action_list and action_list[-1] != 'fold':
                    last_action = action_list[-1]
                    last_betting_size = self.players[position]["actions"][street_name]["betting_size"][last_action]
                    stake += min(last_betting_size, all_in_size)
                # 올인 유저가 없거나, 폴드한 경우 예외처리
                else:
                    pass
            
            # 어느 한 스트릿에서라도 올인을 하게 되면, 그의 지분은 그 스트릿에서의 자기 올인에 대한 지분과 직전 스트릿까지의 팟 총액이다.
            # 이 값은 그 게임의 최종 스트릿 이전 스트릿에서 올인을 한 유저가 이겼을 때 사용된다.
            # 반면 올인을 안하고 끝까지 살아남았다는 건(i.e.올인을 한번도 안하고 끝까지 레이즈, 벳, 콜 중 하나를 했다는 건), 이겼을 때 그의 지분이 전체 팟이라는 것을 의미한다.
            user_stake = self.main_pot_confirmed[street_name][all_in_position]
            user_stake = stake
            if street_name != "pre_flop":
                prev_street = self.street_name[self.street_name.index(street_name) - 1]
                prev_pot_cumulative = self.main_pot_confirmed[prev_street][prev_street]
                user_stake += prev_pot_cumulative
            
    def _check(self, street_name, current_player):
        last_action = "check"
        self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
        self.check_users.append(current_player)
        self.actioned_queue.append(self.action_queue.popleft())
        '''
        모든 클라이언트들에게 다음을 요청
        체크한 플레이어가 체크했음을 렌더링       
        '''
    
    def _fold(self, street_name, current_player):
        last_action = "fold"
        self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
        self.fold_users.append(self.action_queue.popleft())
##########################################################################
#                             SHOWDOWN
##########################################################################   
    def _end_conditions(self, street_name):
        # 모두 폴드한 경우 : 접속 상태 불량, 실제 모두 폴드 액션 버튼 누른 경우
        if len(self.fold_users) == self.rings:
            pass # 게임 종료

        # 한 명 빼고 모두 폴드한 경우 = 액션을 마친 유저 숫자가 1명 뿐인 경우
        # 이 때 남은 한명은 올인유저일 수도 있고, 마지막 베팅 유저일 수도 있다.
        if len(self.fold_users) == self.rings - 1 or len(self.actioned_queue) < 2:
            if self.actioned_queue[0] == 'check':
                pass # 게임종료

            if (len(self.all_in_users_total) == 1 and self.all_in_users) or (not self.all_in_users_total and self.actioned_queue):
                self.winner_confirmed = True
                if bool(not self.all_in_users_total and self.actioned_queue):
                    self.table_card_open_only = True

            if not self.user_card_open_first:
                self.table_card_open_first = True
            return True
        
        # 올인에 콜할수 있는 유저가 1명 뿐인 경우
        if self.short_stack_end_flag:
            if len(self.all_in_users_total) == 1:
                self.winner_confirmed = True
            return True

        # 모두 올인 또는 한명 빼고 전부 올인한 경우
        if self.rings - 1 <= len(self.all_in_users_total) + len(self.fold_users):
            return True
        
        # 현재 스트릿이 리버인 경우
        if street_name == 'river':
            if not self.user_card_open_first:
                self.table_card_open_first = True
            
            self.river_all_check = True
            self.river_bet_exists = True
            return True

    def _compare_hand(self, user_cards : dict, community_cards : list) -> dict:

        for position in user_cards:
            pocket_cards = user_cards[position]
            best_hands = self._make_best_hands(pocket_cards, community_cards)
            self.log_best_hands[position] = best_hands

        best_rank = 0
        nuts_positions = []

        # 각 위치별로 최고의 핸드를 검색
        for position, best_hands_dict in self.log_best_hands.items():
            # 현재 위치의 가장 높은 랭크와 해당 핸드를 검색
            highest_rank, hand = max(best_hands_dict.items(), key=lambda item: self.hand_power.get(item[0], 0))
            current_rank = self.hand_power.get(highest_rank, 0)
            
            # 현재 랭크가 가장 높은 랭크보다 높으면 업데이트
            if current_rank > best_rank:
                best_rank = current_rank
                nuts_positions = [position]
            # 현재 랭크가 가장 높은 랭크와 같으면 위치 추가
            elif current_rank == best_rank:
                nuts_positions.append(position)

        # 타이가 발생하는 경우 카드 랭크와 키커로 넛츠 판별. 무승부시 복수 넛츠 허용
        if len(nuts_positions) > 1:
            final_nuts_positions = self._resolve_ties(nuts_positions)
            nuts_positions = final_nuts_positions

        for position in nuts_positions:
            self.log_nuts[position] = self.log_best_hands[position]

        # 유저의 베스트 핸드를 랭크 순위대로 정렬하여 users_ranking 리스트 작성
        users_ranking = self._users_ranking()

        return users_ranking

    def _showdown(self, street_name):
        # 커뮤니티 카드 오픈 순서
        def _community_cards_open_order(street_name) -> list:
            stages = {
                'pre_flop': [("burned", 0), "flop", ("burned", 1), "turn", ("burned", 2), "river"],
                'flop': [("burned", 1), "turn", ("burned", 2), "river"],
                'turn': [("burned", 2), "river"],
                'river': []
            }
            open_order = []
            for stage in stages.get(street_name, []):
                if isinstance(stage, tuple):
                    open_order.append(self.log_hand_cards[stage[0]][stage[1]])
                else:
                    open_order.append(self.log_hand_cards[stage])
            return open_order

        community_cards : list = self._face_up_community_cards_for_showdown()
        user_cards : dict = self._face_up_user_hand()
        users_ranking : list = self._compare_hand(user_cards, community_cards)
        community_cards_open_order : list = _community_cards_open_order(street_name)

        if self.user_card_open_first:
            '''
            서버에 요청
            모든 클라이언트에게 동시에 스타팅 카드 오픈 렌더링 후
            커뮤니티 카드 오픈 렌더링 요청
            user_cards
            community_cards_open_order
            위 변수를 인자로 전달
            '''
            pass

        elif self.table_card_open_first and street_name != 'river':
            if self.table_card_open_only:
                pass
                '''
                서버에 요청
                모든 클라이언트에 커뮤니티 카드 오픈 렌더링 
                community_cards_open_order
                위 변수를 인자로 전달
                '''
            pass
            '''
            서버에 요청
            모든 클라이언트에 커뮤니티 카드 오픈 렌더링 후
            유저의 스타팅 카드 액션 순서대로 오픈 렌더링 요청
            users
            actioned_queue
            community_cards_open_order
            위 변수를 인자로 전달
            '''
        elif self.table_card_open_first and street_name == 'river':
            if self.river_all_check:
                pass
                '''
                서버에 요청
                리버에서 체크했던 순서대로 클라이언트 카드 오픈
                self.check_users 
                위 변수를 인자로 전달
                '''
            elif self.river_bet_exists and self.table_card_open_only:
                pass
                '''
                카드 오픈과 관련해 아무것도 렌더링하지 않음
                '''
            elif self.river_bet_exists and not self.table_card_open_only:
                pass
                '''
                서버에 요청
                리버에서 마지막으로 베팅액션을 한 클라이언트부터 딜링 방향으로 카드 오픈
                self.survivors 
                위 변수를 인자로 전달
                '''
            pass

        return users_ranking

    def _pot_award(self, street_name, users_ranking):
        '''
        self.side_pot = True
        self.winner_confirmed = True
        위 두가지 변수만 고려
        users_ranking 에는 all_in_users_total + actioned_queue 의 유저들의 베스트 핸드를 비교해 
        내림차순으로 정렬한 유저 포지션 리스트가 들어 있다. 무승부인 포지션은 튜플로 묶여 있다.
        넛츠는 self.log_nuts 에 있다. 타이인 경우 동률인 포지션 이름이 모두 들어 있다.
        '''
        winner_list = [position for position in self.log_nuts]

        if len(winner_list) == 1:
            winner = winner_list[0]
            # 승자가 현재 스트릿이 아닌 이전 스트릿의 올인 유저였을 경우 그의 팟 지분을 분배
            if winner in self.all_in_users_total and self.all_in_users_total[winner] != street_name:
                street = self.all_in_users_total[winner]
                stake = self.main_pot_confirmed[street][winner]
                self.players[winner]['stk_size'] += stake
                self.main_pot_cumulative -= stake

                # 남은 팟을 users_ranking을 사용해 분배
                while self.main_pot_cumulative:
                    users_ranking[1:] 
            
            # 승자가 현재 스트릿의 올인 유저이거나 한번도 올인한 적 없이 끝까지 살아남은 유저였을 때
            elif winner in self.all_in_users or winner not in self.all_in_users_total:
                action_list = self.players[winner]["actions"][street_name]["action_list"]
                betting_size = self.players[winner]["actions"][street_name]["betting_size"]
                last_action = action_list[-1]
                stake = betting_size[last_action][-1]
                self.players[winner]['stk_size'] += stake
                self.main_pot_cumulative -= stake

        elif len(winner_list) > 1:
            users_ranking[1:]
            # 남은 팟을 users_ranking을 사용해 분배
            pass 

##########################################################################
#                             AUXILIARY
##########################################################################   
    def _posting_blind(self):
        if self.stakes == "low":
            self.players["SB"]["stk_size"] -= self.SB
            self.players["BB"]["stk_size"] -= self.BB
            self.players["SB"]["actions"]["pre_flop"]["betting_size"]["bet"].append(self.SB)
            self.players["SB"]["actions"]["pre_flop"]["action_list"].append("bet")
            self.players["BB"]["actions"]["pre_flop"]["betting_size"]["bet"].append(self.BB)
            self.players["BB"]["actions"]["pre_flop"]["action_list"].append("bet")
            self.main_pot_cumulative += (self.SB + self.BB)
            self.street_pot += (self.SB + self.BB)

    def _check_connection(self, on_user_list):
        connected_users = []
        if on_user_list:
            for on_user in on_user_list:
                connected_users.append(self.user2pos[on_user])
            for position in self.start_order:
                if position not in connected_users:
                    self.fold_users.append(self.start_order.popleft())   

    def _reorder_start_member(self, street_name):
        if self.rings == 6:
            start_order = deque(["SB", "BB", "UTG", "HJ", "CO", "D"])
        elif self.rings == 6:
            start_order = deque(['SB', 'BB', 'UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D'])     
        new_order = []
        while start_order:
            position = start_order.popleft()
            if position in self.survivors:
                new_order.append(position)
        
        self.start_order = deque(new_order)

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
        all_user = [position for position in self.all_in_users_total] + self.actioned_queue
        for position in all_user:
            starting_cards = self.players[position]['starting_cards']
            user_hand[position] = starting_cards
        return user_hand
##########################################################################
#                                LOOP
##########################################################################   
    def _prep_preFlop(self, street_name, on_user_list):
        self.attack_flag == True
        self._posting_blind()
        '''
        서버에 요청
        on_user_list 변수에 접속 중인 클라이언트의 유저 아이디 요청
        모든 클라이언트에게 스택사이즈 렌더링 요청
        '''
        self._check_connection(on_user_list)

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
        self._initialize_conditions()

        self._reorder_start_member()
        cards = self._face_up_community_cards()
        '''
        서버에 요청
        on_user_list 변수에 접속 중인 클라이언트의 유저 아이디 요청
        모든 클라이언트에게 cards 전달, 렌더링 요청
        '''
        self._check_connection(on_user_list)
        '''
        서버에 요청
        스타팅 카드 전송 후 렌더링
        start_order 에 있는 유저만 남기고 나머지 유저들 삭제 렌더링
        '''
        if self.start_order:
            self.action_queue.append(self.start_order.popleft())
        else:
            pass # 예외처리        

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
        
        # 스트릿에서 모든 유저의 액션이 끝나면
        # 해당 스트릿까지의 팟 누적합 업데이트
        self._update_pot(street_name)
        if self.all_in_users:
            self._multi_pots()
        for position in self.all_in_users:
            self.all_in_users_total[position] = street_name
 
    def _finishing_street(self, street_name):
        self.survivors.extend(self.actioned_queue)
##########################################################################
#                                STREET
##########################################################################           
    def preFlop(self):
        
        street_name = "pre_flop"
        self._prep_preFlop(street_name)
        self._play_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            users_ranking = self._showdown(street_name)
            self._pot_award(street_name, users_ranking)
        self._finishing_street(street_name)
    
    def flop(self):
    
        street_name = "flop"
        self._prep_street(street_name)
        self._play_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            users_ranking = self._showdown(street_name)
            self._pot_award(street_name, users_ranking)
        self._finishing_street(street_name)
    
    def trun(self):

        street_name = "turn"
        self._prep_street(street_name)
        self._play_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            users_ranking = self._showdown(street_name)
            self._pot_award(street_name, users_ranking)
        self._finishing_street(street_name)
    
    def river(self):

        street_name = "river"
        self._prep_street(street_name)
        self._play_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            users_ranking = self._showdown(street_name)
            self._pot_award(street_name, users_ranking)
        self._finishing_street(street_name)


if __name__ == '__main__':

    dealer = Dealer(user_id_list, stk_size, rings, stakes)
    # 스트릿 루프 진입 전 클라이언트들에게 모두 제자리에 있는지 응답 요청
    dealer._posting_blind() # 호출후 SB와 BB 클라이언트의 스택사이즈를 블라인드 차감된 양으로 렌더링 요청, 메인팟 업데이트 렌더링 요청
    print(dealer.players)
    print(dealer.players["BB"]["actions"]["pre_flop"]["betting_size"])
    print(dealer.players["BB"]["actions"]["pre_flop"]["action_list"])
    print(dealer.players["BB"]['stk_size'])
