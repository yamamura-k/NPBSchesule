from utils import color
from base import Base

import os
import math
import pulp
from matplotlib import pyplot as plt
import japanize_matplotlib


class NPB(Base):

    def __init__(self):
        super().__init__()
        self.lat = 90.38
        self.lon = 111
        self.coordinates = {0:(43.014846,141.410007), 1:(38.256599,140.902609), 2:(33.595211,130.362182),
                3:(35.768479,139.420484), 4:(35.645444,140.031186),5:(34.669359,135.476274),
                6:(35.705471,139.751801), 7:(35.185805,136.947498), 8:(35.67452,139.717083),
                9:(34.721394,135.361594), 10:(34.392028,132.484678), 11:(35.443086,139.64005)}
        self.Teams_name = {0:'日ハ', 1:'楽天', 2:'S B ', 3:'西武', 4:'ロ　', 5:'オリ',
                            6:'巨人', 7:'中日', 8:'ヤク', 9:'阪神',10:'広島',11:'横浜'}
        self.stadium = {0:'札幌ドーム', 1:'日本生命パーク宮城', 2:'福岡ドーム', 3:'メットライフドーム', 4:'ZOZOマリン', 5:'京セラ',
                            6:'東京ドーム', 7:'名古屋ドーム', 8:'神宮球場', 9:'甲子園',10:'MAZDA',11:'横浜スタジアム'}
        self.Teams["p"] = [x for x in range(6)]
        self.Teams["s"] = [x for x in range(6,12)]

        self.W["r"] = [w for w in range(21)]
        self.W["i"] = [0,1,2]
        self.total_game['r'] = 42
        self.total_game['i'] = 6
        self.D = [[0]*12 for _ in range(12)]
    
    def EuclidDistance(self, coord1, coord2):
        dist = math.sqrt(((coord1[0]-coord2[0])*self.lat)**2+((coord1[1]-coord2[1])*self.lon)**2)
        return dist 
    
    def DistMatrix(self):
        K = self.Teams['p']+self.Teams['s']
        for i in K:
            for j in K:
                self.D[i][j] = self.EuclidDistance(self.coordinates[i],self.coordinates[j])


