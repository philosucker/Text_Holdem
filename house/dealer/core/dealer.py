from fastapi import WebSocket
import asyncio
from src import Base

class Dealer(Base):

    def __init__(self, table_dict : dict, connections : dict[WebSocket]) -> None:
        super().__init__(table_dict, connections)

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                     STREET                                                                       #
    ####################################################################################################################################################
    ####################################################################################################################################################
    
    async def _prep_preFlop(self, street_name : str) -> None:
        
        await self._initialize_start_order(street_name)
        # SB와 BB의 블라인드 포스팅은 bet으로 간주
        self.attack_flag == True
        await self._posting_blind(street_name)

        '''
        서버 요청 사항
        1. 모든 클라이언트에게 모든 상대방의 닉과 포지션 렌더링 요청
        2. 모든 클라이언트에게 모든 상대방의 스택사이즈 렌더링 요청.
        3. 모든 클라이언트에게 각자 자신의 스타팅 카드 렌더링 요청
        4. 모든 클라이언트에게 팟 총액 렌더링 요청
        '''
        await self._notify_clients_nick_positions()
        await self._notify_clients_stack_sizes()
        await self._notify_clients_starting_cards()
        await self._broadcast_message("Pot Total", self.pot_total)

        await self._check_connection(self.connections.keys())
        # 유저 액선큐 등록
        if self.start_order:
            self.action_queue.append(self.start_order.popleft())

    async def _prep_street(self, street_name : str ) -> None:
        
        # 이전 스트릿에서 넘어온 유저만을 대상으로 start_order 재정렬
        await self._initialize_start_order(street_name)

        # 스트릿에서 사용할 인스턴스 변수들 초기화
        await self._initialize_betting_state()
        await self._initialize_action_state()
        await self._initialize_conditions()

        '''
        서버 요청 사항
        1. 모든 클라이언트에게 모든 상대방의 닉과 포지션 렌더링 요청
        2. 모든 클라이언트에게 모든 상대방의 스택사이즈 렌더링 요청.
        3. 모든 클라이언트에게 각자 자신의 스타팅 카드 렌더링 요청
        4. 모든 클라이언트에게 팟 총액 렌더링 요청
        '''
        await self._notify_clients_nick_positions()
        await self._notify_clients_stack_sizes()
        await self._notify_clients_starting_cards()
        await self._broadcast_message("Pot Total", self.pot_total)

        await self._check_connection(self.connections.keys())
        # 유저 액선큐 등록
        if self.start_order:
            self.action_queue.append(self.start_order.popleft())

    async def _play_street(self, street_name : str ) -> None:

        while self.action_queue:
            '''
            서버 요청 사항 
            시간제한은 클라이언트 쪽에서 구현
            1. current_player에 해당하는 클라이언트에게 possible_actions 리스트 전달, 렌더링 요청
            2. current_player에 해당하는 클라이언트가 bet, raise, all-in을 할 수 있는 경우 betting_condition 리스트 전달, 렌더링 요청
                self.prev_VALID 유저가 베팅 액션 선택시 베팅 해야하는 최소 금액
                self.prev_TOTAL 유저가 레이즈 액션 선택시 가능한 레이즈 최소 금액 렌더링 요청
            '''
            current_player = self.action_queue[0]
            possible_actions : list = await self._possible_actions(street_name, current_player)
            for action in possible_actions:
                if action in ['bet', 'raise', 'all-in']:
                    betting_condition = [self.prev_VALID, self.prev_TOTAL]

            '''
            서버 응답 대기
            현재 액션할 차례인 클라이언트가 서버에 전달한 액션 내용을 서버로부터 받음
            응답 형식 : 딕셔너리 = {액션종류, 베팅금액}
            {'call' : None}, {'fold' : None}, {'check' : None},  {'all-in' : None} 
            {'bet' : bet_amount}, {'raise' : raise_amount} 
            서버로부터 받은 응답을 answer 변수에 할당
            '''

            message = {"Possible Actions" : possible_actions, "Betting Condition" : betting_condition}
            answer : dict = await self._request_action(current_player, message)

            # 클라이언트에게 전달 받은 응답이 call 이면
            if next(iter(answer)) == "call":
                await self._call(street_name, current_player, answer)
                
            # 클라이언트에게 전달 받은 응답이 fold 면 
            elif next(iter(answer)) == "fold":
                await self._fold(street_name, current_player, answer)
                
            # 클라이언트에게 전달 받은 응답이 check 면      
            elif next(iter(answer)) == "check":  # BB 만 가능
                await self._check(street_name, current_player, answer)

             # 클라이언트로부터 전달 받은 응답이 answer = {"bet" : bet_amount} 이면
            elif next(iter(answer)) == "bet": # 플롭부터 가능
                await self._bet(street_name, current_player, answer)

            # 클라이언트로부터 전달 받은 응답이 answer = {"raise" : raised_total} 이면
            elif next(iter(answer)) == "raise":
                await self._raise(street_name, current_player, answer)
                 
            # 클라이언트로부터 전달 받은 응답이 answer = {"all-in" : all_in_amount} 이면
            elif next(iter(answer)) == "all-in":
                await self._all_in(street_name, current_player, answer)

            '''
            모든 클라이언트들에게 다음을 요청
            1. 현재 클라이언트의 액션을 렌더링 
            2. 베팅, 콜, 레이즈, 올인한 클라이언트의 스택 사이즈를 렌더링
            3. 메인팟 사이즈를 렌더링
            '''                
            await self._broadcast_message("Action", answer)
            if not {"check", "fold"} & answer.keys():
                await self._broadcast_message("Stack Size", self.players[current_player]['stk_size'])
                await self._broadcast_message("Pot Size", self.pot_total)
                   
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

    async def _finishing_street(self, street_name : str ) -> None:

        # 사이드팟 생성
        pots = await self._side_pots(street_name)
        self.side_pots[street_name]['pots'] = pots

        # 현재 스트릿의 올인 유저 리스트를 전체 올인 리스트에 추가
        for position in self.all_in_users:
            self.all_in_users_total[position] = street_name
       # 현재 스트릿의 폴드 유저 리스트를 전체 폴드 리스트에 추가
        for position in self.fold_users:
            self.fold_users_total[position] = street_name

        # 다음 스트릿으로 넘어가는 유저 목록
        self.survivors.extend(list(self.actioned_queue))
    
    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    SHOWDOWN                                                                      #
    ####################################################################################################################################################
    ####################################################################################################################################################
       
    async def _end_conditions(self, street_name : str ) -> bool:
        
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
    
    async def _showdown(self, street_name : str) -> dict:
        # 커뮤니티 카드 오픈 순서
        async def _community_cards_open_order(street_name) -> list:
            stages = {
                'pre_flop': [("burned", 0), "flop", ("burned", 1), "turn", ("burned", 2), "river"],
                'flop': [("burned", 1), "turn", ("burned", 2), "river"],
                'turn': [("burned", 2), "river"],
                'river': []
            }
            open_order = []
            for stage in stages.get(street_name, []):
                if isinstance(stage, tuple):
                    open_order.append(self.log_community_cards[stage[0]][stage[1]])
                else:
                    open_order.append(self.log_community_cards[stage])
            return open_order
        
        community_cards : list = await self._face_up_community_cards_for_showdown(street_name) # _face_up_community_cards_for_showdown 호출 후
        community_cards_open_order : list = await _community_cards_open_order(street_name) #_community_cards_open_order 호출되어야 한다. 호출순서 바뀌면 안됨
        
        await self._check_connection(self.connections.keys())

        user_cards : dict = await self._face_up_user_hand()
        nuts = await self._compare_hand(user_cards, community_cards)

        if self.user_card_open_first:
            '''
            서버에 요청
            모든 클라이언트에게 동시에 스타팅 카드 오픈 렌더링 후
            커뮤니티 카드 오픈 렌더링 요청
            '''
            message = {"User Cards" : user_cards, "Community Cards Open Order" : community_cards_open_order}
            await self._broadcast_message("User Cards Open First", message)

        elif self.table_card_open_first and street_name != 'river':
            if self.table_card_open_only:
                '''
                서버에 요청
                모든 클라이언트에 커뮤니티 카드 오픈 렌더링 
                '''            
                await self._broadcast_message("Community Cards Open Order", community_cards_open_order)
            '''
            서버에 요청
            모든 클라이언트에 커뮤니티 카드 오픈 렌더링 후
            유저의 액션 순서대로 스타팅 카드 오픈 렌더링 요청
            '''
            await self._broadcast_message("Table Cards Open First", community_cards_open_order)
            user_cards_open_order = {position: user_cards[position] for position in self.actioned_queue if position in user_cards}
            await self._broadcast_message("User Cards Open Order", user_cards_open_order)
        
        elif street_name == 'river':
            if self.river_all_check:
                '''
                서버에 요청
                리버에서 체크했던 순서대로 클라이언트 카드 오픈
                '''
                user_cards_open_order = {position: user_cards[position] for position in self.check_users if position in user_cards}
                await self._broadcast_message("User Cards Open Order", user_cards_open_order)         

            elif self.river_bet_exists and self.table_card_open_only:
                '''
                카드 오픈과 관련해 아무것도 렌더링하지 않음
                '''
                pass
            elif self.river_bet_exists and not self.table_card_open_only:
                '''
                서버에 요청
                리버에서 마지막으로 베팅액션을 한 클라이언트부터 딜링 방향으로 카드 오픈
                '''
                user_cards_open_order = {position: user_cards[position] for position in self.actioned_queue if position in user_cards}
                await self._broadcast_message("User Cards Open Order", user_cards_open_order)

        return nuts

    async def _pot_award(self, nuts : dict, street_name : str, version : int) -> None:

        if version == 1:
            await self._pot_award_1(nuts, street_name)

        elif version == 2:
            await self._pot_award_2(nuts, street_name)
        
        elif version == 3:
            await self._pot_award_3(nuts, street_name)

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                      HAND                                                                        #
    ####################################################################################################################################################
    ####################################################################################################################################################

    async def _preFlop(self) -> None:
        
        street_name = "pre_flop"
        await self._prep_preFlop(street_name)
        await self._play_street(street_name)
        await self._finishing_street(street_name)
        showdown = await self._end_conditions(street_name)
        if showdown:
            nuts = await self._showdown(street_name)
            await self._pot_award(nuts, street_name, 1)
        else:
            await self._flop()
    
    async def _flop(self) -> None:
        
        street_name = "flop"
        await self._prep_street(street_name)
        await self._play_street(street_name)
        await self._finishing_street(street_name)
        showdown = await self._end_conditions(street_name)
        if showdown:
            nuts = await self._showdown(street_name)
            await self._pot_award(nuts, street_name, 1)
        else:
            await self._turn()
    
    async def _turn(self) -> None:

        street_name = "turn"
        await self._prep_street(street_name)
        await self._play_street(street_name)
        await self._finishing_street(street_name)
        showdown = await self._end_conditions(street_name)
        if showdown:
            nuts = await self._showdown(street_name)
            await self._pot_award(nuts, street_name, 1)
        else:
            await self._river()
    
    async def _river(self) -> None:

        street_name = "river"
        await self._prep_street(street_name)
        await self._play_street(street_name)
        await self._finishing_street(street_name)
        showdown = await self._end_conditions(street_name)
        if showdown:
            nuts = await self._showdown(street_name)
            await self._pot_award(nuts, street_name, 1)
        else:
            raise SystemExit("!!!!!!!!!!!!!!종료조건에 걸리지 않는 상황입니다. 유저들의 액션을 검토해서 종료조건을 수정하거나 추가하세요!!!!!!!!!!!!!!")

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    EXECUTION                                                                     #
    ####################################################################################################################################################
    ####################################################################################################################################################

    async def go_street(self) -> None:
        await self._preFlop()
        game_log = await self._making_game_log()
        return game_log






