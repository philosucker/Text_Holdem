from fastapi import WebSocket
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
        모든 클라이언트에게 렌더링 요청
        1. 모든 클라이언트의 닉과 포지션
        2. 모든 클라이언트의 스택사이즈 렌더링
        3. 각자 자신의 스타팅 카드
        4. 팟 총액
        '''
        await self._notify_clients_nick_positions()
        await self._notify_clients_stack_sizes()
        await self._notify_clients_starting_cards()
        await self._broadcast_message("Pot Total", self.pot_total)

        # 유저 액선큐 등록
        if self.start_order:
            self.action_queue.append(self.start_order.popleft())
        
        return

    async def _prep_street(self, street_name : str ) -> None:
        
        # 이전 스트릿에서 넘어온 유저만을 대상으로 start_order 재정렬
        await self._initialize_start_order(street_name)

        # 스트릿에서 사용할 인스턴스 변수들 초기화
        await self._initialize_betting_state()
        await self._initialize_action_state()
        await self._initialize_conditions()

        '''
        모든 클라이언트에게 렌더링 요청
        1. 모든 클라이언트의 닉과 포지션
        2. 모든 클라이언트의 스택사이즈 렌더링
        3. 각자 자신의 스타팅 카드
        4. 팟 총액
        '''
        await self._notify_clients_nick_positions()
        await self._notify_clients_stack_sizes()
        await self._notify_clients_starting_cards()
        await self._broadcast_message("Pot Total", self.pot_total)

        # 유저 액선큐 등록
        if self.start_order:
            self.action_queue.append(self.start_order.popleft())

        return
    
    async def _play_street(self, street_name : str ) -> None:

        while self.action_queue:
            '''
            클라이언트에게 렌더링 및 응답 요청
            1. current_player에 해당하는 클라이언트에게 possible_actions 리스트 전달
            2. current_player에 해당하는 클라이언트가 bet, raise, all-in을 할 수 있는 경우 betting_condition 리스트 전달
                self.prev_VALID 유저가 베팅 액션 선택시 베팅 해야하는 최소 금액
                self.prev_TOTAL 유저가 레이즈 액션 선택시 가능한 레이즈 최소 금액
            '''
            current_player = self.action_queue[0]
            possible_actions : list = await self._possible_actions(street_name, current_player)
            for action in possible_actions:
                if action in ['bet', 'raise', 'all-in']:
                    betting_condition = [self.prev_VALID, self.prev_TOTAL]
            message = {"Possible Actions" : possible_actions, "Betting Condition" : betting_condition}
            answer : dict = await self._request_action(current_player, message)

            # 클라이언트에게 전달 받은 응답이 {'call' : None} 이면
            if next(iter(answer)) == "call":
                await self._call(street_name, current_player)
                
            # 클라이언트에게 전달 받은 응답이 {'fold' : None} 이면 
            elif next(iter(answer)) == "fold":
                await self._fold(street_name, current_player)
                
            # 클라이언트에게 전달 받은 응답이 {'check' : None} 이면      
            elif next(iter(answer)) == "check":  # BB 만 가능
                await self._check(street_name, current_player)

             # 클라이언트로부터 전달 받은 응답이 answer = {"bet" : bet_amount} 이면
            elif next(iter(answer)) == "bet": # 플롭부터 가능
                await self._bet(street_name, current_player, answer)

            # 클라이언트로부터 전달 받은 응답이 answer = {"raise" : raised_total} 이면
            elif next(iter(answer)) == "raise":
                await self._raise(street_name, current_player, answer)
                 
            # 클라이언트로부터 전달 받은 응답이 answer = {"all-in" : None} 이면
            elif next(iter(answer)) == "all-in":
                await self._all_in(street_name, current_player)

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
        
        return

    async def _finishing_street(self, street_name : str ) -> None:

        # 사이드팟 생성
        pots = await self._making_side_pots(street_name)
        self.side_pots[street_name]['pots'] = pots

        # 현재 스트릿의 올인 유저 리스트를 전체 올인 리스트에 추가
        for position in self.all_in_users:
            self.all_in_users_total[position] = street_name
       # 현재 스트릿의 폴드 유저 리스트를 전체 폴드 리스트에 추가
        for position in self.fold_users:
            self.fold_users_total[position] = street_name

        # 다음 스트릿으로 넘어가는 유저 목록
        self.survivors.extend(list(self.actioned_queue))

        return
    
    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    SHOWDOWN                                                                      #
    ####################################################################################################################################################
    ####################################################################################################################################################
       
    async def _end_conditions(self, street_name : str ) -> bool:
        
        if len(self.fold_users_total) == self.rings:
            print("Every user fold")
            return 

        # 한 명 빼고 모두 폴드한 경우 = 액션을 마친 유저 숫자가 1명 뿐인 경우
        # 이 때 남은 한명은 올인유저일 수도 있고, 마지막 베팅 유저일 수도 있다.
        if len(self.fold_users_total) == self.rings - 1 or len(self.actioned_queue) == 1:
            if self.actioned_queue and self.check_users:
                self.check_users[0] == self.actioned_queue[0]
                print("All other user fold after first player check")
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
        
        community_cards : list = await self._face_up_community_cards_for_showdown(street_name) 
        user_cards : dict = await self._face_up_user_hand()
        nuts = await self._compare_hand(user_cards, community_cards)

        if self.user_card_open_first:
            '''
            클라이언트에게 렌더링 요청
            스타팅 카드 오픈 렌더링 후
            커뮤니티 카드 오픈 렌더링
            '''
            message = {"User Cards" : user_cards, "Community Cards Open Order" : community_cards}
            await self._broadcast_message("User Cards Open First", message)

        elif self.table_card_open_first and street_name != 'river':
            if self.table_card_open_only:
                '''
                클라이언트에게 렌더링 요청
                커뮤니티 카드 오픈 렌더링 
                '''            
                await self._broadcast_message("Community Cards Open Order", community_cards)
            '''
            클라이언트에게 렌더링 요청
            커뮤니티 카드 오픈 먼저 렌더링 후
            유저의 액션 순서대로 스타팅 카드 오픈 렌더링
            '''
            await self._broadcast_message("Table Cards Open First", community_cards)
            user_cards_open_order = {position: user_cards[position] for position in self.actioned_queue if position in user_cards}
            await self._broadcast_message("User Cards Open Order", user_cards_open_order)
        
        elif street_name == 'river':
            if self.river_all_check:
                '''
                클라이언트에게 렌더링 요청
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
                클라이언트에게 렌더링 요청
                리버에서 마지막으로 베팅액션을 한 클라이언트부터 딜링 방향으로 카드 오픈
                '''
                user_cards_open_order = {position: user_cards[position] for position in self.actioned_queue if position in user_cards}
                await self._broadcast_message("User Cards Open Order", user_cards_open_order)

        return nuts

    async def _pot_award(self, nuts : dict, street_name : str, version = 'normal') -> None:

        if version == 'normal':
            await self._side_pots(nuts, street_name)

        elif version == 'experimental':
            await self._ratio_using_ranking(nuts, street_name)
        
        elif version == 'hybrid':
            await self._side_pots_using_ranking(nuts, street_name)

        return

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
            await self._pot_award(nuts, street_name)
            return
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
            await self._pot_award(nuts, street_name)
            return
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
            await self._pot_award(nuts, street_name)
            return
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
            await self._pot_award(nuts, street_name)
            return
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

    '''
    게임 중 연결이 끊어진 클라이언트가 dealer 서버 웹소켓에 재접속 한 경우
    DealerManager의 add_connection에서 dealer.reconnecion_handler(reconnection) 을 호출해준다.
    '''
    async def reconnection_handler(self, reconnection : dict[str, WebSocket]) -> None:
        nick, websocket = list(reconnection.items())[0]
        self.connections[nick] = websocket





