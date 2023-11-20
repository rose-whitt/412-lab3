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
        self.all_paths = []
        self.node_to_num_parents = {}   # map node to the number of parents it has
        self.node_to_all_parents = {}
        self.nodes_to_paths = {}
        self.node_edge_map = {}

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
        
        for root in self.roots:
            self.find_all_paths(root)
        
        for path in self.all_paths:
            print(self.print_node_list_lines(path))
        
        for node in self.DP_MAP.nodes_map.values():
            self.get_all_parents(node)
        
        # self.get_paths_to_node(self.DP_MAP.nodes_map[8])

        self.assign_paths_to_nodes()

        print(self.DP_MAP.edge_list)
        print(len(self.DP_MAP.edge_list))

        self.convert_edge_map()
        self.print_edge_map()

        for root in self.roots:
            self.set_priorities(root)
        
        self.DP_MAP.print_dot()
        

        # for root in self.roots:
        #     print("[Calling DFS for root at line " + str(root.line_num) + "]")
        #     self.DFS_one_path(root)
        if (self.DEBUG_FLAG == True):
            self.DP_MAP.print_vrtonode()
        self.DP_MAP.graph_consistency_checker()
        print("// num roots: " + str(len(self.roots)))
        print("// num leaves: " + str(len(self.leaves)))

    def print_node_list_lines(self, node_list):
        tmp = []
        for node in node_list:
            tmp.append(node.line_num)
        return tmp

   

    def find_all_paths(self, start, path=[]):
        """
            Find all paths from root
        """
        path = path + [start]
        paths = [path]
        if len(start.outof_edges) == 0:  # No neighbors (leaf)
            # print(self.print_node_list_lines(path))
            self.all_paths.append(path)
        outof_nodes = []
        for child_line, e in start.outof_edges.items():
            outof_nodes.append(self.DP_MAP.nodes_map[child_line])
        for node in outof_nodes:
            newpaths = self.find_all_paths(node, path)
            for newpath in newpaths:
                paths.append(newpath)
        # print("len of paths: " + str(len(paths)))
        return paths
        
    def get_all_parents(self, node):
        all_parents = []
        max = 0
        for path in self.all_paths:
            if node in path:
                
                idx = path.index(node)
                # print("node " + str(node.line_num) + "in path at idx " + str(idx))
                if (idx > 1):
                    num_parents = idx - 1
                else:
                    num_parents = idx
                if (num_parents > max):
                    max = num_parents
                    all_parents = path[:idx]
        self.node_to_num_parents[node] = len(all_parents)
        self.node_to_all_parents[node] = all_parents
        print("node " + str(node.line_num) + " has " + str(len(all_parents)) + " parents.")
        for node in all_parents:
            print(node.line_num)
        
    def get_paths_to_node(self, node):
        """
            Splice the all_paths arrays so that the ending node in each is the parameter node
        """
        print("Getting all paths to node " + str(node.line_num) + "...")
        node_paths = []
        for path in self.all_paths:
            if node in path:
                idx = path.index(node)
                if (idx == len(path) - 1):  # last elem already
                    tmp = path
                else:
                    tmp = path[:(idx + 1)]
                if (tmp not in node_paths):
                    node_paths.append(tmp)
        # print
        for path in node_paths:
            print(self.print_node_list_lines(path))
        
        return node_paths



    def assign_paths_to_nodes(self):
        for node in self.DP_MAP.nodes_map.values():
            self.nodes_to_paths[node] = self.get_paths_to_node(node)
        
        print("NODES TO PATHS")
        for node, paths in self.nodes_to_paths.items():
            print(str(node.line_num) + " : ")
            for path in paths:
                print(self.print_node_list_lines(path))

    def convert_edge_map(self):
        """
            different graph representation
            convert edge list to map
            {parent : [(child, edge_latency), ...]}

        """
        self.node_edge_map = {node: [] for node in self.DP_MAP.nodes_map.values()}
        for edge in self.DP_MAP.edge_list:
            parent = edge.parent
            child = edge.child
            edge_latency = edge.latency
            tuple = (child, edge_latency)
            self.node_edge_map[parent].append(tuple)
    
    def print_edge_map(self):
        tmp = "{"
        for parent, edges in self.node_edge_map.items():
            tmp += str(parent.line_num)
            tmp += ": ["
            for tuple in edges: 
                cunt = "(" + str(tuple[0].line_num) + ", " + str(tuple[1]) + "), "
                tmp += cunt
            tmp += "], "
        tmp += "}"
        print(tmp)

    def set_priorities(self, start):
        # initialized stack with the start node and its priority
        stack = [(start, 0)]

        while stack:
            current, parent_priority = stack.pop()

            # update priority for the current node only if its higher than the current priority
            current_priority = max(parent_priority, self.DP_MAP.nodes_map[current.line_num].priority)
            self.DP_MAP.nodes_map[current.line_num].priority = current_priority

            # push neighbors onto stack in reverse order to match th eorder of recursive function
            for neighbor, edge_latency in reversed(self.node_edge_map.get(current, [])):
                stack.append((neighbor, current_priority + edge_latency))







        
    
    
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