class Solve(NPB):
    def __init__(self):
        super().__init__()

    def RegularGame(self, league, num_of_process=1,option=[]):
        self.DistMatrix()# calc dist mat
        # set local variables
        I = self.Teams[league]
        W = self.W["r"]
        D = self.D

        # declare problem type
        problem = pulp.LpProblem('GameSchesule')

        # set variables
        h = pulp.LpVariable.dicts('home', ([0,1],I,I,W),0,1,'Integer')
        v = pulp.LpVariable.dicts('visitor', ([0,1],I,I,W),0,1,'Integer')
        home = pulp.LpVariable.dicts('new_home', ([0,1],I,I,W),0,1,'Integer')
        vis = pulp.LpVariable.dicts('new_vis', ([0,1],I,I,I,W),0,1,'Integer')
        # set objective function
        problem += pulp.lpSum([D[_from][to]*(home[day][_from][to][w]+vis[day][team][_from][to][w])for _from in I for to in I for w in W for day in [0,1]for team in I])
        
        # set constraints
        for i in I:
            # 総試合数に関する制約
            problem += pulp.lpSum([h[0][i][j][w]+v[0][i][j][w]+h[1][i][j][w]+v[1][i][j][w] for j in I for w in W]) == self.total_game["r"]
            for w in W:
                # 1日あたりの試合数に関する制約
                problem += pulp.lpSum([h[0][i][j][w]+v[0][i][j][w] for j in I]) == 1
                problem += pulp.lpSum([h[1][i][j][w]+v[1][i][j][w] for j in I]) == 1
        
        for team in I:
            for _from in I:
                for to in I:
                    for w in W[1:]:
                        # 非線形な目的関数を線形にするために導入した変数に関する制約                        
                        problem +=(1-pulp.lpSum([h[0][to][j][w]for j in I])-v[1][to][_from][w-1]+home[0][_from][to][w]>=0)
                        problem +=(pulp.lpSum([h[0][to][j][w]for j in I])-home[0][_from][to][w]>=0)
                        problem +=(v[1][to][_from][w-1]-home[0][_from][to][w]>=0)
                        problem +=(1-pulp.lpSum([h[1][to][j][w]for j in I])-v[0][to][_from][w]+home[1][_from][to][w]>=0)
                        problem +=(pulp.lpSum([h[1][to][j][w]for j in I])-home[1][_from][to][w]>=0)
                        problem +=(v[0][to][_from][w]-home[1][_from][to][w]>=0)

                        problem +=(1-v[0][team][to][w]-h[1][_from][team][w-1]+vis[0][team][_from][to][w]>=0)
                        problem +=(v[0][team][to][w]-vis[0][team][_from][to][w]>=0)
                        problem +=(h[1][_from][team][w-1]-vis[0][team][_from][to][w]>=0)
                        problem +=(1-v[1][team][to][w]-h[0][_from][team][w]+vis[1][team][_from][to][w]>=0)
                        problem +=(v[1][team][to][w]-vis[1][team][_from][to][w]>=0)
                        problem +=(h[0][_from][team][w]-vis[1][team][_from][to][w]>=0)
        
        for i in I:
            for j in I:
                for w in W:
                    if i != j:
                        #同じ対戦カードは一週間に一回以下である、という制約
                        problem += (h[0][i][j][w]+v[0][i][j][w]+h[1][i][j][w]+v[1][i][j][w] <= 1)
                    else:
                        # 自チームとの試合は行えない
                        problem += (h[0][i][j][w]+v[0][i][j][w]+h[1][i][j][w]+v[1][i][j][w] == 0)
        for i in I:
            for j in I:
                for w in W[1:]:
                    if i != j:
                        #同じ対戦カードは一週間に一回以下である、という制約
                        problem += (h[0][i][j][w]+v[0][i][j][w]+h[1][i][j][w-1]+v[1][i][j][w-1] <= 1)
                    else:
                        # 自チームとの試合は行えない
                        problem += (h[0][i][j][w]+v[0][i][j][w]+h[1][i][j][w-1]+v[1][i][j][w-1] == 0)    

        for i in I:
            home_total = 0
            vist_total = 0
            for j in I:
                home_game = pulp.lpSum([h[0][i][j][w]+h[1][i][j][w] for w in W])
                visitor_game = pulp.lpSum([v[0][i][j][w]+v[1][i][j][w] for w in W])
                home_total += home_game
                vist_total += visitor_game
                if i != j:
                    # ホームとビジターの試合数を調整するための制約
                    problem += (4 <= home_game <= 5)
                    problem += (4 <= visitor_game <= 5)
                    problem += (8 <= home_game+visitor_game <= 9)
                else:
                    # 自チームとは試合をしない
                    problem += home_game == 0
                    problem += visitor_game == 0
            # トータルでホームゲームとビジターゲームをなるべく同数行う
            problem += home_total-vist_total == 0
    
        # solve this problem
        solver = pulp.PULP_CBC_CMD(msg=1, options=option, threads=num_of_process, maxSeconds=1800)
        status = problem.solve(solver)

        return status, h, v


    def InterLeague(self, num_of_process=1,option=[]):
        # set local variables
        self.DistMatrix()
        D = self.D
        I = self.Teams['p']
        J = self.Teams['s']
        W_I = self.W['i']

        # declare problem type
        problem = pulp.LpProblem('GameSchesule')

        # set variables
        h = pulp.LpVariable.dicts('home', ([0,1],I,J,W_I),0,1,'Integer')
        v = pulp.LpVariable.dicts('visitor', ([0,1],I,J,W_I),0,1,'Integer')
        home = pulp.LpVariable.dicts('new_home', ([0,1],J,I,W_I),0,1,'Integer')
        vis = pulp.LpVariable.dicts('new_vis', ([0,1],I,J,J,W_I),0,1,'Integer')
        home_vis = pulp.LpVariable.dicts('new_home_vis',([0,1],I,J,W_I),0,1,'Integer')

        # set objective function
        obj = [D[_from][to]*home[day][_from][to][w]for _from in J for to in I for w in W_I for day in [0,1]]
        obj += [D[_from][to]*vis[day][team][_from][to][w]for _from in J for to in J for w in W_I for day in [0,1]for team in I]
        obj += [D[_from][to]*home_vis[day][_from][to][w]for _from in I for to in J for w in W_I for day in [0,1]]
        obj = pulp.lpSum(obj)
        problem += obj

        # set constraints
        for i in I:
            # 総試合数
            problem += pulp.lpSum([h[0][i][j][w]+v[0][i][j][w]+h[1][i][j][w]+v[1][i][j][w] for j in J for w in W_I]) == self.total_game["i"]
            for w in W_I:
                # 1日一試合
                # パ・リーグ
                problem += pulp.lpSum([h[0][i][j][w]+v[0][i][j][w] for j in J]) == 1
                problem += pulp.lpSum([h[1][i][j][w]+v[1][i][j][w] for j in J]) == 1
        # セ・リーグ
        for j in J:
            for w in W_I:
                for day in [0,1]:
                    # 1日一試合
                    problem += pulp.lpSum([h[day][i][j][w]+v[day][i][j][w] for i in I]) == 1

        # 非線形な目的関数を線形にするために導入した変数に関する制約 
        for _from in J:
            for to in I:
                for w in W_I[1:]:
                    problem +=(1-pulp.lpSum([h[0][to][j][w]for j in J])-v[1][to][_from][w-1]+home[0][_from][to][w]>=0)
                    problem +=(pulp.lpSum([h[0][to][j][w]for j in J])-home[0][_from][to][w]>=0)
                    problem +=(v[1][to][_from][w-1]-home[0][_from][to][w]>=0)
                    problem +=(1-pulp.lpSum([h[1][to][j][w]for j in J])-v[0][to][_from][w]+home[1][_from][to][w]>=0)
                    problem +=(pulp.lpSum([h[1][to][j][w]for j in J])-home[1][_from][to][w]>=0)
                    problem +=(v[0][to][_from][w]-home[1][_from][to][w]>=0)
        
        for team in I:
            for _from in J:
                for to in J:
                    for w in W_I[1:]:                       
                        problem +=(1-v[0][team][to][w]-v[1][team][_from][w-1]+vis[0][team][_from][to][w]>=0)
                        problem +=(v[0][team][to][w]-vis[0][team][_from][to][w]>=0)
                        problem +=(v[1][team][_from][w-1]-vis[0][team][_from][to][w]>=0)
                        problem +=(1-v[1][team][to][w]-v[0][team][_from][w]+vis[1][team][_from][to][w]>=0)
                        problem +=(v[1][team][to][w]-vis[1][team][_from][to][w]>=0)
                        problem +=(v[0][team][_from][w]-vis[1][team][_from][to][w]>=0)
        
        for _from in I:
            for to in J:
                for w in W_I[1:]:
                    problem +=(1-pulp.lpSum([h[0][_from][j][w]for j in J])-v[1][_from][to][w-1]+home_vis[0][_from][to][w]>=0)
                    problem +=(pulp.lpSum([h[0][_from][j][w]for j in J])-home_vis[0][_from][to][w]>=0)
                    problem +=(v[1][_from][to][w-1]-home_vis[0][_from][to][w]>=0)
                    problem +=(1-pulp.lpSum([h[1][_from][j][w]for j in J])-v[0][_from][to][w]+home_vis[1][_from][to][w]>=0)
                    problem +=(pulp.lpSum([h[1][_from][j][w]for j in J])-home_vis[1][_from][to][w]>=0)
                    problem +=(v[0][_from][to][w]-home_vis[1][_from][to][w]>=0)                    

        # 1週間のうち同一カードは一回のみ
        for i in I:
            for j in J:
                for w in W_I:
                    problem += (h[0][i][j][w]+v[0][i][j][w]+h[1][i][j][w]+v[1][i][j][w] <= 1)

        # 試合数を均等に
        # パ・リーグ
        for i in I:
            hh = 0
            vv = 0
            for j in J:
                home_game = pulp.lpSum([h[0][i][j][w]+h[1][i][j][w] for w in W_I])
                visitor_game = pulp.lpSum([v[0][i][j][w]+v[1][i][j][w] for w in W_I])
                # もう一方のリーグの全チームと一回づつ試合をする
                problem += home_game+visitor_game==1
                hh += home_game
                vv += visitor_game
            problem += hh == 3
            problem += vv == 3

        # セ・リーグ
        for j in J:
            hh = 0
            vv = 0
            for i in I:
                home_game = pulp.lpSum([h[0][i][j][w]+h[1][i][j][w] for w in W_I])
                visitor_game = pulp.lpSum([v[0][i][j][w]+v[1][i][j][w] for w in W_I])
                hh += home_game
                vv += visitor_game
            problem += hh == 3
            problem += vv == 3

        # solve this problem
        solver = pulp.PULP_CBC_CMD(msg=1, options=option, threads=num_of_process, maxSeconds=1800)
        status = problem.solve(solver)

        return status, h, v


