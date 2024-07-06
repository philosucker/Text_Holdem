from dealer import Dealer

rings = 6  # robby 에서 전달 받음
user_id_list = ['1', '2', '3', '4', '5', '6'] # robby 에서 전달 받음
stakes = "low"   # robby 에서 전달 받음
# stk_size = {'1' : 100, '2' : 100, '3' : 100, '4' : 100, '5' : 100, '6' : 100}  # SQL DB에서 전달 받음

# short situation
# 1 : UTG, 2 : HJ, 3 : CO, 4 : D, 5 : SB, 6 : BB
stk_size = {'1' : 50, '2' : 70, '3' : 200, '4' : 200, '5' : 500, '6' : 1000}  # SQL DB에서 전달 받음


dealer = Dealer(user_id_list, stk_size, rings, stakes)
dealer.go_street(stk_size)

