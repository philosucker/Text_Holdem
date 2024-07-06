from src import Base
from collections import deque, OrderedDict, defaultdict
import sys

class Dealer(Base):

    def __init__(self, user_id_list, stk_size, rings, stakes):
        super().__init__(user_id_list, stk_size, rings, stakes)

        if self.rings == 6:
            self.start_order = deque(["UTG", "HJ", "CO", "D", "SB", "BB"])
            
        elif self.rings == 9:
            self.start_order = deque(['UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D', 'SB', 'BB'])

        self.all_in_users_total = OrderedDict()
        self.fold_users_total = OrderedDict()

        self.main_pot_cumulative = 0
        self.pot_change = [self.main_pot_cumulative]

        self.main_pot_confirmed = defaultdict(dict)
        self.main_pot_confirmed["pre_flop"] = {}
        self.main_pot_confirmed["flop"] = {}
        self.main_pot_confirmed["turn"] = {}
        self.main_pot_confirmed["river"] = {}
        
        self.street_name = ["pre_flop", "flop", "turn", "river"]

        self._initialize_betting_state()
        self._initialize_action_state()
        self._initialize_conditions()      

    def _initialize_betting_state(self):
        self.raised_total = 0 # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
        self.bet_amount = 0 # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
        self.all_in_amount = 0   

        self.LPFB = self.BB # the largest prior full bet = the last legal increment = minimum raise
        self.prev_VALID = self.BB  # 콜시 유저의 스택에 남아 있어야 하는 최소 스택 사이즈의 기준
        self.prev_TOTAL = self.prev_VALID + self.LPFB # 레이즈시 유저의 스택에 남아있어야 하는 최소 스택 사이즈의 기준

        self.street_pot = 0 # 해당 스트릿에서만 발생한 베팅 총액, 필요한 변수일까? 검토 필요

    def _initialize_action_state(self):
        self.action_queue = deque([])
        self.actioned_queue = deque([])

        self.all_in_users = list()
        self.fold_users = list()

        self.check_users = list()
        self.attack_flag = False # only only and just once bet, raise, all-in is True  # 플롭부터는 False로 초기화
        self.raise_counter = 0 # 5가 되면 Possible action 에서 raise 삭제
        self.reorder_flag = True # 언더콜인 올인 발생시 actioned_queue에 있는 유저들을 start_order 리스트 뒤에 붙이는 reorder를 금지시키기 위한 플래그

    def _initialize_conditions(self):
        self.deep_stack_user_counter = 0
        self.short_stack_end_flag = False # 올인 발생시 딥스택 유저 수 부족으로 바로 핸드 종료시키는 조건

        self.user_card_open_first = False # TDA Rule 16 : Face Up for All
        self.table_card_open_first = False
        self.table_card_open_only = False # TDA Rule 18 : Asking to See a Hand

        self.river_all_check = False # TDA Rule : 17 : Non All-In Showdowns and Showdown Order
        self.river_bet_exists = False # TDA Rule : 17 : Non All-In Showdowns and Showdown Order

        self.survivors = list() # 다음 스트릿으로 갈 생존자 리스트

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                      ACTION                                                                      #
    ####################################################################################################################################################
    ####################################################################################################################################################
    
    def _possible_actions(self, street_name, current_player):

        player_stack = self.players[current_player]['stk_size']

        if street_name == 'pre_flop':
            # 프리플롭에서 첫 바퀴를 돌고 BB 차례가 되었을 때, 모두 콜 or 폴드만 한 경우 BB option 및 check 구현
            if self.raised_total == 0 and len(self.all_in_users) == 0 and current_player == 'BB':
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

        betting_size_total = self.players[current_player]["actions"][street_name]["betting_size_total"]
        pot_contribution = self.players[current_player]["actions"][street_name]["pot_contribution"]        
        action_list = self.players[current_player]["actions"][street_name]["action_list"]

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
        betting_size_total["bet"].append(self.prev_VALID)
        pot_contribution["bet"].append(self.prev_VALID)
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

        betting_size_total = self.players[current_player]["actions"][street_name]["betting_size_total"]
        pot_contribution = self.players[current_player]["actions"][street_name]["pot_contribution"]        
        action_list = self.players[current_player]["actions"][street_name]["action_list"]

        # 현재 액션이 첫번째 액션이 아닌 경우
        if action_list:
            last_action = action_list[-1]
        # 현재 액션 콜이 첫번째 액션인 경우
        else:
            last_action = None

        # 현재 스트리트가 프리플롭이거나 (모든 스트리트에서 현재 액션이 첫 액션이 아니고 마지막 액션이 체크가 아닌 경우)
        if street_name == 'pre_flop' or (action_list and last_action != 'check'):
            if last_action:
                call_amount = self.prev_VALID - betting_size_total[last_action][-1]
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
        betting_size_total["call"].append(self.prev_VALID)
        pot_contribution["call"].append(call_amount)
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

        betting_size_total = self.players[current_player]["actions"][street_name]["betting_size_total"]
        pot_contribution = self.players[current_player]["actions"][street_name]["pot_contribution"]        
        action_list = self.players[current_player]["actions"][street_name]["action_list"]

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
            raise_amount = self.raised_total - betting_size_total[last_action][-1]
        # 플롭, 턴, 리버에서 자신이 체크 레이즈를 하는 경우
        else:
            raise_amount = self.raised_total

        self.players[current_player]["stk_size"] -= raise_amount # 스택 사이즈 업데이트
        self.main_pot_cumulative += raise_amount # 메인 팟 업데이트

        self.pot_change.append(self.prev_VALID)  # 팟 변화량 업데이트
        self.street_pot += self.prev_VALID

        # 로그 업데이트
        betting_size_total["raise"].append(self.prev_VALID)
        pot_contribution["raise"].append(raise_amount)
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
    
    def _all_in(self, street_name, current_player):

        if current_player in self.check_users:
            self.check_users.remove(current_player)

        betting_size_total = self.players[current_player]["actions"][street_name]["betting_size_total"]
        pot_contribution = self.players[current_player]["actions"][street_name]["pot_contribution"]        
        action_list = self.players[current_player]["actions"][street_name]["action_list"]

        '''
        모든 클라이언트들에게 다음을 요청
        올인한 클라이언트에게 올인 버튼 렌더링(지속형 이벤트)
        '''
        # all_in_amount : 클라이언트에게서 전달받은 올인액수 (total을 의미)
        self.all_in_amount = self.players[current_player]['stk_size']

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

        self.players[current_player]["stk_size"] -= self.all_in_amount # 스택 사이즈 업데이트
        self.main_pot_cumulative += self.all_in_amount # 메인팟 업데이트
      
        self.pot_change.append(self.all_in_amount)  # 팟 변화량 업데이트
        self.street_pot += self.all_in_amount

        # 로그 업데이트
        betting_size_total["all-in"].append(self.all_in_amount)
        pot_contribution["all-in"].append(self.all_in_amount)
        action_list.append("all-in")
    
        self.attack_flag = True
        self.user_card_open_first = True

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

    def _sum_pot_contributions(self, path):
        pot_contribution = path
        total_sum = 0
        for key in pot_contribution:
            total_sum += sum(pot_contribution[key])
        return total_sum
        
    def _multi_pots(self, street_name):  # 사이드팟 생성함수

        all_user : list = list(self.actioned_queue) + self.all_in_users + self.fold_users

        # 한 명 빼고 모두 폴드한 경우 이 때 남은 한명이 올인유저일 경우
        if len(self.all_in_users) == 1 and len(self.fold_users_total) == self.rings - 1:
            # 그런 올인 유저가 프리플롭에서 발생했을 때 그의 지분은 블라인드
            if street_name == "pre_flop":
                self.main_pot_confirmed[street_name][self.all_in_users[0]] = self.SB + self.BB
                self.players[self.all_in_users[0]]['stk_size'] += self.all_in_amount
                self.main_pot_cumulative -= self.all_in_amount
            # 그런 올인 유저가 플롭이후부터 발생했을 때 그의 유저의 지분은 직전 스트릿까지의 팟 총액
            else:
                prev_street = self.street_name[self.street_name.index(street_name) - 1]
                prev_whole_pot = self.main_pot_confirmed[prev_street][prev_street]
                self.main_pot_confirmed[street_name][self.all_in_users[0]] += prev_whole_pot
                self.players[self.all_in_users[0]]['stk_size'] += self.all_in_amount
                self.main_pot_cumulative -= self.all_in_amount
        else:            
            for all_in_position in self.all_in_users:
                self.main_pot_confirmed[street_name][all_in_position] = 0
                # 올인 유저들의 "해당 스트릿에서의" 메인팟에 대한 지분
                all_in_user_stake = 0
                all_in_user_path = self.players[all_in_position]["actions"][street_name]["pot_contribution"]
                all_in_user_pot_contribution = self._sum_pot_contributions(all_in_user_path)
                
                # 해당 스트릿에서의 모든 유저의 팟 기여도
                user_contributions = {position: self._sum_pot_contributions(self.players[position]["actions"][street_name]["pot_contribution"]) for position in all_user}
                
                for _ , contribution in user_contributions.items():
                    all_in_user_stake += min(contribution, all_in_user_pot_contribution)
                
                self.main_pot_confirmed[street_name][all_in_position] = all_in_user_stake

                # 플롭 이후 스트릿에서 올인을 했다면, 그의 지분은 그 스트릿에서의 자기 올인에 대한 지분에 직전 스트릿까지의 팟 총액을 더해야 한다.
                prev_pot_cumulative = 0
                if street_name != "pre_flop":
                    prev_street = self.street_name[self.street_name.index(street_name) - 1]
                    prev_pot_cumulative = self.main_pot_confirmed[prev_street][prev_street]
                    self.main_pot_confirmed[street_name][all_in_position] += prev_pot_cumulative

                # 해당 스트릿에서 승자 발생시, 해당 스트릿에서의 승자들이 무승부인 경우, 그들이 가져가게 될 공통 몫
                fold_users_stake = 0
                for fold_user in self.fold_users:
                    fold_user_path = self.players[fold_user]["actions"][street_name]["pot_contribution"]
                    fold_user_pot_contribution = self._sum_pot_contributions(fold_user_path)
                    fold_users_stake += fold_user_pot_contribution     
                common_share = fold_users_stake + prev_pot_cumulative
                self.main_pot_confirmed[street_name]['common_share'] = common_share

    def _check(self, street_name, current_player):
        last_action = "check"
        self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
        self.actioned_queue.append(current_player)
        self.check_users.append(self.action_queue.popleft())
        '''
        모든 클라이언트들에게 다음을 요청
        체크한 플레이어가 체크했음을 렌더링       
        '''
    
    def _fold(self, street_name, current_player):

        if current_player in self.check_users: # 체크했던 유저가 폴드할 수도 있다.
            self.check_users.remove(current_player)

        last_action = "fold"
        self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
        self.fold_users.append(self.action_queue.popleft())

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    SHOWDOWN                                                                      #
    ####################################################################################################################################################
    ####################################################################################################################################################
       
    def _end_conditions(self, street_name):
        
        if len(self.fold_users_total) == self.rings:
            print("every user fold")
            return 

        # 한 명 빼고 모두 폴드한 경우 = 액션을 마친 유저 숫자가 1명 뿐인 경우
        # 이 때 남은 한명은 올인유저일 수도 있고, 마지막 베팅 유저일 수도 있다.
        if len(self.fold_users_total) == self.rings - 1 or len(self.actioned_queue) == 1 :
            if self.actioned_queue and self.check_users:
                self.check_users[0] == self.actioned_queue[0]
                print("all other user fold after first player check")
                return
            
            # 마지막 남은 유저 1명이 올인 유저인 경우
            if (len(self.all_in_users_total) == 1 and self.all_in_users):
                self.table_card_open_first = True
                self.table_card_open_only = True                
                return True
            
            # 마지막 남은 유저 1명이 올인 유저가 아닌 베팅 유저인 경우
            if not self.all_in_users_total and self.actioned_queue:
                self.table_card_open_first = True
                self.table_card_open_only = True
                return True
        
        # 올인에 콜할수 있는 유저가 1명 뿐인 경우
        if self.short_stack_end_flag:
            return True

        # 모두 올인 또는 한명 빼고 전부 올인한 경우
        if self.rings - 1 <= len(self.all_in_users_total) + len(self.fold_users_total):
            return True
        
        # 현재 스트릿이 리버인 경우
        if street_name == 'river':
            if len(self.actioned_queue) == len(self.check_users):
                self.river_all_check = True
            if len(self.check_users) == 0:
                self.river_bet_exists = True
                if len(self.fold_users_total) == self.rings - 1:
                    self.table_card_open_only = True
            return True
        

        return False
    
    def _compare_hand(self, user_cards : dict, community_cards : list):

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

        # live hands의 베스트 핸드를 랭크 순위대로 정렬하여 users_ranking 리스트 작성
        self.log_users_ranking = self._users_ranking()

        nuts = self.log_nuts
        users_ranking = self.log_users_ranking

        return nuts, users_ranking

    def _showdown(self, street_name : str) -> dict:
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
        

        community_cards : list = self._face_up_community_cards_for_showdown(street_name) # _face_up_community_cards_for_showdown 호출 후
        community_cards_open_order : list = _community_cards_open_order(street_name) #_community_cards_open_order 호출되어야 한다. 호출순서 바뀌면 안됨

        # self._check_connection(on_user_list) # 실제코드
        user_cards : dict = self._face_up_user_hand()
        nuts, users_ranking = self._compare_hand(user_cards, community_cards)
        

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
        elif street_name == 'river':
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

        return nuts, users_ranking

    def _pot_award(self, street_name : str, nuts : dict, users_ranking : deque) -> None:
        winner_list = [winner for winner in nuts.keys()]
        final_street_live_hands = self.all_in_users + list(self.actioned_queue)
        #  (1) 맨 마지막까지 진행된 스트릿에서만 승자가 나온 경우 
        if all(winner in final_street_live_hands for winner in winner_list):
            # 승자가 한 명일 때 
            max_value = max(self.main_pot_confirmed[street_name].values())
            if len(winner_list) == 1:
                winner = winner_list[0]
                # short all in 으로 이긴 경우
                if self.main_pot_confirmed[street_name][winner] != max_value:
                    # winner 의 지분을 분배한 후
                    self.players[winner]['stk_size'] = self.main_pot_confirmed[street_name][winner]
                    self.main_pot_cumulative -= self.main_pot_confirmed[street_name][winner]
                    # winner를 순위표에서 뺀 다음
                    users_ranking.popleft()
                    # 순위표에 남아 있는 유저들의 해당 스트릿 기여도와 남은 팟 금액을 비교해서
                    while self.main_pot_cumulative > 0:
                        # 남은 유저 랭킹에서 해당 등수 유저가 여러 명인 경우
                        if isinstance(users_ranking[0], tuple):
                            for user in users_ranking[0]:
                                user_pot_contribution = self._sum_pot_contributions(self.players[user]['actions'][street_name]["pot_contribution"])
                                if user_pot_contribution >= self.main_pot_cumulative:
                                    self.players[user]['stk_size'] += self.main_pot_cumulative
                                    self.main_pot_cumulative = 0
                                elif user_pot_contribution < self.main_pot_cumulative:
                                    self.players[user]['stk_size'] += user_pot_contribution
                                    self.main_pot_cumulative -= user_pot_contribution       
                            users_ranking.popleft()       
                        # 남은 유저 랭킹에서 해당 등수가 유일한 경우의 유저인 경우
                        else:             
                            user_pot_contribution = self._sum_pot_contributions(self.players[users_ranking[0]]['actions'][street_name]["pot_contribution"])
                            # 기여도가 팟보다 크면 남은 팟을 다 주고
                            if user_pot_contribution >= self.main_pot_cumulative:
                                self.players[users_ranking[0]]['stk_size'] += self.main_pot_cumulative
                                self.main_pot_cumulative = 0
                            # 기여도가 팟보다 작으면 기여도 만큼만 돌려주고, 팟에서 그 기여도만큼 뺀 금액으로 남은 팟을 계산한 후
                            elif user_pot_contribution < self.main_pot_cumulative:
                                self.players[users_ranking[0]]['stk_size'] += user_pot_contribution
                                self.main_pot_cumulative -= user_pot_contribution
                            # 배분이 끝난 유저는 빼고 다시 루프로 돌아간다.
                            users_ranking.popleft()
 
                    assert self.main_pot_cumulative == 0           
                        
                # 그냥 이겼거나 full all in으로 이긴 경우
                else:
                    self.players[winner]['stk_size'] = self.main_pot_cumulative
                    self.main_pot_cumulative -= self.main_pot_cumulative

                    assert self.main_pot_cumulative == 0  

            # 승자가 여러 명일 때
            elif len(winner_list) > 1:
                # short all in 으로 이긴 사람이 승자 구성에 포함된 경우
                if any(self.main_pot_confirmed[street_name][winner] != max_value for winner in winner_list):
                    # 지분이 가장 작은 순서대로 오름차순 정렬한 다음
                    tie_winner_list = sorted(winner_list, key=lambda winner: self.main_pot_confirmed[street_name].get(winner, float('inf')))
                    # 해당 스트릿에서 무승부인 승자들이 공통으로 가져갈 몫을 먼저 분배 한 후 (multi_pot에 있는 코드와 겹친다. 합칠수 없나?)
                    losers_list = [user for user in self.live_hands if user not in winner_list]
                    losers_stake = 0
                    for loser in losers_list:
                        loser_path = self.players[loser]["actions"][street_name]["pot_contribution"]
                        loser_pot_contribution = self._sum_pot_contributions(loser_path)
                        losers_stake += loser_pot_contribution

                    common_share = self.main_pot_confirmed[street_name]['common_share']   
                    common_share += losers_stake
                    quotient, remainder = divmod(common_share, len(tie_winner_list))
                    print(quotient, remainder)
                    for winner in tie_winner_list:
                        self.players[winner]['stk_size'] += quotient
                        self.main_pot_cumulative -= quotient
                    
                    # 나머지를 버튼에서 왼쪽 방향으로 가장 가까운 사람에게 준 다음.
                    start_order = self._start_order(street_name)
                    for user in start_order:
                        if user in self.fold_users_total:
                            continue
                        else:
                            self.players[user]['stk_size'] += remainder
                            self.main_pot_cumulative -= remainder
                            break
                    # 남은 팟을 승자발생 스트릿에서의 자기 지분 만큼 가져간다.
                    for winner in tie_winner_list:
                        stake = self._sum_pot_contributions(self.players[winner]['actions'][street_name]["pot_contribution"])
                        self.players[winner]['stk_size'] += stake
                        self.main_pot_cumulative -= stake
                    print(self.main_pot_cumulative)      

                    assert self.main_pot_cumulative == 0

                # 그냥 이겼거나 full all in으로 이긴 사람으로만 승자가 구성된 경우
                else:                
                    quotient, remainder = divmod(self.main_pot_cumulative, len(winner_list))
                    for winner in winner_list:
                        self.players[winner]['stk_size'] = quotient
                        self.main_pot_cumulative -= quotient
                    # 나머지는 버튼에서 왼쪽 방향으로 가장 가까운 사람에게 준다.
                    for user in self.start_order:
                        if user in self.fold_users_total:
                            continue
                        else:
                            self.players[user]['stk_size'] += remainder
                            break
                    self.main_pot_cumulative -= remainder

                    assert self.main_pot_cumulative == 0            

       
        # (2)맨 마지막까지 진행된 스트릿 이전 스트릿에서 승자가 나온 경우
        else:
            print("미구현")

    #     # 이 경우 승자가 1명인 경우
    #     if 
        
    #     # 승자가 여러 명인 경우
    #     else:
        '''
        (1) 맨 마지막까지 진행된 스트릿에서만 승자가 나온 경우 
                승자가 한명이면 
                    풀 올인으로 이길 때, 그냥 이길 때 팟 전부 를 가져간다. 
                    short all in 으로 이길 때 팟을 나눈다.
                승자가 여러명이면(무승부인 경우)
                    풀인 올인 유저와 그냥 이긴 승자들만 있을 때 팟을 등분한다.
                        나머지가 생기면 딜러에서 왼쪽으로 가까운 포지션이 가진다
                    short all in 유저가 섞여 있을 때 지분대로 팟을 나눈다. 
                        나머지가 생기면 딜러에서 왼쪽으로 가까운 포지션이 가진다
                            남은 팟은 각자 지분만큼 돌려준다
                            
        (2) 맨 마지막까지 진행된 스트릿 이전 스트릿에서 승자가 나온 경우
            그 이전 스트릿에서 승자가 한명 나오는 경우는 (이 경우 올인 유저는 계산되어 있고 나머지 유저의 지분을 계산해야 한다) 지분만큼 팟을 가져가고
             이 경우 같은 스트릿에서 무승부라면 지분대로 가져가고
             다른 스트릿에서 무승부라면, 스트릿 순서대로 승자 지분을 배분하고
                위 두 경우 모두 메인 팟에서 승자들의 지분을 뺀 나머지가 승자가 아닌 유저들에게 돌아간다
                이 나머지는 가장 마지막 스트릿에서 승자가 이긴 스트릿 이후 스트릿들에 참여한 유저들에게 돌려줘야 하는 돈이다. 
                    돌려줄 때 핸드 랭크 순으로 돌려준다.
        
        따라서 가장 바깥의 조건문은 승자가 맨마지막에서 진행된 스트릿에서 나왔는지 아닌지를 먼저 따진다.
        맨 마지막에서 나왔다면 (1)로 팟 어워드 하면 끝난다.
        아니라면 (2) 로 팟어워드를 한다
        
        (2) 상세
        이전 스트릿의 올인 유저와 그 스트릿과 같은 스트릿에서 올인한 유저가 무승부인 경우: 
            이 경우 이미 올인 유저의 지분을 다 계산했으므로 그걸 사용한다. 
                지분이 같으므로 팟을 등분하고 나머지가 생기면 딜러에서 왼쪽으로 가까운 포지션이 가진다
                    그리고도 남은 나머지는 가장 마지막 스트릿에서 우승한 올인 유저 그 다음 스트릿부터 끝까지 참여한 유저가 있는 경우 그들의 핸드랭크 순으로 돌려준다.
            
        이전 스트릿의 올인 유저와 다른 스트릿의 올인 유저가 무승부인 경우 : 
            이 경우는 승자들의 지분이 다르지만 이미 올인유저의 지분을 다 계산했으므로 그걸 사용한다. 
                지분이 다르므로 지분대로 팟을 나누고 나머지가 생기면 딜러에서 왼쪽으로 가까운 포지션이 가진다
                    그리고도 남은 나머지는 가장 마지막 스트릿에서 우승한 올인 유저 그 다음 스트릿부터 끝까지 참여한 유저가 있는 경우 그들의 핸드랭크 순으로 돌려준다.

        이전 스트릿의 올인 유저와 마지막 스트릿의 그냥 유저가 무승부인 경우 : 
            이 경우는 올인 유저의 지분은 계산한걸 사용하고 마지막 스트릿의 유저의 지분은 전체팟이에 해당한다.
            올인 유저의 지분이 마지막 스트릿 유저의 지분보다 적은 경우
            500 : 700 인 경우
            700의 절반인 350을 등분한다.
            전체팟의 절반보다 올인 유저의 지분이 적은 경우
            300 : 700 인 경우
            올인 유저의 지분을 먼저 배분하고 나머지는 전부 마지막 스트릿 유저에게 준다.

        '''
    
    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    AUXILIARY                                                                     #
    ####################################################################################################################################################
    ####################################################################################################################################################
    
    def _posting_blind(self):
        if self.stakes == "low":
            self.players["SB"]["stk_size"] -= self.SB
            self.players["BB"]["stk_size"] -= self.BB
            self.players["SB"]["actions"]["pre_flop"]["betting_size_total"]["bet"].append(self.SB)
            self.players["SB"]["actions"]["pre_flop"]["action_list"].append("bet")
            self.players["BB"]["actions"]["pre_flop"]["betting_size_total"]["bet"].append(self.BB)
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
                    self.fold_users_total[position] = self.start_order.popleft()

    def _start_order(self, street_name):
        if street_name == 'pre_flop':
            if self.rings == 6:
                start_order = ["SB", "BB", "UTG", "HJ", "CO", "D"]
            elif self.rings == 6:
                start_order = ['SB', 'BB', 'UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D']
        else:
            if self.rings == 6:
                start_order =["UTG", "HJ", "CO", "D", "SB", "BB"]
                
            elif self.rings == 9:
                start_order = ['UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D', 'SB', 'BB']
        
        return start_order

    def _reorder_start_member(self):
        if self.rings == 6:
            start_order = deque(["SB", "BB", "UTG", "HJ", "CO", "D"])
        elif self.rings == 9:
            start_order = deque(['SB', 'BB', 'UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D'])     
        new_order = []
        while start_order:
            position = start_order.popleft()
            if position in self.survivors:
                new_order.append(position)
        
        self.start_order = deque(new_order)

    def _face_up_community_cards(self, street_name : str) -> list: 
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
        all_user = [position for position in self.all_in_users_total] + list(self.actioned_queue)
        for position in all_user:
            starting_cards = self.players[position]['starting_cards']
            user_hand[position] = starting_cards
        return user_hand
    
    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                     STREET                                                                       #
    ####################################################################################################################################################
    ####################################################################################################################################################
    
    def _prep_preFlop(self):

        # SB와 BB의 블라인드 포스팅은 bet으로 간주
        self.attack_flag == True
        self._posting_blind()

        # 시스템 로그. 유저 액션 기록
        self.log_hand_actions['pre_flop'].append(("SB", {"bet" : self.SB}))
        self.log_hand_actions['pre_flop'].append(("BB", {"bet" : self.BB}))
        self.players['SB']["actions"]['pre_flop']["betting_size_total"]['bet'].append(self.SB)
        self.players['SB']["actions"]['pre_flop']['pot_contribution']['bet'].append(self.SB) 
        self.players['SB']["actions"]['pre_flop']["action_list"].append('bet')
        self.players['BB']["actions"]['pre_flop']["betting_size_total"]['bet'].append(self.BB)
        self.players['BB']["actions"]['pre_flop']['pot_contribution']['bet'].append(self.BB) 
        self.players['BB']["actions"]['pre_flop']["action_list"].append('bet')    

        '''
        서버 요청 사항
        1. 현재 접속 중인 클라이언트의 유저 아이디 리스트 요청. on_user_list 변수에 할당
        2. 모든 클라이언트에게 스타팅 카드 전송 후 렌더링. users_starting_cards 딕셔너리 전달
        3. 모든 클라이언트에게 스택사이즈 렌더링 요청. users_stack_size 딕셔너리 전달
        4. start_order 에 있는 유저만 남기고 나머지 유저들 삭제 렌더링. start_order 리스트 전달
        '''
        # on_user_list =  # 서버에서 전달 받은 현재 접속 중인 클라이언트들의 유저 아이디 리스트

        # 현재 접속 중인 유저만 남기고 start_order 재정렬
        # self._check_connection(on_user_list) # 실제코드

        users_starting_cards = dict()
        users_stack_size = dict()

        for position in self.start_order:
            starting_cards = self.players[position]['starting_cards']
            users_starting_cards[position] = starting_cards
            stack_size = self.players[position]['stk_size']
            users_stack_size[position] = stack_size

        start_order = self.start_order.copy() 

        # 유저 액선큐 등록
        if self.start_order:
            self.action_queue.append(self.start_order.popleft())

    def _prep_street(self, street_name):
        
        # 이전 스트릿에서 넘어온 유저만을 대상으로 start_order 재정렬
        self._reorder_start_member()

        # 스트릿에서 사용할 인스턴스 변수들 초기화
        self._initialize_betting_state()
        self._initialize_action_state()
        self._initialize_conditions()

        '''
        서버 요청 사항
        1. 현재 접속 중인 클라이언트의 유저 아이디 리스트 요청. on_user_list 변수에 할당
        2. 모든 클라이언트에게 스타팅 카드 전송 후 렌더링. users_starting_cards 딕셔너리 전달
        3. 모든 클라이언트에게 커뮤니티 카드 전송 후 렌더링.community_cards 리스트 전달
        4. 모든 클라이언트에게 스택사이즈 렌더링 요청. users_stack_size 딕셔너리 전달
        5. 모든 클라이언트에게 팟 사이즈 렌더링 요청.  main_pot 전달
        6. start_order 에 있는 유저만 남기고 나머지 유저들 삭제 렌더링. start_order 리스트 전달
        '''

        # on_user_list =  # 서버에서 전달 받은 현재 접속 중인 클라이언트들의 유저 아이디 리스트

        # 현재 접속 중인 유저만 남기고 start_order 재정렬
        # self._check_connection(on_user_list) # 실제코드

        community_cards :list = self._face_up_community_cards(street_name)
        users_starting_cards = dict()
        users_stack_size = dict()

        for position in self.start_order:
            starting_cards = self.players[position]['starting_cards']
            users_starting_cards[position] = starting_cards
            stack_size = self.players[position]['stk_size']
            users_stack_size[position] = stack_size

        main_pot = self.main_pot_cumulative

        start_order = self.start_order.copy() 

        # 유저 액선큐 등록
        if self.start_order:
            self.action_queue.append(self.start_order.popleft())

    def _play_street(self, street_name):

        while self.action_queue:

            current_player = self.action_queue[0]
            possible_actions : list = self._possible_actions(street_name, current_player)

            '''
            서버 요청 사항 
            시간제한은 클라이언트 쪽에서 구현
            1. current_player에 해당하는 클라이언트에게 possible_actions 리스트 전달, 렌더링 요청
            2. current_player에 해당하는 클라이언트가 bet, raise, all-in을 할 수 있는 경우 betting_condition 리스트 전달, 렌더링 요청
                self.prev_VALID 유저가 베팅 액션 선택시 베팅 해야하는 최소 금액
                self.prev_TOTAL 유저가 레이즈 액션 선택시 가능한 레이즈 최소 금액 렌더링 요청
            
            '''
            for action in possible_actions:
                if action in ['bet', 'raise', 'all-in']:
                    betting_condition = [self.prev_VALID, self.prev_TOTAL]

            stack_size = self.players[current_player]['stk_size']

            '''
            서버 응답 대기
            현재 액션할 차례인 클라이언트가 서버에 전달한 액션 내용을 서버로부터 받음
            응답 형식 : 딕셔너리 = {액션종류, 베팅금액}
            {'call' : None}, {'fold' : None}, {'check' : None},  {'all-in' : None} 
            {'bet' : bet_amount}, {'raise' : raise_amount} 
            서버로부터 받은 응답을 answer 변수에 할당
            '''

            # answer = 서버로부터 전달받은 유저의 액션 내용이 담긴 딕셔너리 

            # 테스트 코드
            answer = self.test_code_action_info(current_player, possible_actions, street_name)

            # 클라이언트에게 전달 받은 응답이 call 이면
            if next(iter(answer)) == "call":
                self._call(street_name, current_player)
                
            # 클라이언트에게 전달 받은 응답이 fold 면 
            elif next(iter(answer)) == "fold":
                self._fold(street_name, current_player)
                
            # 클라이언트에게 전달 받은 응답이 check 면      
            elif next(iter(answer)) == "check":  # BB 만 가능
                self._check(street_name, current_player)

             # 클라이언트로부터 전달 받은 응답이 answer = {"bet" : bet_amount} 이면
            elif next(iter(answer)) == "bet": # 플롭부터 가능
                self._bet(street_name, current_player, answer)

            # 클라이언트로부터 전달 받은 응답이 answer = {"raise" : raised_total} 이면
            elif next(iter(answer)) == "raise":
                self._raise(street_name, current_player, answer)
                 
            # 클라이언트로부터 전달 받은 응답이 answer = {"all-in" : all_in_amount} 이면
            elif next(iter(answer)) == "all-in":
                self._all_in(street_name, current_player)

            '''
            서버 요청 사항
            1. 모든 클라이언트에게 answer 딕셔너리 전달
                현재 플레이어의 액션 종류 렌더링 요청
                각 액션에 따른 팟 금액 변화, 해당 유저의 스택사이즈 변화 렌더링 요청
            '''
            
            # 다음 차례 유저 액션큐 등록
            if self.start_order:
                self.action_queue.append(self.start_order.popleft())
            
            # 시스템 로그. 유저 액션 기록
            if next(iter(answer)) == 'all-in':
                answer = {'all-in' : self.players[current_player]['actions'][street_name]['betting_size_total']['all-in'][-1]}
                self.log_hand_actions[street_name].append((current_player, answer)) 
            elif next(iter(answer)) == 'call':
                answer = {'call' : self.players[current_player]['actions'][street_name]['betting_size_total']['call'][-1]}
                self.log_hand_actions[street_name].append((current_player, answer))
            else:
                self.log_hand_actions[street_name].append((current_player, answer)) 

    def _finishing_street(self, street_name):

        # 해당 스트릿까지의 팟 누적합 업데이트
        self._update_pot(street_name)

        # 해당 스트릿에서 올인 유저 발생시 올인 유저의 지분 계산 (사이드 팟 생성)
        if self.all_in_users:
            self._multi_pots(street_name)

        # 현재 스트릿의 올인 유저 리스트를 전체 올인 리스트에 추가
        for position in self.all_in_users:
            self.all_in_users_total[position] = street_name
       # 현재 스트릿의 폴드 유저 리스트를 전체 폴드 리스트에 추가
        for position in self.fold_users:
            self.fold_users_total[position] = street_name

        # 스택 사이즈가 0인 유저는 all_in_users_total 로 이동 (suvivors에서 제외)
        # 해당 스트릿 종료시 마지막 액션이 콜인 유저의 스택사이즈가 0이 되는 경우가 있음. 케이스1 참고
        if self.actioned_queue:
            new_actioned_queue = []
            for position in self.actioned_queue:
                if self.players[position]['stk_size'] == 0:
                    self.all_in_users_total.append(position)
                else:
                    # 다음 스트릿으로 이동시킬 유저 리스트 업데이트
                    new_actioned_queue.append(position)
            self.survivors.extend(new_actioned_queue)

        # 테스트 코드
        self.test_code_street_info(street_name)

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                      HAND                                                                        #
    ####################################################################################################################################################
    ####################################################################################################################################################

    def _preFlop(self, stk_size):
        
        street_name = "pre_flop"
        self._prep_preFlop()
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            nuts, users_ranking = self._showdown(street_name)
             # 테스트 코드
            self.test_code_showdown_info()

            self._pot_award(street_name, nuts, users_ranking)

            # 테스트 코드
            self.test_code_pot_award_info(stk_size)
        else:
            self._flop(stk_size)
    
    def _flop(self, stk_size):
    
        street_name = "flop"
        self._prep_street(street_name)
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            nuts, users_ranking = self._showdown(street_name)
            # 테스트 코드
            self.test_code_showdown_info()

            self._pot_award(street_name, nuts, users_ranking)

            # 테스트 코드
            self.test_code_pot_award_info(stk_size)
        else:
            self._turn(stk_size)
    
    def _turn(self, stk_size):

        street_name = "turn"
        self._prep_street(street_name)
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            nuts, users_ranking = self._showdown(street_name)
            # 테스트 코드
            self.test_code_showdown_info()

            self._pot_award(street_name, nuts, users_ranking)

            # 테스트 코드
            self.test_code_pot_award_info(stk_size)
        else:
            self._river(stk_size)
    
    def _river(self, stk_size):

        street_name = "river"
        self._prep_street(street_name)
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            nuts, users_ranking = self._showdown(street_name)
            # 테스트 코드
            self.test_code_showdown_info()

            self._pot_award(street_name, nuts, users_ranking)

            # 테스트 코드
            self.test_code_pot_award_info(stk_size)
        else:
            print("!!!!!!!!!!!!!!종료조건에 걸리지 않는 상황입니다. 유저들의 액션을 검토해서 종료조건을 수정하거나 추가하세요!!!!!!!!!!!!!!")    

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    EXECUTION                                                                     #
    ####################################################################################################################################################
    ####################################################################################################################################################

    def go_street(self, stk_size):
        self._preFlop(stk_size)     

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    TEST CODE                                                                     #
    ####################################################################################################################################################
    ####################################################################################################################################################
    
    def get_input(self, prompt):
        print(prompt)
        input_line = sys.stdin.readline().strip()
        parts = input_line.split()
        
        if len(parts) == 2:
            key = parts[0]
            try:
                value = int(parts[1])
            except ValueError:
                value = None
        elif len(parts) == 1:
            key = parts[0]
            value = None
        else:
            raise ValueError("Invalid input format. Expected format: 'string' or 'string int'")

        return {key: value}
    
    def test_code_action_info(self, current_player, possible_actions, street_name):
        print(f'{street_name} 스트리트 입니다')
        stack_size = self.players[current_player]['stk_size']
        print(f'LPFB : {self.LPFB}')
        print(f'prev_VALID : {self.prev_VALID}')
        print(f'prev_TOTAL : {self.prev_TOTAL}')
        print(f'{current_player} 님의 현재 스택사이즈는 {stack_size}입니다')
        print(f'{current_player} 님의 가능한 액션은 {possible_actions} 입니다') 
        answer = self.get_input(f'{current_player} 님 액션을 입력해 주세요')    
        print(f'{current_player}님의 액션은 {next(iter(answer))} 입니다')
        print()
        return answer

    def test_code_street_info(self, street_name):
        print()
        print(f'==============={street_name} 스트리트===============')
        print(f'actioned_queue: {self.actioned_queue}')
        print(f'fold_users: {self.fold_users}')
        print(f'fold_users_total: {self.fold_users_total}')
        print(f'all_in_users: {self.all_in_users}')
        print(f'all_in_users_total: {self.all_in_users_total}')
        print()
        print(f'일어난 모든 액션들의 내용을 일어난 순서대로 기록: {self.log_hand_actions}')
        print(f'main_pot_cumulative : {self.main_pot_cumulative}')
        print(f'main_pot_confirmed : {self.main_pot_confirmed}')
        print(f'생존자 : {self.survivors}')
        print()

    def test_code_showdown_info(self):
        print("=====================쇼다운 결과=====================")
        print(f'best hands : {self.log_best_hands}')
        print(f'users_ranking : {self.log_users_ranking}')
        print(f'nuts : {self.log_nuts}')
        print()

    def test_code_pot_award_info(self, stk_size):
        print("====================팟 분배 결과====================")
        print(f'올인 유저들의 지분 : {self.main_pot_confirmed}')
        print()
        for id, position in zip(stk_size, self.players):
            stack_size = self.players[position]['stk_size']
            print(f'{position} 의 stk_size 변화 : {stk_size[id]} -> {stack_size}')