class Output(NPB):
    def __init__(self):
        super().__init__()
        self.schesules = {"r":dict(), "i":dict()}
        self.DistMatrix()
        self.dists = dict()
    
    def getSchesule(self, status, h, v, game_type, league='p'):
        if status == 0:
            print('infeasible')
            return
        I = self.Teams[league]
        W = self.W[game_type]
        if game_type == "r":
            J = I                              
        else:
            if league == 'p':
                J = self.Teams["s"]
            else:
                J = self.Teams['p']
        for i in I:
            if i not in self.schesules[game_type].keys():
                self.schesules[game_type][i] = []
                for j in J:
                    for w in W:
                        for day in [0,1]:
                            if h[day][i][j][w].value() == 1:
                                self.schesules[game_type][i].append((w,day,j,'HOME'))
                            if v[day][i][j][w].value() == 1:
                                self.schesules[game_type][i].append((w,day,j,'VISITOR'))
                self.schesules[game_type][i].sort()  
        if game_type == 'i':
            for j in J:
                if j not in self.schesules[game_type].keys():
                    self.schesules[game_type][j] = []
                for i in I:
                    for w in W:
                        for day in [0,1]:
                            if h[day][i][j][w].value() == 1:
                                self.schesules[game_type][j].append((w,day,i,'VISITOR'))
                            if v[day][i][j][w].value() == 1:
                                self.schesules[game_type][j].append((w,day,i,'HOME'))
                self.schesules[game_type][j].sort()

    def GamePerDay(self, w, d, league, game_type='r'):
        pycolor = color.pycolor
        schesule = self.schesules[game_type]
        if game_type == 'r':
            I = self.Teams[league]
            for i in I:
                for k in range(len(schesule[i])):
                    if schesule[i][k][0] == w and schesule[i][k][1]==d and schesule[i][k][-1] == 'HOME':
                        place = self.Teams_name[i]
                        print(self.stadium[i])
                        print(pycolor.GREEN+self.Teams_name[i]+pycolor.END+":"+pycolor.PURPLE+self.Teams_name[schesule[i][k][2]]+pycolor.END)
                    
        else:
            I = self.Teams['p']
            J = self.Teams['s']
            for i in I:
                for k in range(len(schesule[i])):
                    if schesule[i][k][0] == w and schesule[i][k][1]==d and schesule[i][k][-1] == 'HOME':
                        place = self.Teams_name[i]
                        print(self.stadium[i])
                        print(pycolor.GREEN+self.Teams_name[i]+pycolor.END+":"+pycolor.PURPLE+self.Teams_name[schesule[i][k][2]]+pycolor.END)
            for i in J:
                for k in range(len(schesule[i])):
                    if schesule[i][k][0] == w and schesule[i][k][1]==d and schesule[i][k][-1] == 'HOME':
                        place = self.Teams_name[i]
                        print(self.stadium[i])
                        print(pycolor.GREEN+self.Teams_name[i]+pycolor.END+":"+pycolor.PURPLE+self.Teams_name[schesule[i][k][2]]+pycolor.END)

    def GameSchesule(self):
        for game_type in ['r','i']:
            for w in self.W[game_type]:
                for d in [0,1]:
                    for league in ['p','s']:
                        self.GamePerDay(w,d,league,game_type=game_type)

    def GameTable(self, i):
        bar = '==='
        pycolor = color.pycolor
        print(bar+self.Teams_name[i]+bar)
        for game_type in ['r','i']:
            h = 0
            v = 0
            if game_type == 'r':
                print('===通常試合===')
            else:
                print('===交流戦===')

            if game_type not in self.schesules.keys():
                print('None')
                continue

            for o in self.schesules[game_type][i]:
                if o[1] == 0:
                    day='(火)'
                else:
                    day = '(金)'
                if o[-1] == "HOME":
                    print(str(o[0]+1)+pycolor.GREEN+self.Teams_name[o[2]]+pycolor.END+day)
                    h += 1
                else:
                    print(str(o[0]+1)+pycolor.PURPLE+self.Teams_name[o[2]]+pycolor.END+day)
                    v += 1

            print("home:{}\nvisitor:{}".format(h,v))
    
    def GameTables(self):
        for i in range(12):
            self.GameTable(i)

    def CalcDist(self, team, type):
        post_stadium = None
        cur_stadium = None
        schesule_r = self.schesules['r'][team]
        schesule_i = self.schesules['i'][team]

        if type == 1:
            if schesule_i[0][-1] == 'HOME':
                cur_stadium = team
            else:
                cur_stadium = schesule_i[0][2]
            if schesule_r[5][-1] == 'HOME':
                post_stadium = team
            else:
                post_stadium = schesule_r[5][2]
        
        else:
            if schesule_i[-1][-1] == 'HOME':
                cur_stadium = team
            else:
                cur_stadium = schesule_i[-1][2]
            if schesule_r[11][-1] == 'HOME':
                post_stadium = team
            else:
                post_stadium = schesule_r[11][2]  

        return self.D[post_stadium][cur_stadium]                

    def TotalDist(self, team):
        post_stadium = None
        cur_stadium = None
        total_dist = 0 
        D = self.D

        for game_type in self.schesules.keys():
            schesule = self.schesules[game_type][team]
            if schesule[0][-1] == 'HOME':
                post_stadium = team
            else:
                post_stadium = schesule[0][2]

            for t in range(1, len(schesule)):
                if schesule[t][-1] == 'HOME':
                    cur_stadium = team
                else:
                    cur_stadium = schesule[t][2]
                total_dist += D[post_stadium][cur_stadium]
                post_stadium = cur_stadium
        total_dist += self.CalcDist(team,1)+self.CalcDist(team,0)
        self.dists[team] = total_dist
        output = "{} : {}km".format(self.Teams_name[team], total_dist)
    
        return output
    
    def TotalDists(self):
        dists = dict()
        for league in ['p', 's']:
            for team in self.Teams[league]:
                dists[team] = self.TotalDist(team)
        return dists

    def Ranking(self):
        dists = list(self.dists.items())
        dists.sort(key=lambda x:x[1],reverse=True)
        for v in dists:
            i,d = v
            print(self.Teams_name[i]+':{}km'.format(d))

    def Plot(self, game_type, league):
        """
        各チームの移動経路を図示する関数
        """
        total_game = self.total_game[game_type]
        schesule = self.schesules[game_type]
        route_x = []
        route_y = []
        fig, axes= plt.subplots(3, 2)
        row = col = 0
        for team in self.Teams[league]:
            for k in range(total_game):
                _, _, j, stadium = schesule[team][k]
                if stadium == 'VISITOR':
                    route_x.append(self.coordinates[j][1])
                    route_y.append(self.coordinates[j][0])
                else:
                    route_x.append(self.coordinates[team][1])
                    route_y.append(self.coordinates[team][0])
            axes[row, col].plot(route_x, route_y, 'o-')
            axes[row,col].set_title(self.Teams_name[team])
            if row <= 1:
                row += 1
            elif col <= 0:
                col += 1
                row = 0
            route_x = []
            route_y = []
        save_dir = "./result/"
        plt.savefig(os.path.join(save_dir,'{}_{}.png'.format(game_type,league)))

    def Visualize(self):
        for game_type in ['r','i']:
            for league in ['p','s']:
                self.Plot(game_type,league)