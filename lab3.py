import scanner
# from IR_List import *
import lab1
import lab2
import sys
import math
import cProfile, pstats
from io import StringIO
from DP_MAP import *


CATEGORIES = ["MEMOP", "LOADI", "ARITHOP", "OUTPUT", "NOP", "CONST", "REG", "COMMA", "INTO", "ENDFILE", "NEWLINE"]
# only want to process opcodes with registers, which is index 0 through 7
opcodes_list = ["load", "store", "loadI", "add", "sub", "mult", "lshift", "rshift", "output", "nop"]

LOAD_OP = 0
STORE_OP = 1
LOADI_OP = 2
ADD_OP = 3
SUB_OP = 4
MULT_OP = 5
LSHIFT_OP = 6
RSHIFT_OP = 7
OUTPUT_OP = 8
NOP_OP = 9

# MACROS
INVALID = -1
INF = math.inf


# KINDS
DATA = 0
SERIAL = 1
CONFLICT = 2


class Lab3:
    """
    
    """
    def __init__(self, IR_LIST, DEBUG_FLAG):
        self.IR_LIST = IR_LIST
        self.DEBUG_FLAG = DEBUG_FLAG
        self.DP_MAP = DependenceGraph(DEBUG_FLAG)
        self.kinds = ["Data", "Serial", "Conflict"]
        self.roots = []
        self.leaves = []

    def build_graph(self):
        # print("WASSUP BITCH")
        start = self.IR_LIST.head
        while (start != None):
            # creates node for o
            # if o defines vri, sets vr_to_node[vri] = node
            tmp_node = self.DP_MAP.add_node(start)  # always adds node
            # for each vrj used in o, add an edge from o to the node in M(vrj)
            self.DP_MAP.add_data_edge(tmp_node) # doesnt always add edge, conditions to add are in function

            # if o is a load, store or output operation, add edges to ensure serialization of memory ops
            # variables to make sure we only add the most recent one
            OUTPUT_OUTPUT = False   # parent = output, child = output, serial
            STORE_WAW = False   # parent = store, child = store, serial
            # WAR IS ALL READS SINCE LAST STORE, NOT JUST THE MOST RECENT READ
            LAST_STORE = -1
            # LOAD_WAR = False    # parent = store, child = load, serial
            # OUTPUT_WAR = False  # parent = store, child = output, serial

            LOAD_RAW = False    # parent = load, child = store, conflict
            OUTPUT_RAW = False  # parent = output, child = store, conflict

            tmp_node_list = list(self.DP_MAP.nodes_map.values())
            # reverse so it starts from most recent node to farthest away node
            for other_node in reversed(tmp_node_list):
                

                # serial and conflict edges
                if (start.opcode == LOAD_OP or start.opcode == STORE_OP or start.opcode == OUTPUT_OP):
                    # TODO: load to load, no edge needed

                    # either output to output (serial) or output to store (conflict)
                    if (tmp_node.type == OUTPUT_OP):
                        if (other_node.type == OUTPUT_OP and other_node != tmp_node and OUTPUT_OUTPUT == False):   # TODO: maybe OUTPUT_WAR variable so its the most recent output?
                            self.DP_MAP.add_serial_edge(tmp_node, other_node)
                            OUTPUT_OUTPUT = True
                        if (other_node.type == STORE_OP and OUTPUT_RAW == False):
                            self.DP_MAP.add_conflict_edge(tmp_node, other_node)
                            OUTPUT_RAW = True   # only go to most recent store
                    elif (tmp_node.type == STORE_OP):
                        if (other_node.type == STORE_OP and other_node != tmp_node and STORE_WAW == False):
                            self.DP_MAP.add_serial_edge(tmp_node, other_node)
                            STORE_WAW = True
                        if (other_node.type == LOAD_OP and self.check_for_edge(tmp_node, other_node) == False):
                            self.DP_MAP.add_serial_edge(tmp_node, other_node)
                        if (other_node.type == OUTPUT_OP):
                            self.DP_MAP.add_serial_edge(tmp_node, other_node)
                    elif (tmp_node.type == LOAD_OP):
                        if (other_node.type == STORE_OP and LOAD_RAW == False):
                            self.DP_MAP.add_conflict_edge(tmp_node, other_node)
                            LOAD_RAW = True

            start = start.next

        cunt = self.DP_MAP.identify_roots_and_leaves()
        self.roots = cunt[0]
        self.leaves = cunt[1]
        # find line num of first 
        # self.first_op_line_num = 
        self.DP_MAP.print_dot()
        # self.printAllPaths(self.roots[0], self.DP_MAP.nodes_map[3])
        # self.get_parents_and_children(self.DP_MAP.nodes_map[1])
        # parent_nodes = self.find_parents_iteratively(self.DP_MAP.nodes_map[1])
        # print("PARENT NODES: [")
        # for n in parent_nodes:
        #     print(n.line_num)
        # print("]")
        self.print_into_outof(self.DP_MAP.nodes_map[1])
        for root in self.roots:
            for line_num, node in self.DP_MAP.nodes_map.items():
                num_paths = self.countPaths(root, node)
                print(str(root.line_num) + " -> " + str(node.line_num) + " num paths: " + str(num_paths))
        # for root in self.roots:
        #     print("[Calling DFS for root at line " + str(root.line_num) + "]")
        #     self.DFS_one_path(root)
        if (self.DEBUG_FLAG == True):
            self.DP_MAP.print_vrtonode()
        self.DP_MAP.graph_consistency_checker()
        print("// num roots: " + str(len(self.roots)))
        print("// num leaves: " + str(len(self.leaves)))



    def find_root(self):
        """
            Given a node, traverse the graph until arrive at a root
            for testing:
                report05.i has two roots
                report11.i has two roots
                report13.i has two roots
                report18.i has four roots
        """
        finished_nodes = [] # nodes that have had all the paths calculated
    
    def get_highest_edge(self, edge_map):
        """
            Given an edge map, return the edge with the highest latency
        """
        max = 0
        max_edge = None
        for key, edge in edge_map.items():
            if (edge.latency > max):
                max = edge.latency
                max_edge = edge
        return max_edge

    def leaf_to_root(self, node):
        """
            traverse leaf to root to find highest latency path
        """
    
    # 
    def DFS_one_path(self, node):
        """
            prints all not yet visited vertices reachable from node (root)

            prints all vertices in DFS manner from a given source.
        
        """
        # Initially mark all node as not visited, key is their line num since it doesnt always start on first line
        visited = {}
        # Create a list to store paths
        paths = {}
        for line_num, node in self.DP_MAP.nodes_map.items():
            visited[line_num] = False
            paths[line_num] = []
 
        # Create a stack for DFS 
        stack = []

 
        # Push the current source node. 
        stack.append(node) 
 
        while (len(stack)): 
            # Pop a vertex from stack and print it 
            node = stack[-1] 
            stack.pop()
 
            # Stack may contain same vertex twice. So 
            # we need to print the popped item only 
            # if it is not visited. 
            if (not visited[node.line_num]):     # visited is indexed by node line num
                print(node.line_num, end=' ')
                tmp_joined_path = ' -> '.join(map(str, paths[node.line_num]))
                print("Path to " + str(node.line_num) + " : " + tmp_joined_path)
                visited[node.line_num] = True
            
 
            # Get all adjacent vertices of the popped vertex s 
            # If a adjacent has not been visited, then push it 
            # to the stack. 
            # for node in self.adj[node]: 
            # going root to leaf so want to get child associated with each outof_edge
            for child_line_num, edge in node.outof_edges.items():
                child = edge.child
                if (not visited[child_line_num]): 
                    stack.append(child) 
                    paths[child.line_num] = paths[edge.parent.line_num] + [child.line_num]
        print('\n')
        


    def printAllPathsUtil(self, start, end, visited, path):
        # Mark all nodes as unvisited
        

        # Create a queue to store nodes to be explored
        queue = [start]

        # Mark the starting node as visited
        # visited[start.line_num] = True
        visited.remove(start)

        while queue:
            # Remove the first node from the queue
            print("QUEUE: [")
            for n in queue:
                print(str(n.line_num))
            print("]")

            print("VISITED: [")
            for n in visited:
                print(str(n.line_num))
            print("]")

            # print(queue)
            current_node = queue.pop(0)

            # Check if the current node is the target node
            if current_node == end:
                # Print the current path
                path = []
                i = visited.index(current_node)
                while (current_node != start and i < len(visited) and i >= 0):
                    path.append(current_node)
                    current_node = visited[i]
                    i += 1
                path.reverse()
                # print(path)
                for node in path:
                    print(node)
                continue

            # Explore all unvisited neighbors of the current node
            for child_line_num, edge in current_node.outof_edges.items():
                child = edge.child
                if child in visited:
                    # Mark the neighbor as visited and add it to the queue
                    visited.remove(child)
                    queue.append(child)

     # Prints all paths from 's' to 'd'
    def printAllPaths(self, s, d):
 
        # Mark all the vertices as not visited, when visited remove from visited
        visited = []
        for line_num, node in self.DP_MAP.nodes_map.items():
            visited.append(node)
 
        # Create an array to store paths
        path = []
 
        # Call the recursive helper function to print all paths
        self.printAllPathsUtil(s, d, visited, path)

    
    
    

    def get_parents_and_children(self, node):
        # get nodes in out of edges (children)
        child_nodes = []
        for child_line, e in node.outof_edges.items():
            # get child node from nodes list
            child_nodes.append(self.DP_MAP.nodes_map[child_line])

        
        # get nodes in into of edges (parents)
        parent_nodes = []
        for parent_line, e in node.into_edges.items():
            # get child node from nodes list
            cur_parent = self.DP_MAP.nodes_map[parent_line]
            parent_nodes.append(cur_parent)
            # cur_into_edges = cur_parent.into_edges
            # while (len(cur_into_edges) > 0):    # until root
            #     for p, e in cur_into_edges:
        
        print("CHILD NODES: [")
        for n in child_nodes:
            print(n.line_num)
        print("]")
        print("PARENT NODES: [")
        for n in parent_nodes:
            print(n.line_num)
        print("]")
        
    def print_into_outof(self, node):
        into = "parents = ["
        for parent_linenum, e in node.into_edges.items():
            into += " "
            into += str(parent_linenum)
            into += " "
        into += "]"

        outof = "children = ["
        for child_linenum, e in node.outof_edges.items():
            outof += " "
            outof += str(child_linenum)
            outof += " "
        outof += "]"

        print("------------node " + str(node.line_num) + "------------")
        print(into)
        print(outof)

        print("------------------------")

    
    # Returns count of paths from 's' to 'd'
    def countPaths(self, s, d):
 
        # Mark all the vertices
        # as not visited
        visited = {}
        for line_num, node in self.DP_MAP.nodes_map.items():
            visited[line_num] = False
 
        # Call the recursive helper
        # function to print all paths
        pathCount = [0]
        self.countPathsUtil(s, d, visited, pathCount)
        return pathCount[0]
 
    # A recursive function to print all paths
    # from 'u' to 'd'. visited[] keeps track
    # of vertices in current path. path[]
    # stores actual vertices and path_index
    # is current index in path[]
    def countPathsUtil(self, u, d, visited, pathCount):
        visited[u.line_num] = True
 
        # If current vertex is same as
        # destination, then increment count
        if (u == d):
            pathCount[0] += 1
 
        # If current vertex is not destination
        else:
 
            # Recur for all the vertices
            # adjacent to current vertex
            i = 0
            adj_nodes = []
            for child_line, e in u.outof_edges.items():
                adj_nodes.append(self.DP_MAP.nodes_map[child_line])
            while i < len(adj_nodes):

                if (not visited[adj_nodes[i].line_num]):
                    self.countPathsUtil(adj_nodes[i], d, visited, pathCount)
                i += 1
 
        visited[u.line_num] = False

        
        




        
        





        
    
    
    def check_for_edge(self, parent_node, child_node):
        """
            Check if a data edge already exists.
            True if data edge exists and we dont want to add new special edge type
            False if data edge doesn't exist therefore we may want to add new special edge type
            slide 17- "Theoretically, there would be a serial edge from 6 to 4 and 6 to 5.
              BUT since there is already the data edge (“flow dependence with a longer latency”??)
                from 6 to 4 it would be redundant to add a serial edge as well.
                  It wouldnt be incorrect ot add it, but it would add extra time and work.
                    Also the reference doesnt do that."
        """
        # print("[check_for_edge]")
        # see if child_node.line_num is in parent_node.outofedges
        if (child_node.line_num in parent_node.outof_edges):
            # print("[check_for_edge] an edge exists already btwn parent and child")
            edge = parent_node.outof_edges[child_node.line_num]
            print(edge)
            if (edge.kind == DATA):
                # print("[check_for_edge] the edge between parent and child is a data edge. do not add new special edge.")
                return True
        return False
                

       



    

    


