from src import PreInitializer
from collections import deque

rings = 6  # robby 에서 전달 받음
user_id_list = ['1', '2', '3', '4', '5', '6'] # robby 에서 전달 받음
stakes = "low"   # robby 에서 전달 받음
stk_size = {'1' : 110, '2' : 120, '3' : 130, '4' : 140, '5' : 150, '6' : 160}  # SQL DB에서 전달 받음


class Dealer(PreInitializer):

    def __init__(self, user_id_list, stk_size, rings, stakes):
        super().__init__(user_id_list, stk_size, rings, stakes)
        
        if rings == 6:
            self.start_order = deque(["UTG", "HJ", "CO", "D", "SB", "BB"])
        elif rings == 9:
            self.start_order = deque(['UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D', 'SB', 'BB'])

        self.action_queue = deque([])
        self.actioned_queue = deque([])
        self.all_in_users = []
        self.fold_users = []

        self.attack_flag = True # only only and just once bet, raise, all-in is True # 턴부터는 False로 초기화

        self.survivors = [] # 다음 스트릿으로 갈 생존자 리스트
        self.check_list = []
        
        self.raised_total = 0 # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
        self.all_in_amount = 0   # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
        self.bet_amount = 0 # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
         
        self.LPFB = self.BB # the largest prior full bet
        self.prev_VALID = self.BB  # 콜시 유저의 스택에 남아 있어야 하는 최소 스택 사이즈의 기준
        self.prev_TOTAL = self.prev_VALID + self.LPFB # 레이즈시 유저의 스택에 남아있어야 하는 최소 스택 사이즈의 기준

        self.pot_change = [self.main_pot]
    
    def preFlop(self):

        # 최초로 액션할 유저를 등록. 필요시 유저가 응답 가능한지 확인하고 불가능하면 다음 유저에게 물어보는 루프로 바꿀 것
        self.action_queue.append(self.start_order.popleft())

        while self.action_queue:
            current_player = self.action_queue[0]                     
            
            if end_condition:
                if len(self.actioned_queue) == rings - 1 and self.raised_total == 0: # BB 구현 및 BB check 구현, 프리플롭에서만 사용
                    if self.attack_flags is True and self.prev_TOTAL <= self.players[current_player][stk_size]:
                        possible_actions = ["check", "raise", "fold", "all-in"]
                    elif self.attack_flags is True and self.prev_VALID <= self.players[current_player][stk_size] < self.prev_TOTAL:
                        possible_actions = ["check", "fold", "short-all-in"]
                    elif self.attack_flags is True and self.players[current_player][stk_size] < self.prev_VALID:
                        possible_actions = ["fold", "short-all-in"]
                    else:
                        pass
            # attacked
            if self.attack_flags is True and self.prev_TOTAL <= self.players[current_player][stk_size]: 
                possible_actions = ["call", "raise", "fold", "all-in"]
            # attacked
            elif self.attack_flags is True and self.prev_VALID <= self.players[current_player][stk_size] < self.prev_TOTAL: 
                possible_actions = ["call", "fold", "short-all-in"]
            # attacked
            elif self.attack_flags is True and self.players[current_player][stk_size] < self.prev_VALID:
                possible_actions = ["fold", "short-all-in"]
            
            else:
                pass

            # current_player에 해당하는 클라이언트에게 possible_actions 전달, 응답 기다림       
            answer = input() # "레이즈는 {"raise" : raised_total} 형식으로. 

            if answer == "call":
                # 클라이언트에게 전달 받은 응답이 call 이면
                self.actioned_queue.append(self.action_queue.popleft())

                self.main_pot += self.prev_VALID
                self.pot_change.append(self.prev_VALID) # 팟 변화량 업데이트

                self.players[current_player]["stk_size"] -= self.prev_VALID
                # 모든 클라이언트들에게 다음을 요청
                    # 콜한 클라이언트의 스택 사이즈를 self.prev_VALID 만큼 차감한 결과로 렌더링
                    # 메인팟 사이즈를 prev_VALID을 더한 결과로 렌더링              

            elif answer == "fold":
                # 클라이언트에게 전달 받은 응답이 fold 면 
                self.fold_users.append(self.action_queue.popleft())
                pass # 메인팟 사이드팟 관련 구현 필요한지?

            elif next(iter(answer)) == "raise":
                # 클라이언트로부터 전달 받은 응답이 answer = {"raise" : raised_total} 이면
                    # raised_total : 클라이언트에게서 전달받은 레이즈 액수 (레이즈 액수는 total을 의미.)

                # 액션큐 처리. 올인/벳 동일
                if self.actioned_queue is not None:
                    for actor in self.actioned_queue:
                        self.start_order.append(actor)
                    self.actioned_queue = deque([])
                    self.actioned_queue.append(self.action_queue.popleft())
                else:
                    self.actioned_queue.append(self.action_queue.popleft())
                
                self.raised_total = answer["raise"]

                self.LPFB = self.raised_total - self.prev_VALID # LPFB 업데이트
                self.prev_VALID = self.raised_total # prev_VALID 업데이트
                self.prev_TOTAL = self.LPFB + self.prev_VALID # prev_TOTAL 업데이트

                self.main_pot += self.raised_total # 메인팟 업데이트

                self.pot_change.append(self.raised_total) # 팟 변화량 업데이트
                self.players[current_player]['stk_size'] -= self.raised_total

                # 모든 클라이언트들에게 다음을 요청
                    # 레이즈한 클라이언트의 스택 사이즈를 raised_total 만큼 차감한 결과로 렌더링
                    # 메인팟 사이즈를 raised_total을 더한 결과로 렌더링

            elif next(iter(answer)) == "all-in":
                # 클라이언트로부터 전달 받은 응답이 answer = {"all-in" : all_in_amount} 이면
                    # all_in_amount : 클라이언트에게서 전달받은 올인액수

                # 모든 클라이언트들에게 다음을 요청
                    # 올인한 클라이언트에게 올인 버튼 렌더링(지속형 이벤트)

                # 액션큐 처리. 레이즈/벳 동일
                if self.actioned_queue is not None:
                    for actor in self.actioned_queue:
                        self.start_order.append(actor)
                    self.actioned_queue = deque([])
                    self.all_in_users.append(self.action_queue.popleft())
                else:
                    self.all_in_users.append(self.action_queue.popleft())
                
                self.all_in_amount = answer['all-in']

                if self.prev_TOTAL <= self.all_in_amount:
                    self.LPFB = self.all_in_amount - self.prev_VALID
                    self.VALID = self.all_in_amount
                    self.prev_TOTAL = self.VALID + self.LPFB

                elif self.prev_VALID <= self.all_in_amount < self.prev_TOTAL:
                    self.prev_VALID = self.all_in_amount
                    self.prev_TOTAL = self.prev_VALID + self.LPFB

                elif self.all_in_amount < self.prev_VALID:
                    pass # 구현 불필요

                self.main_pot += self.all_in_amount # 메인팟 업데이트
                self.pot_change.append(self.all_in_amount) # 팟 변화량 업데이트

                self.players[current_player]['stk_size'] -= self.all_in_amount
                # 모든 클라이언트들에게 다음을 요청
                    # 올인한 클라이언트의 스택 사이즈를 self.all_in_amount 만큼 차감한 결과로 렌더링
                    # 메인팟 사이즈를 self.all_in_amount을 더한 결과로 렌더링
            

            elif answer == "check":  # BB 만 가능
                if current_player == "BB":
                    break


            if len(self.start_order) == 0:
                break
            else:
                self.action_queue.append(self.start_order.popleft())

        # 다음 스트릿으로 갈 플레이어 survivors 리스트 리턴
        self.survivors.extend(self.all_in_users)
        self.survivors.extend(self.actioned_queue)
        # 메인팟, 사이드팟 리턴
        # 나머지 모든 인스턴스 변수 초기화

        return self.survivors
    


    def Flop(self):

        # 최초로 액션할 유저를 등록. 필요시 유저가 응답 가능한지 확인하고 불가능하면 다음 유저에게 물어보는 루프로 바꿀 것
        self.action_queue.append(self.start_order.popleft())

        while self.action_queue:
            current_player = self.action_queue[0]                     
            
            if end_condition:
                pass

            # not yet attacked
            if self.attack_flags is False and self.prev_TOTAL <= self.players[current_player][stk_size]:
                possible_actions = ["bet", "check", "raise", "fold", "all-in"] 

            # not yet attacked
            elif self.attack_flags is False and self.prev_VALID <= self.players[current_player][stk_size] < self.prev_TOTAL: 
                possible_actions = ["bet", "check", "fold", "short-all-in"]
            
            # not yet attacked
            elif self.attack_flags is False and self.players[current_player][stk_size] < self.prev_VALID:
                possible_actions = ["check", "fold", "short-all-in"]

            # attacked
            elif self.attack_flags is True and self.prev_TOTAL <= self.players[current_player][stk_size]: 
                possible_actions = ["call", "raise", "fold", "all-in"]
            # attacked
            elif self.attack_flags is True and self.prev_VALID <= self.players[current_player][stk_size] < self.prev_TOTAL: 
                possible_actions = ["call", "fold", "short-all-in"]
            # attacked
            elif self.attack_flags is True and self.players[current_player][stk_size] < self.prev_VALID:
                possible_actions = ["fold", "short-all-in"]
            
            else:
                pass

            # current_player에 해당하는 클라이언트에게 possible_actions 전달, 응답 기다림       
            answer = input() # "레이즈는 {"raise" : raised_total} 형식으로. 

            if answer == "call":
                # 클라이언트에게 전달 받은 응답이 call 이면

                if current_player in self.check_list:
                    self.check_list.remove(current_player)

                self.actioned_queue.append(self.action_queue.popleft())

                self.main_pot += self.prev_VALID
                self.pot_change.append(self.prev_VALID) # 팟 변화량 업데이트

                self.players[current_player]["stk_size"] -= self.prev_VALID
                # 모든 클라이언트들에게 다음을 요청
                    # 콜한 클라이언트의 스택 사이즈를 self.prev_VALID 만큼 차감한 결과로 렌더링
                    # 메인팟 사이즈를 prev_VALID을 더한 결과로 렌더링              

            elif answer == "fold":
                # 클라이언트에게 전달 받은 응답이 fold 면 
                if current_player in self.check_list:
                    self.check_list.remove(current_player)

                self.fold_users.append(self.action_queue.popleft())
                pass # 메인팟 사이드팟 관련 구현 필요한지?

            elif next(iter(answer)) == "raise":
                # 클라이언트로부터 전달 받은 응답이 answer = {"raise" : raised_total} 이면
                    # raised_total : 클라이언트에게서 전달받은 레이즈 액수 (레이즈 액수는 total을 의미.)

                if current_player in self.check_list:
                    self.check_list.remove(current_player)

                # 액션큐 처리. 올인/벳 동일
                if self.actioned_queue is not None:
                    for actor in self.actioned_queue:
                        self.start_order.append(actor)
                    self.actioned_queue = deque([])
                    self.actioned_queue.append(self.action_queue.popleft())
                else:
                    self.actioned_queue.append(self.action_queue.popleft())
                
                self.raised_total = answer["raise"]

                self.LPFB = self.raised_total - self.prev_VALID # LPFB 업데이트
                self.prev_VALID = self.raised_total # prev_VALID 업데이트
                self.prev_TOTAL = self.LPFB + self.prev_VALID # prev_TOTAL 업데이트

                self.main_pot += self.raised_total # 메인팟 업데이트

                self.pot_change.append(self.raised_total) # 팟 변화량 업데이트
                self.players[current_player]['stk_size'] -= self.raised_total

                self.attack_flag = True  

                # 모든 클라이언트들에게 다음을 요청
                    # 레이즈한 클라이언트의 스택 사이즈를 raised_total 만큼 차감한 결과로 렌더링
                    # 메인팟 사이즈를 raised_total을 더한 결과로 렌더링

            elif next(iter(answer)) == "all-in":
                # 클라이언트로부터 전달 받은 응답이 answer = {"all-in" : all_in_amount} 이면
                    # all_in_amount : 클라이언트에게서 전달받은 올인액수
                
                if current_player in self.check_list:
                    self.check_list.remove(current_player)

                # 모든 클라이언트들에게 다음을 요청
                    # 올인한 클라이언트에게 올인 버튼 렌더링(지속형 이벤트)

                # 액션큐 처리. 레이즈/벳 동일
                if self.actioned_queue is not None:
                    for actor in self.actioned_queue:
                        self.start_order.append(actor)
                    self.actioned_queue = deque([])
                    self.all_in_users.append(self.action_queue.popleft())
                else:
                    self.all_in_users.append(self.action_queue.popleft())
                
                self.all_in_amount = answer['all-in']

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

                self.main_pot += self.all_in_amount # 메인팟 업데이트
                self.pot_change.append(self.all_in_amount) # 팟 변화량 업데이트

                self.players[current_player]['stk_size'] -= self.all_in_amount

                self.attack_flag = True  

                # 모든 클라이언트들에게 다음을 요청
                    # 올인한 클라이언트의 스택 사이즈를 self.all_in_amount 만큼 차감한 결과로 렌더링
                    # 메인팟 사이즈를 self.all_in_amount을 더한 결과로 렌더링
            
            elif next(iter(answer)) == "bet":
                # 클라이언트로부터 전달 받은 응답이 answer = {"bet" : bet_amount} 이면
                    # bet_amount : 클라이언트에게서 전달받은 베팅액수

                if current_player in self.check_list:
                    self.check_list.remove(current_player)

                # 액션큐 처리. 올인/레이즈 동일
                if self.actioned_queue is not None:
                    for actor in self.actioned_queue:
                        self.start_order.append(actor)
                    self.actioned_queue = deque([])
                    self.actioned_queue.append(self.action_queue.popleft())
                else:
                    self.actioned_queue.append(self.action_queue.popleft())

                self.bet_amount = answer['bet']

                self.LPFB = self.bet_amount
                self.VALID = self.bet_amount
                self.prev_TOTAL = self.VALID + self.LPFB

                self.main_pot += self.bet_amount # 메인팟 업데이트
                self.pot_change.append(self.bet_amount) # 팟 변화량 업데이트

                self.players[current_player]['stk_size'] -= self.bet_amount

                self.attack_flag = True 

                # 모든 클라이언트들에게 다음을 요청
                    # 베팅한 클라이언트의 스택 사이즈를 self.bet_amount 만큼 차감한 결과로 렌더링
                    # 메인팟 사이즈를 self.bet_amount을 더한 결과로 렌더링


            elif answer == "check":
                if len(self.check_list) == len(self.survivors):  # check는 flop, turn, river 에서만 구현
                    break
                    # 모든 클라이언트에게 다음을 요청
                        # 다음 스트릿으로 이동
                else:
                    self.actioned_queue.append(current_player)
                    self.check_list.append(self.action_queue.popleft())

                    # 모든 클라이언트들에게 다음을 요청
                        # 체크한 플레이어가 체크했음을 렌더링
                    




            if len(self.start_order) == 0:
                break
            else:
                self.action_queue.append(self.start_order.popleft())

        # 다음 스트릿으로 갈 플레이어 survivors 리스트 리턴
        self.survivors.extend(self.all_in_users)
        self.survivors.extend(self.actioned_queue)
        # 메인팟, 사이드팟 리턴
        # 나머지 모든 인스턴스 변수 초기화

        return self.survivors
    



    

    def showdown(self):
        '''
        올인이 아닌 쇼다운
            마지막 스트릿에 베팅이 있었던 경우
                라스트 어그레서부터 딜링방향으로 오픈                  
            마지막 스트릿에 베팅이 없었던 경우
                마지막 스트릿의 첫번째 액션 차례였던 플레이어부터 딜링방향으로 오픈
        올인이 있었던 쇼다운
            모든 핸드는 테이블링 된다
        '''

if __name__ == '__main__':

    dealer = Dealer(user_id_list, stk_size, rings, stakes)
    print(dealer.LPFB)