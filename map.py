import networkx as nx
import pandas as pd
import random
import math



class Map(object):
    #input speed period df
    #Nodes is a nodes map
    def __init__(self, TIME, timeSlice, Nodes, EDGE_TO_NODE, EDGE_LENGTH):
        super(Map, self).__init__()
        self.time = TIME
        self.nodes=Nodes
        self.edges=self.create_Edges(timeSlice,EDGE_TO_NODE,EDGE_LENGTH)
        self.edge_to_node = EDGE_TO_NODE
        self.G = self.network()

    def create_Edges(self,df,EDGE_TO_NODE,EDGE_LENGTH):
        edges = {}
        errors_Count = 0
        edges_Added = 0
        for index, row in df.iterrows():
            try:
                edgeID = row['ROADSECT_ID']
                edges[edgeID] = (Edge(edgeID,EDGE_TO_NODE[edgeID],EDGE_LENGTH[edgeID], row['GOLEN'],row['GOTIME'],row['GOCOUNT']))
                edges_Added += 1
            except:
                errors_Count += 1

        print("Total of "+str(errors_Count)+" of edges did not match")
        print("Added "+str(edges_Added)+" edges to "+str(len(self.nodes))+" nodes")
        return edges


    def network(self):
        G = nx.DiGraph()
        G.add_nodes_from(self.nodes)
        for key,edge in self.edges.items():
            u=edge.front_end[0]
            v=edge.front_end[1]
            G.add_weighted_edges_from([(u,v,edge.length)])
            G.edges[u,v]['id']=edge.edge_id
            G.edges[u,v]['time']=edge.pass_time
            G.edges[u,v]['av']=0

        return G

    def get_Car(self, num, AV_Ratio):
        df=pd.DataFrame([s.get_RoadCondition() for _,s in self.edges.items()])
        df_normalized = normalize(df,'count')
        car_Direction = self.get_Path(df_normalized,num)
        av,cv = self.split(car_Direction,AV_Ratio)

        return av,cv

    def split(self, car,av_ratio):
        av_num = round(av_ratio * len(car))
        cv_num = len(car) - av_num
        av = car[:av_num]
        cv = car[av_num:]

        return av,cv

    def get_Path(self,df_normalized,choose_size):
        choice1 = random.choices(population=df_normalized['id'], weights=df_normalized['count'],k=choose_size)
        choice2 = random.choices(population=df_normalized['id'], weights=df_normalized['count'],k=choose_size)

        node_list_1=([random.choice(self.edge_to_node[edge]) for edge in choice1])
        node_list_2=([random.choice(self.edge_to_node[edge]) for edge in choice2])

        return list(zip(node_list_1, node_list_2))




class Node(object):
    """docstring for Node."""

    def __init__(self, ID, ROAD_INTX):
        super(Node, self).__init__()
        self.id = ID
        #ROAD_ID is a tuple pair for the interaction of two roads
        self.road_intx = ROAD_INTX

class Edge(object):

    def __init__(self, ID,FRONT_END,LENGTH,GOLEN,GOTIME,GOCOUNT):
        super(Edge, self).__init__()
        self.edge_id = ID
        #front_end stores a node id tuple pair
        self.front_end = FRONT_END
        self.length = LENGTH
        self.count = GOCOUNT
        self.speed = self.avg_speed(GOLEN,GOTIME)
        self.pass_time=self.pass_time()
        self.av = False

    def avg_speed(self,GOLEN,GOTIME):
        return (GOLEN/GOTIME)

    def pass_time(self):
        return(self.length/self.speed)

    def get_RoadCondition(self):
        return {
        'id': self.edge_id,
        'count': self.count
        }


def normalize(df,feature_name):
    result = df.copy()
    max_value = df[feature_name].max()
    min_value = df[feature_name].min()
    result[feature_name] = (df[feature_name] - min_value) / (max_value - min_value)
    return result