def main():
    # pr = cProfile.Profile()
    # pr.enable() 
    # print("in lab3 main")
    # print(sys.argv)
    if (sys.argv[1] == '-h'):
        print("HELP: FUNCTIONALITY AND COMMAND LINE FLAGS")
        print("     - the file is checked for validity in lab3, i.e. before it is passed into lab2, lab1.")
        print("     - lab1 runs with the functionality of the -p flag from lab1. that is that it invokes parser and resports on success or failure, invokes scanner and parser.")
        print("     - lab2 renames and allocates the file.")
        print("     - lab3 checks validity of file, then passes the file to lab2 which passes the file to lab1.")
        print("FLAGS:")
        print("     -lab2 -x [filename]     Performs scanning, parsing, renaming on the file and then prints the renamed block to the stdout.")
        print("")
        print("     -lab2 [k] [filename]      Where k is the number of registers available to the allocator (3<=k<=64).")
        print("                     Scan, parse, rename, and allocate code in the input block given in filename so that it uses")
        print("                     only registers r0 to rk-1 and prints the resulting code in the stdout.")
        print("     [filename]          Runs lab3, i.e. used to invoke schedule shit.")
        print("     -x [filename]          Debugging for lab3. Runs lab3 like normal but prints extra info for debugging like latency-weighted distance in nodes in graph/dot file, latency of edge in graph/dot file, VR_TO_NODE map, and any other things I decide.")

    else:

        arg_len = len(sys.argv)

        __file__ = sys.argv[arg_len - 1]
            
        # open file
        try:
            f = open(__file__, 'r')
        except FileNotFoundError:  # FileNotFoundError in Python 3
            print(f"ERROR input file not found", file=sys.stderr)
            sys.exit()
        Lab_2 = lab2.Lab2(f)
        Lab_2.rename()
        # Only renaming for Lab3, not allocating.
        if (sys.argv[1] == '-lab2'):
            if (sys.argv[2] == '-x'):
                Lab_2.print_renamed_block()
            elif (int(sys.argv[2]) >= 3 and int(sys.argv[2]) <= 64):
                # lab2.allocate(int(sys.argv[1]))
                Lab_2.dif_alloc(int(sys.argv[2]))
                Lab_2.print_allocated_file()
        # Lab_2.main()
        f.close()
        DEBUG_FLAG = False
        if (sys.argv[1] == '-x'):
            DEBUG_FLAG = True

        
        Lab_3 = Lab3(Lab_2.IR_LIST, DEBUG_FLAG)
        Lab_3.build_graph()



if __name__ == "__main__":
  main()
