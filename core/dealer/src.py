import random
from itertools import combinations
from collections import OrderedDict, defaultdict, Counter, deque

class Base:
    
    def __init__(self, user_id_list : list, stk_size : list, rings : int, stakes : str) -> None:

        # from floor
        self.user_id_list = user_id_list
        self.stk_size = stk_size
        self.rings = rings
        self.stakes = stakes

        # initialize self.players
        self.shuffled_deck = self._shuffle_deck()
        self.players, self.stub, self.user2pos = self._initialize_players(user_id_list, stk_size, self.shuffled_deck)
        
        # initialize street
        self.start_order : deque = None
        self.SB, self.BB = self._blind_post()
        self._initialize_betting_state()
        self._initialize_action_state()
        self._initialize_conditions()

        # for end_condition, finishing_street, face_up_user_hand
        self.all_in_users_total = OrderedDict()

        # for end_condition, finishing_street, check_connection
        self.fold_users_total = OrderedDict()
        self.log_community_cards = {"burned" : [], "flop" : [], "turn" : [], "river" : [], "table_cards" : []} 

        # for showdown
        self.card_rank_order = "23456789TJQKA"
        self.hand_power = {
            "royal_straight_flush": 10, "straight_flush": 9, "quads": 8, "full_house": 7,
            "flush": 6, "straight": 5, "set": 4, "trips": 4, "two_pair": 3, "one_pair": 2,
            "high_card": 1
        }
        self.log_nuts = {}

        # for pot awarding
        self.pot_total = 0 
        self.side_pots = defaultdict(dict)
        self.side_pots["pre_flop"] = {}
        self.side_pots["flop"] = {}
        self.side_pots["turn"] = {}
        self.side_pots["river"] = {}

        # for logging
        self.log_best_hands = OrderedDict()
        self.log_users_ranking = None 
        self.log_pot_change = [self.pot_total]
        self.log_hand_actions = {"pre_flop" : [], "flop" : [], "turn" : [], "river" : []}    

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                            INITIALIZE CARDS, PLAYERS                                                             #
    ####################################################################################################################################################
    #################################################################################################################################################### 
   
    def _get_positions(self, rings : int) -> list:
        
        if rings == 6:
            return ["UTG", "HJ", "CO", "D", "SB", "BB"]
        elif rings == 9:
            return ['UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D', 'SB', 'BB']
        else:
            raise ValueError("Invalid number of rings. Must be 6 or 9.")

    def _shuffle_positions(self, positions : list) -> list: 
        
        shuffled_positions = random.sample(positions, len(positions))
        
        return shuffled_positions

    def _shuffle_deck(self) -> list:

        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        suits = ['H', 'D', 'C', 'S']  # H: 하트, D: 다이아몬드, C: 클로버, S: 스페이드
        deck = [rank + suit for suit in suits for rank in ranks]
        shuffled_deck = random.sample(deck, len(deck))

        return shuffled_deck
    
    def _dealing_cards(self, players : dict, shuffled_deck : list) -> tuple[dict, list]:
        for _ in range(2):
            for position in players:
                players[position]['starting_cards'].append(shuffled_deck.pop(0))

        return players, shuffled_deck

    def _initialize_players(self, user_id_list : list, stk_size : list, shuffled_deck : list) -> tuple[dict, list, dict]:
        positions = self._get_positions(self.rings) # 테스트 코드
        # positions = self._shuffle_positions(self._get_positions(self.rings)) # 실제코드
        user2pos = {user_id: position for position, user_id in zip(positions, user_id_list)}
        players = {position: {
            "user_id": user_id,
            "stk_size": stk_size[user_id],
            "starting_cards": [],
            "actions": {
                street: {"action_list": [], 
                        "pot_contribution": {"call": [0], "raise": [0], "all-in": [0], "bet": [0]},
                        "betting_size_total": {"call": [0], "raise": [0], "all-in": [0], "bet": [0]},
                        }
                for street in ["pre_flop", "flop", "turn", "river"]
            }
        } for position, user_id in zip(positions, user_id_list)}
        
        players, stub = self._dealing_cards(players, shuffled_deck)

        return players, stub, user2pos

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                      ACTION                                                                      #
    ####################################################################################################################################################
    ####################################################################################################################################################
    
    def _possible_actions(self, street_name : str, current_player :str) -> list:

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
       
    def _bet(self, street_name : str, current_player : str, answer :dict) -> None:

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
        self.pot_total += self.bet_amount # 팟총액 업데이트
        
        self.log_pot_change.append(self.prev_VALID) # 팟 변화량 업데이트

        # 로그 업데이트
        betting_size_total["bet"].append(self.prev_VALID)
        pot_contribution["bet"].append(self.prev_VALID)
        action_list.append("bet")

        self.attack_flag = True 


        # 현재 베팅 액션으로 인해 스택사이즈가 0이 되었다면 해당 베팅은 올인으로 간주
        if self.players[current_player]["stk_size"] == 0:
            self.all_in_users.append(self.action_queue.popleft())

        # 액션큐 처리. 벳의 경우 자기 앞에 액션은 체크를 한 사람 밖에 없다.
        if self.actioned_queue:
            self.start_order.extend(self.actioned_queue)
            self.actioned_queue.clear()
        
        if self.action_queue:
            self.actioned_queue.append(self.action_queue.popleft())

        '''
        모든 클라이언트들에게 다음을 요청
        베팅한 클라이언트의 스택 사이즈를 self.bet_amount 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 self.bet_amount을 더한 결과로 렌더링
        '''
    
    def _call(self, street_name : str, current_player : str) -> None:

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
        self.pot_total += call_amount # 팟 총액 업데이트

        self.log_pot_change.append(self.prev_VALID)  # 팟 변화량 업데이트
 

        # 로그 업데이트
        betting_size_total["call"].append(self.prev_VALID)
        pot_contribution["call"].append(call_amount)
        action_list.append("call")

        # 현재 콜 액션으로 인해 스택사이즈가 0이 되었다면 해당 콜은 올인으로 간주
        if self.players[current_player]["stk_size"] == 0:
            self.all_in_users.append(self.action_queue.popleft())
        else:
            self.actioned_queue.append(self.action_queue.popleft())

        '''
        모든 클라이언트들에게 다음을 요청
        콜한 클라이언트의 스택 사이즈를 self.prev_VALID 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 prev_VALID을 더한 결과로 렌더링
        '''

    def _raise(self, street_name : str, current_player : str, answer : dict) -> None:

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
        self.pot_total += raise_amount # 팟 총액 업데이트

        self.log_pot_change.append(self.prev_VALID)  # 팟 변화량 업데이트

        # 로그 업데이트
        betting_size_total["raise"].append(self.prev_VALID)
        pot_contribution["raise"].append(raise_amount)
        action_list.append("raise")

        self.attack_flag = True
        
        self.raise_counter += 1

        # 현재 레이즈 액션으로 인해 스택사이즈가 0이 되었다면 해당 레이즈는 올인으로 간주
        if self.players[current_player]["stk_size"] == 0:
            self.all_in_users.append(self.action_queue.popleft())

        # 액션큐 처리.
        if self.actioned_queue:
            self.start_order.extend(self.actioned_queue)
            self.actioned_queue.clear()
        
        if self.action_queue:
            self.actioned_queue.append(self.action_queue.popleft())
        
        '''
        모든 클라이언트들에게 다음을 요청
        레이즈한 클라이언트의 스택 사이즈를 raised_total 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 raised_total을 더한 결과로 렌더링
        '''
    
    def _all_in(self, street_name : str, current_player : str) -> None:

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
            elif self.prev_VALID < self.all_in_amount < self.prev_TOTAL:
                self.prev_VALID = self.all_in_amount
                self.prev_TOTAL = self.prev_VALID + self.LPFB
            # 올인 금액이 현재 콜해야 하는 금액과 같다면 해당 올인은 콜로 간주
            elif self.all_in_amount <= self.prev_VALID:
                self.reorder_flag = False

        self.players[current_player]["stk_size"] -= self.all_in_amount # 스택 사이즈 업데이트
        self.pot_total += self.all_in_amount # 팟 총액 업데이트
      
        self.log_pot_change.append(self.all_in_amount)  # 팟 변화량 업데이트

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
        # 현재 올인 금액이 언더콜인 경우 start_order 유지, reorder_flag 디폴트 값으로 변환
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
        
    def _check(self, street_name : str, current_player : str) -> None:
        last_action = "check"
        self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
        self.actioned_queue.append(current_player)
        self.check_users.append(self.action_queue.popleft())
        '''
        모든 클라이언트들에게 다음을 요청
        체크한 플레이어가 체크했음을 렌더링       
        '''
    
    def _fold(self, street_name : str, current_player : str) -> None:

        if current_player in self.check_users: # 체크했던 유저가 폴드할 수도 있다.
            self.check_users.remove(current_player)

        last_action = "fold"
        self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
        self.fold_users.append(self.action_queue.popleft())

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                AUXILIARY SHOWDOWN                                                                #
    ####################################################################################################################################################
    ####################################################################################################################################################
    
    def _face_up_community_cards(self, street_name : str) -> list: 

        self.log_community_cards['burned'].append(self.stub.pop(0)) # 버닝
        if street_name == 'flop':
            for _ in range(3):
                self.log_community_cards[street_name].append(self.stub.pop(0))
        else:
            self.log_community_cards[street_name].append(self.stub.pop(0))

        return self.log_community_cards[street_name]
    
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

        self.log_community_cards["table_cards"] = self.log_community_cards["flop"] + self.log_community_cards["turn"] + self.log_community_cards["river"]
        community_cards: list = self.log_community_cards["table_cards"]

        return community_cards
    
    def _face_up_user_hand(self) -> dict:

        user_hand = dict()
        all_user = [position for position in self.all_in_users_total] + list(self.actioned_queue)
        for position in all_user:
            starting_cards = self.players[position]['starting_cards']
            user_hand[position] = starting_cards

        return user_hand

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

        # live hands의 베스트 핸드를 랭크 순위대로 정렬하여 users_ranking 리스트 작성
        self.log_users_ranking = self._users_ranking()

        nuts = self.log_nuts

        return nuts
    
    def _make_best_hands(self, pocket_cards : list, community_cards : list) -> dict:

        best_rank_name = None
        best_hand = None
        best_rank_value = 0
        best_hands_dict = defaultdict(list)
        live_hands = pocket_cards + community_cards

        for combo in combinations(live_hands, 5):
            rank_name, hand = self._classify_hand(list(combo), pocket_cards)
            rank_value = self.hand_power[rank_name]
            if rank_value > best_rank_value:
                best_rank_name = rank_name
                best_rank_value = rank_value
                best_hands_dict[rank_name] = [hand]
            elif rank_value == best_rank_value:
                best_hands_dict[rank_name].append(hand)

        # 가장 높은 핸드 조합 선택
        best_hand = max(best_hands_dict[best_rank_name], key=lambda hand: [self._card_rank(card) for card in hand])
        remaining_cards = [card for card in live_hands if card not in best_hand]
        best_kicker = sorted(remaining_cards, key=self._card_rank, reverse=True)

        kicker_mapping = {
            "one_pair": 3,
            "two_pair": 1,
            "trips": 2,
            "quads": 1 if all(card in community_cards for card in best_hand) else 0
        }

        best_kicker = best_kicker[:kicker_mapping.get(best_rank_name, 0)]

        return {best_rank_name: best_hand, "kicker": best_kicker}

    def _classify_hand(self, cards : list, pocket_cards : list) -> tuple[str, list]:

        def _flush(cards):
                suits = [card[1] for card in cards]
                return len(set(suits)) == 1

        def _straight(cards):
            ranks = sorted(set(self._card_rank(card) for card in cards), reverse=True)
            for i in range(len(ranks) - 4):
                if ranks[i] - ranks[i + 4] == 4:
                    return True
            return False

        cards = sorted(cards, key=self._card_rank, reverse=True)
        ranks = [card[0] for card in cards]
        rank_counts = Counter(ranks)
        counts = sorted(rank_counts.values(), reverse=True)

        made_flush = _flush(cards)
        made_straight = _straight(cards)

        if made_flush and made_straight:
            if ranks[:5] == ['A', 'K', 'Q', 'J', 'T']:
                return "royal_straight_flush", cards[:5]
            return "straight_flush", cards[:5]
        
        if counts == [4, 1]:
            quads_rank = next(rank for rank, count in rank_counts.items() if count == 4)
            quads = [card for card in cards if card[0] == quads_rank]
            return "quads", quads

        if counts == [3, 2]:
            three_of_a_kind_rank = next(rank for rank, count in rank_counts.items() if count == 3)
            pair_rank = next(rank for rank, count in rank_counts.items() if count == 2)
            three_of_a_kind = [card for card in cards if card[0] == three_of_a_kind_rank]
            pair_cards = [card for card in cards if card[0] == pair_rank]
            return "full_house", three_of_a_kind + pair_cards[:2]

        if made_flush:
            return "flush", cards[:5]

        if made_straight:
            straight = sorted(set(cards), key=self._card_rank, reverse=True)
            for i in range(len(straight) - 4):
                if self._card_rank(straight[i]) - self._card_rank(straight[i + 4]) == 4:
                    return "straight", straight[i:i + 5]

        if counts == [3, 1, 1]:
            three_of_a_kind_rank = next(rank for rank, count in rank_counts.items() if count == 3)
            three_of_a_kind = [card for card in cards if card[0] == three_of_a_kind_rank]
            if all(card in pocket_cards for card in three_of_a_kind[:2]):
                return "set", three_of_a_kind
            return "trips", three_of_a_kind

        if counts == [2, 2, 1]:
            pair_rank = sorted((rank for rank, count in rank_counts.items() if count == 2), key=self.card_rank_order.index, reverse=True)
            two_pair = [card for card in cards if card[0] in pair_rank]
            return "two_pair", two_pair

        if counts == [2, 1, 1, 1]:
            pair_rank = next(rank for rank, count in rank_counts.items() if count == 2)
            one_pair = [card for card in cards if card[0] == pair_rank]
            return "one_pair", one_pair

        return "high_card", cards[:5]

    def _card_rank(self, card : str) -> int:
            
            return self.card_rank_order.index(card[0])

    def _resolve_ties(self, nuts_positions : list) -> list:
        if len(nuts_positions) <= 1:
            return nuts_positions

        best_hands = [self.log_best_hands[pos] for pos in nuts_positions]

        # 랭크별 비교할 카드 수 설정
        rank_card_count = {
            "one_pair": 2,
            "two_pair": 4,
            "trips": 3,
            "set": 3,
            "quads": 4,
            "full_house": 5,
            "flush": 5,
            "straight": 5,
            "straight_flush": 5,
            "royal_straight_flush": 5,
            "high_card": 5
        }

        best_rank_name = next(iter(best_hands[0]))
        compare_count = rank_card_count[best_rank_name]

        # 핸드 비교
        for i in range(compare_count):
            max_rank = max(self._card_rank(hand[best_rank_name][i]) for hand in best_hands)
            best_hands = [hand for hand in best_hands if self._card_rank(hand[best_rank_name][i]) == max_rank]
            if len(best_hands) == 1:
                break
        else:
            self.tie_flag = True  # 핸드 비교 후에도 무승부일 때 플래그 설정

        # 핸드가 모두 동일한 경우 키커 비교
        if len(best_hands) > 1 and any(hand['kicker'] for hand in best_hands):
            max_kicker_length = max(len(hand['kicker']) for hand in best_hands)
            for i in range(max_kicker_length):
                max_kicker_rank = max(self._card_rank(hand['kicker'][i]) for hand in best_hands if len(hand['kicker']) > i)
                best_hands = [hand for hand in best_hands if len(hand['kicker']) > i and self._card_rank(hand['kicker'][i]) == max_kicker_rank]
                if len(best_hands) == 1:
                    break
            else:
                self.tie_flag = True  # 키커 비교 후에도 무승부일 때 플래그 설정

        # 최종 넛츠 포지션 반환
        final_nuts_positions = [pos for pos in nuts_positions if self.log_best_hands[pos] in best_hands]

        return final_nuts_positions

    def _users_ranking(self) -> list:
        '''
        종류 : 리턴값이 있는 함수
        기능 : live hands의 쇼다운 결과 무승부는 튜플로 묶은 카드 랭크 순위 오름차순 리스트를 반환
        목적 : 로그 작성용
        '''
        def _hand_key(position):
            '''
            종류 : 리턴값이 있는 함수
            기능 : self.log_best_hands 에서 핸드의 파워가 강력한 순서로 해당 핸드를 가진 유저의 포지션을 내림차순 정렬하기 위해 다음 순서의 비교 기준을 튜플로 반환
            핸드 랭크 이름으로 먼저 비교 후, 같으면 카드 조합의 카드 랭크를 앞에서부터 순서대로 비교 후, 같으면 키커가 있는 경우 키커도 앞에서부터 순서대로 비교
            목적 : _users_ranking 함수에서 유저 카드 랭킹 리스트 정렬 기준을 제공하는 보조함수        
            '''
            hand_name = next(iter(self.log_best_hands[position]))
            hand_combinations = self.log_best_hands[position][hand_name]
            card_ranks = [self._card_rank(card) for card in hand_combinations]
            kicker_ranks = [self._card_rank(card) for card in self.log_best_hands[position].get('kicker', [])]

            return (self.hand_power[hand_name], card_ranks, kicker_ranks)
        
        positions = list(self.log_best_hands.keys())
        users_ranking_list = sorted(positions, key=lambda position: _hand_key(position), reverse=True)
        
        tied_players = []
        ranked_users = []

        previous_key = None
        current_tie_group = []

        for pos in users_ranking_list:
            current_key = _hand_key(pos)

            if previous_key is not None and current_key == previous_key:
                current_tie_group.append(pos)
            else:
                if current_tie_group:
                    tied_players.append(tuple(current_tie_group))
                    current_tie_group = []
                current_tie_group.append(pos)

            previous_key = current_key

        if current_tie_group:
            tied_players.append(tuple(current_tie_group))

        for group in tied_players:
            if len(group) == 1:
                ranked_users.append(group[0])
            else:
                ranked_users.append(group)

        self.log_users_ranking = ranked_users
        users_ranking = deque(ranked_users).copy()

        return users_ranking
    
    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                               AUXILIARY POT AWARD                                                                #
    ####################################################################################################################################################
    ####################################################################################################################################################

    def _find_optimal_combination(self, winner_list: list, contributors: list) -> list:
        '''
        종류 : 리턴값이 있는 함수
        기능 : 무승부가 발생한 경우, 팟이 생성된 스트리트에 한해서, 무승부인 유저들의 리스트와 해당 스트리트의 팟 생성에 기여한 유저 리스트의 교집합을 반환
        목적 : 무승부 유저가 기여한 팟인 경우, 무승부 유저 수에 따라 팟을 등분하여 무승부 유저들에게 분배
        '''            
        winner_set = set(winner_list)
        contributors_set = set(contributors)
        intersection = winner_set & contributors_set
        
        if not intersection:
            return []
        
        return list(intersection)
                        
    def _individual_pot_contribution(self, path : dict.keys):
        '''
        종류 : 리턴값이 있는 함수
        기능 : 개별 팟 기여도를 반환하는 side_pots 함수의 보조함수
        목적 : individual_pot_contribution 를 계산
        '''
        pot_contribution = path
        total_sum = 0
        for key in pot_contribution:
            total_sum += sum(pot_contribution[key])

        return total_sum

    def _sum_individual_pot_contrbutions(self, street_name : str, user_list : str):
        '''
        종류 : 리턴값이 있는 함수
        기능 : 유저들의 팟 기여도 총합을 반환하는 side_pots 함수의 보조함수
        목적 : individual_pot_contribution 을 누적합하여 contribution_total 을 계산
        '''
        users_stake = 0
        for user in user_list:
            user_path = self.players[user]["actions"][street_name]["pot_contribution"]
            user_pot_contribution = self._individual_pot_contribution(user_path)
            users_stake += user_pot_contribution     
        
        return users_stake
            
    def _side_pots(self, street_name : str, ratio = False) -> dict:
        '''
        종류 : 리턴값이 있는 함수
        기능 : 매 스트릿 종료시 메인팟과 사이드 팟들을 계산해서 반환
        목적 : 팟 분배시 사용
        
        users_pot_contribution : 해당 스트릿에서의 모든 유저의 팟 기여도
        contribution_total : users_pot_contribution의 총합
        contributors_ascending_order : 기여도를 기준으로 오름차순으로 포지션을 정렬한 리스트
        pots : 각 메인팟, 사이드팟들의 금액과 해당 팟에 기여한 유저 목록을 저장할 딕셔너리
        pot_number : 사이드 팟 번호를 추적할 변수
        '''

        all_user : list = list(self.actioned_queue) + self.all_in_users + self.fold_users
        users_pot_contribution = {position: self._individual_pot_contribution(self.players[position]["actions"][street_name]["pot_contribution"]) 
                                  for position in all_user}
        self.side_pots[street_name]['users_pot_contributions'] = users_pot_contribution

        contribution_total = self._sum_individual_pot_contrbutions(street_name, all_user)
        self.side_pots[street_name]['contribution_total'] = contribution_total

        self.side_pots[street_name]['pot_total'] = self.pot_total

        if ratio == True:
            for position in all_user:
                self.side_pots[street_name][position] = 0
                user_stake = 0
                user_contribution = users_pot_contribution[position]
                
                for _ , other_contribution in users_pot_contribution.items():
                    user_stake += min(other_contribution, user_contribution)
                
                self.side_pots[street_name]['stake_for_all'][position] = user_stake

        contributors_ascending_order = deque(sorted(
            [position for position, contribution in users_pot_contribution.items() if contribution > 0],
            key=lambda position: users_pot_contribution[position]
        ))

        pots = {}  
        pot_number = 0 

        while contributors_ascending_order:

            min_contribution = users_pot_contribution[contributors_ascending_order[0]]
            current_pot_total = min_contribution * len(contributors_ascending_order)
            contribution_total -= current_pot_total

            if pot_number == 0:
                pot_name = "main_pot"
            else:
                pot_name = f"side_pot_{pot_number}"

            pots[pot_name] = {}
            pots[pot_name]['size'] = current_pot_total
            pots[pot_name]['contributors'] = list(contributors_ascending_order)
            
            contributers = contributors_ascending_order.copy()
            for position in contributers:
                users_pot_contribution[position] -= min_contribution
                if users_pot_contribution[position] == 0:
                    contributors_ascending_order.popleft()
                    users_pot_contribution.pop(position)

            pot_number += 1

        if contribution_total == 0:
            return pots
        else:
            raise ValueError("Sidepot calculation is incorrect.")
    
    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                  AUXILIARY ETC                                                                   #
    ####################################################################################################################################################
    ####################################################################################################################################################

    def _blind_post(self) -> (int):
        '''
        종류 : 상태변경함수
        기능 : 변수 초기화
        목적 : 프리플롭 진행 전 스테이크에 따른 블라인드 값 초기화
        '''
        if self.stakes == "low":
            sb = 1
            bb = 2
        elif self.stakes == "high":
            sb = 2
            bb = 5

        return sb, bb
    
    def _posting_blind(self, street_name: str) -> None:
        '''
        종류 : 상태변경함수
        기능 : 변수 초기화
        목적 : 프리플롭 진행 전 블라인드 포스팅 및 players 딕셔너리에 SB, BB 유저 액션 기록   
        '''
        if self.stakes == "low":
            self.players["SB"]["stk_size"] -= self.SB
            self.players["BB"]["stk_size"] -= self.BB
            self.players["SB"]["actions"][street_name]["betting_size_total"]["bet"].append(self.SB)
            self.players["SB"]["actions"][street_name]["action_list"].append("bet")
            self.players["BB"]["actions"][street_name]["betting_size_total"]["bet"].append(self.BB)
            self.players["BB"]["actions"][street_name]["action_list"].append("bet")
            self.pot_total += (self.SB + self.BB)

    def _initialize_start_order(self, street_name : str) -> None:
        '''
        종류 : 상태변경함수
        기능 : 변수 초기화
        목적 : 스트릿 진행 전 start_order 초기화, 참가 자격이 있는 유저만 start_order 에 등록        
        '''
        if street_name == 'pre_flop':
            if self.rings == 6:
                self.start_order = deque(["UTG", "HJ", "CO", "D", "SB", "BB"])
            elif self.rings == 9:
                self.start_order = deque(['UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D', 'SB', 'BB'])
        else:
            if self.rings == 6:
                self.start_order = deque(["SB", "BB", "UTG", "HJ", "CO", "D"])
            elif self.rings == 9:
                self.start_order = deque(['SB', 'BB', 'UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D'])
            new_order = []
            while self.start_order:
                position = self.start_order.popleft()
                if position in self.survivors:
                    new_order.append(position)
            self.start_order = deque(new_order)

    def _initialize_betting_state(self) -> None:
        '''
        종류 : 상태변경함수
        기능 : 변수 초기화
        목적 : 풀콜, 풀레이즈, 풀올인 여부 판단을 위한 정보 제공

        self.raised_total : 클라이언트로부터 전달받는 데이터, 레이즈 총량
        self.bet_amount : 클라이언트로부터 전달받는 데이터, 벳 금액
        self.all_in_amount : 올인 금액, 플레이어 스택사이즈 조회   
        self.LPFB = self.BB : the largest prior full bet = the last legal increment = minimum raise, 최초 LPFB는 BB
        self.prev_VALID : 콜 액션시 유저의 스택에 남아 있어야 하는 최소 스택 사이즈의 기준
        self.prev_TOTAL = self.prev_VALID + self.LPFB : 레이즈 액션시 유저의 스택에 남아있어야 하는 최소 스택 사이즈의 기준
        '''            
        self.raised_total = 0
        self.bet_amount = 0 
        self.all_in_amount = 0   

        self.LPFB = self.BB 
        self.prev_VALID = self.BB  
        self.prev_TOTAL = self.prev_VALID + self.LPFB

    def _initialize_action_state(self) -> None:
        '''
        종류 : 상태변경함수
        기능 : 리스트 초기화, flag 설정 및 변경
        목적 : 

        self.attack_flag : possible action 을 결정하기 위한 정보 제공
        self.raise_counter : 5번을 초과해 레이즈 할 수 없도록 레이즈 수를 카운트하기 위한 변수 
        self.reorder_flag : 언더콜인 올인 발생시 start_order 재정렬 금지하기 위한 플래그
        '''    
        self.action_queue = deque([])
        self.actioned_queue = deque([])

        self.all_in_users = list()
        self.fold_users = list()
        self.check_users = list()

        self.attack_flag = False # only only and just once bet, raise, all-in is True  # 플롭부터는 False로 초기화
        self.raise_counter = 0 
        self.reorder_flag = True # 

    def _initialize_conditions(self) -> None:
        '''
        종류 : 상태변경함수
        기능 : flag 설정 및 변경
        목적 : 핸드 조기종료, 쇼다운 시 카드 오픈 순서 정보 제공, 스트릿 이동시 live hands 전달

        self.survivors : 다음 스트릿으로 갈 생존자 리스트
        '''
        self.deep_stack_user_counter = 0
        self.short_stack_end_flag = False  # TDA Rule 16 : Face Up for All
        self.user_card_open_first = False # TDA Rule 16 : Face Up for All

        self.table_card_open_first = False
        self.table_card_open_only = False # TDA Rule 18 : Asking to See a Hand

        self.river_all_check = False # TDA Rule : 17 : Non All-In Showdowns and Showdown Order
        self.river_bet_exists = False # TDA Rule : 17 : Non All-In Showdowns and Showdown Order

        self.survivors = list()

    def _check_connection(self, on_user_list : list) -> None:
        '''
        종류 : 상태변경함수
        기능 : 현재 접속중이지 않은 유저들을 fold_users_total 로 이동
        목적 : 접속 중인 유저를 대상으로 하는 연산에서 제외

        on_user_list : 서버에서 전달 받은 현재 접속 중인 클라이언트들의 유저 아이디 리스트
        '''
        connected_users = []
        if on_user_list:
            for on_user in on_user_list:
                connected_users.append(self.user2pos[on_user])
            for position in self.start_order:
                if position not in connected_users:
                    self.fold_users_total[position] = self.start_order.popleft()