class SAA(object):
    """docstring for SAA."""

    def __init__(self, map, av, cv):
        super(SAA, self).__init__()
        self.network = map.G
        self.init = 93 #random.randint(0, len(self.network.nodes()))
        self.av = av
        self.cv = cv


    def run(self,epoch):
        while not self.is_Cut_Set(self.network,[self.init]):
            self.init = random.randint(0, len(self.network.nodes()))

        av_node_list=[self.init]

        cand_pool = []

        solution_keep=[]

        for x in range(0,epoch):
            T = (epoch - x)
            print('-------------------Epoch '+str(x)+'-------------------')
            print('AV Node Considering:'+str(av_node_list))

            #calculate Loss for this av_node_list situation
            time_before,time_after,res = self.get_sys_loss(av_node_list)
            print('time_before: '+str(round(time_before,2))+' time_after: '+str(round(time_after,2)))

            #Get candidate for possible addition to the list
            cand_pool.extend(self.node_candidate(self.network,av_node_list))

            #Get a neighbor solution with a new candidate
            if len(cand_pool) == 0:
                solution_keep.append(([av_node_list],res))
                print('Discard Solution.')
                self.init = random.randint(0, len(self.network.nodes()))
                av_node_list = [self.init]

            else:
                av_node_new  = cand_pool.pop(0)

                print('Neighbor Solution: ')
                print(av_node_new)

                _,_,res_new = self.get_sys_loss(av_node_new)

                delta_imp = res_new-res
                print(delta_imp)

                if(delta_imp > 0):
                    av_node_list = av_node_new
                    print('New List Accepted!  Improvement:  '+str(delta_imp)+" seconds")

                elif (math.exp(delta_imp/T) > random.uniform(0,1)):
                    av_node_list = av_node_new
                    print('New List Accepted by temperature:  '+str(math.exp(delta_imp/T)))

                else:
                    print('Continue with old list')


    def get_sys_loss(self,av_node_list):
        time_after = 0
        time_before = 0
        no_path = 0
        av_list = self.av
        cv_list = self.cv
        #print(av_node_list)
        map_av,map_cv = self.create_AV_CV_Map(av_list,cv_list,av_node_list)

        for av in av_list:
            if self.find_distance(av[0],av[1],map_av):
                time_after += self.find_distance(av[0],av[1],map_av)

            if self.find_distance(av[0],av[1],self.network):
                time_before += self.find_distance(av[0],av[1],self.network)

        for cv in cv_list:
            if self.find_distance(cv[0],cv[1],map_cv):
                time_after += self.find_distance(cv[0],cv[1],map_cv)
            else:
                no_path+=1

            if self.find_distance(cv[0],cv[1],self.network):
                time_before += self.find_distance(cv[0],cv[1],self.network)

        return time_before,time_after, time_before-time_after

    def create_AV_CV_Map(self,av,cv,av_node_list):
        map_av = self.network.copy()
        map_cv = self.network.copy()

        remove_list =[]
        for u,v,a in map_cv.edges(data=True):
            if u in av_node_list and v in av_node_list:
                remove_list.append((u,v))
        map_cv.remove_edges_from(remove_list)

        for u,v,a in map_av.edges(data=True):
            if u in av_node_list and v in av_node_list:
                map_av[u][v]['time'] = map_av[u][v]['time']/3
                map_av[u][v]['av'] = 1
        return map_av, map_cv



    def node_candidate(self,map,node_list):
        candidates = []
        for node in node_list:
            candidates = unique_List(candidates,self.get_neighbor(node,map))

        cand = []
        for candidate in candidates:
            print("checking node: "+str(candidate))
            if candidate not in node_list:
                #print('not in node list!')
                temp = node_list.copy()
                temp.append(candidate)
                #print(temp)
                if self.is_Cut_Set(map, temp):
                    #print('is cut set!')
                    cand.append(temp)
        return cand

    def is_Cut_Set(self, map, list_node_remove):
        remove_list =[]
        map_temp = map.copy()
        ori_rank = len(map.nodes()) - nx.algorithms.components.number_weakly_connected_components(map)
        # print('Original graph:')
        # print('Component:' + str(nx.algorithms.components.number_weakly_connected_components(map)))
        # print('Rank: '+ str(ori_rank))

        for u,v,a in map_temp.edges(data=True):
            if u in list_node_remove and v not in list_node_remove:
                remove_list.append((u,v))
            if v in list_node_remove and u not in list_node_remove:
                remove_list.append((u,v))

        map_temp.remove_edges_from(remove_list)
        after_rank = len(map_temp.nodes()) - nx.algorithms.components.number_weakly_connected_components(map_temp)

        # print('After graph:')
        # print('Component:' + str(nx.algorithms.components.number_weakly_connected_components(map_temp)))
        # print('Rank: '+ str(after_rank))


        if ori_rank - after_rank == 1:
            return True
        else:
            return False

    #enter Node Id in int, return a list of neighbor nodes
    def get_neighbor(self,node,map):
        return [n for n in map.neighbors(node)]


    def find_distance(self,source,target,G):
        if nx.has_path(G, source, target):
            return nx.shortest_path_length(G,source,target, weight='time')
        else:
            return False


def unique_List(list1,list2):
    list1.extend(list2)
    return list(dict.fromkeys(list1))
