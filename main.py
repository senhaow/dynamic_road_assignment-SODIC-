import map
import pandas as pd
from map import SAA
import networkx as nx
import matplotlib.pyplot as plt

global ROAD_TO_ID
global INTX_NODE_ID
global EDGE_TO_NODE
global EDGE_LENGTH


def main():
    df = pd.read_csv("data/properties.csv")
    df_futian = df.loc[df['SECT10'] == 1]
    pos = read_pos('data/node_pos.csv')

    Road_Name_To_ID(df_futian)
    node_Table(df_futian)
    timeSlice = pd.read_csv("data/speed/2018-04-06 00:00:00/5.csv")
    map1 = create_Map('2018-04-06',timeSlice,EDGE_TO_NODE,EDGE_LENGTH)

    av,cv=map1.get_Car(10000,0.6)
    saa = map.SAA(map1,av,cv)
    #draw(map1.G,pos)

    saa.run(2)
    #print(saa.is_Cut_Set(saa.network,[93, 70]))


    # map2 = nx.DiGraph()
    # map2.add_edges_from([(1,2),(2,1),(2,5),(2,3),(3,4),(1,4),(1,5),(5,1),(5,2),(5,3),(4,5)])
    # print(saa.is_Cut_Set(map2,[1,2,3]))
    # print(saa.node_candidate(map2,[2]))



def read_pos(pos_dir):
    pos = pd.read_csv(pos_dir)
    pos_dic = {}
    for index, row in pos.iterrows():
        pos_dic[row['F1']] = (row['x'],row['y'])

    return pos_dic



def draw(G,pos):
    black_edges = [edge for edge in G.edges()]

    # Need to create a layout when doing
    # separate calls to draw nodes and edges
    nx.draw_networkx_nodes(G, pos, cmap=plt.get_cmap('jet'), node_size = 20)
    nx.draw_networkx_labels(G, pos, font_size=3)
    nx.draw_networkx_edges(G, pos, width=.8,arrows=False)
    plt.savefig('luduantu.png',dpi=1200)


def export():
    print(INTX_NODE_ID)
    print(ROAD_TO_ID)

    inv_dict = dict((v, k) for k, v in ROAD_TO_ID.items())

    res = pd.DataFrame(columns=['road1', 'road2', 'num'])

    road_name_temp = {}
    for key,val in INTX_NODE_ID.items():
        road_name_temp[key] = [inv_dict[val[0]], inv_dict[val[1]]]
    print(road_name_temp)

    df = pd.DataFrame.from_dict(data=road_name_temp,orient='index', columns=['road1','road2'])
    df.to_excel("luduandian.xlsx")



#Given a time slice, create a map
def create_Map(time,timeSlice, EDGE_TO_NODE,EDGE_LENGTH):
    map1 = map.Map(time,timeSlice,INTX_NODE_ID, EDGE_TO_NODE,EDGE_LENGTH)
    return map1


#Produce a lookup table for Intersection(Node) IDs
#Produce a Edge ID to Node id tuple Map
def node_Table(df):
    global INTX_NODE_ID,EDGE_TO_NODE,EDGE_LENGTH
    INTX_NODE_ID={}
    EDGE_TO_NODE={}
    EDGE_LENGTH={}
    counter = 0
    for index, row in df.iterrows():
        temp_tup1 = Inx_Tup(row['ROADSECT_NAME'],row['ROADSECT_TO'])
        temp_tup2 = Inx_Tup(row['ROADSECT_NAME'],row['ROADSECT_FROM'])
        if temp_tup1 not in INTX_NODE_ID.values():
            INTX_NODE_ID[counter]=temp_tup1
            counter +=1
        if temp_tup2 not in INTX_NODE_ID.values():
            INTX_NODE_ID[counter]=temp_tup2
            counter +=1

    inv_map = {v: k for k, v in INTX_NODE_ID.items()}
    for index, row in df.iterrows():
        temp_tup1 = Inx_Tup(row['ROADSECT_NAME'],row['ROADSECT_TO'])
        temp_tup2 = Inx_Tup(row['ROADSECT_NAME'],row['ROADSECT_FROM'])
        EDGE_TO_NODE[row['ROADSECT_ID']] = (inv_map[temp_tup1],inv_map[temp_tup2])
        EDGE_LENGTH[row['ROADSECT_ID']] = row['ROADLENGTH']

#return a sorted tuple for intersection
def Inx_Tup(name1, name2):
    code1 = Road_ID(name1)
    code2 = Road_ID(name2)
    if code1 > code2:
        return(code1,code2)
    else:
        return(code2,code1)

#get road id with name given
def Road_ID(name):
    return ROAD_TO_ID[name]

def Road_Name_To_ID(df):
    global ROAD_TO_ID
    ROAD_TO_ID={}

    for index, row in df.iterrows():
        ROAD_TO_ID[row["ROADSECT_NAME"]] = row['ROAD_NO']

    counter = 36000
    for index, row in df.iterrows():
        #If road Name has no id
        if row['ROADSECT_TO'] not in ROAD_TO_ID:
            ROAD_TO_ID[row["ROADSECT_TO"]] = counter
            counter += 1
        if row['ROADSECT_FROM'] not in ROAD_TO_ID:
            ROAD_TO_ID[row["ROADSECT_FROM"]] = counter
            counter += 1

if __name__ == '__main__':
    main()
