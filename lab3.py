import scanner
# from IR_List import *
import lab1
import lab2
import sys
import math
import cProfile, pstats
from io import StringIO
from DP_MAP import *
import copy



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

# LATENCIES (HANDOUT APPENDIX B)
LOAD_LATENCY = 5
LOADI_LATENCY = 1
STORE_LATENCY = 5
ADD_LATENCY = 1
SUB_LATENCY = 1
MULT_LATENCY = 3
LSHIFT_LATENCY = 1
RSHIFT_LATENCY = 1
OUTPUT_LATENCY = 1
NOP_LATENCY = 1

# MACROS
INVALID = -1
INF = math.inf


# KINDS
DATA = 0
SERIAL = 1
CONFLICT = 2

# UNITS
F0 = 0
F1 = 1

# STATUSES
NOT_READY = 1
READY = 2
ACTIVE = 3
RETIRED = 4


# NODE LIST ELEMENT FORMAT
IDX_NODE = 0
LINE_NUM_NODE = 1
FULL_OP_NODE = 2 # (like loadI 12 => r1)
TYPE_NODE = 3   # opcode
DELAY_NODE = 4
ROOT_BOOL_NODE = 5
LEAF_BOOL_NODE = 6
INTO_EDGES_MAP_NODE = 7    # idx of parent mapped to idx of edge in edges list between this node and parent edges going into the node, list of integers where integer is idx in edges list
OUTOF_EDGES_MAP_NODE = 8   # idx of child mapped to idx of edge in edges list between this node and child ; edges going out of the node, list of integers where integer is idx in edges list
STATUS_NODE = 9
IR_ARG1_NODE = 10   # [sr, vr, pr, nu]
IR_ARG2_NODE = 11   # [sr, vr, pr, nu]
IR_ARG3_NODE = 12   # [sr, vr, pr, nu]
PRIORITY_NODE = 13

# EDGE LIST ELEMENT FORMAT
IDX_EDGE = 0
KIND_EDGE = 1
LATENCY_EDGE = 2
VR_EDGE = 3 # only defined if kind is Data
PARENT_IDX_EDGE = 4 # index of parent node in the nodes list
OUTOF_LINE_NUM_EDGE = 5 # line num of parent node
CHILD_IDX_EDGE = 6   # index of child node in nodes list
INTO_LINE_NUM_EDGE = 7  # line num of child node






class Lab3:
    """
    
    """
    def __init__(self, IR_LIST, DEBUG_FLAG, GRAPH_ONLY):
        self.IR_LIST = IR_LIST
        self.DEBUG_FLAG = DEBUG_FLAG
        self.GRAPH_ONLY = GRAPH_ONLY
        self.DP_MAP = DependenceGraph(DEBUG_FLAG)
        self.kinds = ["Data", "Serial", "Conflict"]
        self.roots = []
        self.leaves = []
        self.all_paths = []
        self.node_to_num_parents = {}   # map node to the number of parents it has
        self.node_to_all_parents = {}
        self.nodes_to_paths = {}
        self.node_edge_map = {}

        # scheduling
        # initialize both unit dictionaries to have number of nodes issue slots
        #  each keyed 1 - number of nodes, with the value being None, but will be replaced by node
        self.schedule = {F0: {}, F1: {}}    
        self.num_nodes = 0

        ####################### NEW DEPENDENCE GRAPH IMP #######################
        self.VR_TO_NODE = {}    # vr to index of node in nodes list
        # Node format [IDX, line num, Full OP, type, delay, root boolean, leaf boolean, into edges list (index in edges list), out of edges list (index in edges list), status, ir list arg1, ir list arg2, ir list arg3, priority]
        self.nodes_list = []
        # Edge format [IDX, kind, latency, VR, parent idx, out of line num (line num of parent node), child idx, into line num (line num of child node)]
        self.edges_list = []
        # child to parent list format: idx = child node index in nodes_list, element list of indices of parents
        self.child_to_parents = []
        # parent to child list format: idx = parent node index in nodes_list, element list of indices of children
        self.parent_to_children = []

    
    def build_new_graph(self):
        """
            New graph implementation
        """
        print("WASSUP BITCH")
        start = self.IR_LIST.head
        while (start != None):
            print("CUNT")
            # creates node for o
            # if o defines vri, sets vr_to_node[vri] = node
            tmp_node = self.add_node(start)  # always adds node
            # for each vrj used in o, add an edge from o to the node in M(vrj)
            self.add_data_edge(tmp_node) # doesnt always add edge, conditions to add are in function

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

            tmp_node_list = list(self.nodes_list)
            # reverse so it starts from most recent node to farthest away node
            for other_node in reversed(tmp_node_list):
                

                # serial and conflict edges
                if (start.opcode == LOAD_OP or start.opcode == STORE_OP or start.opcode == OUTPUT_OP):
                    # TODO: load to load, no edge needed

                    # either output to output (serial) or output to store (conflict)
                    if (tmp_node[TYPE_NODE] == OUTPUT_OP):
                        if (other_node[TYPE_NODE] == OUTPUT_OP and other_node != tmp_node and OUTPUT_OUTPUT == False):   # TODO: maybe OUTPUT_WAR variable so its the most recent output?
                            self.add_serial_edge(tmp_node, other_node)
                            OUTPUT_OUTPUT = True
                        if (other_node[TYPE_NODE] == STORE_OP and OUTPUT_RAW == False):
                            self.add_conflict_edge(tmp_node, other_node)
                            OUTPUT_RAW = True   # only go to most recent store
                    elif (tmp_node[TYPE_NODE] == STORE_OP):
                        if (other_node[TYPE_NODE] == STORE_OP and other_node != tmp_node and STORE_WAW == False):
                            self.add_serial_edge(tmp_node, other_node)
                            STORE_WAW = True
                        if (other_node[TYPE_NODE] == LOAD_OP and self.NEW_check_for_edge(tmp_node, other_node) == False):
                            self.add_serial_edge(tmp_node, other_node)
                        if (other_node[TYPE_NODE] == OUTPUT_OP):
                            self.add_serial_edge(tmp_node, other_node)
                    elif (tmp_node[TYPE_NODE] == LOAD_OP):
                        if (other_node[TYPE_NODE] == STORE_OP and LOAD_RAW == False):
                            self.add_conflict_edge(tmp_node, other_node)
                            LOAD_RAW = True

            start = start.next

        self.identify_roots_and_leaves()
        
        self.NEW_convert_edge_map()
        if (self.DEBUG_FLAG == True): self.NEW_print_edge_map()
        print("roots:")
        print(self.roots)
        print("edges:")
        print(self.edges_list)
        for root in self.roots:
            self.NEW_set_priorities(root)
        
        if (self.DEBUG_FLAG == True or self.GRAPH_ONLY == True):
            self.print_dot()
        
        print("DONE. NODES LIST:")
        print(self.nodes_list)
        print("DONE. EDGES LIST:")
        print(self.edges_list)

        
        print(self.DEBUG_FLAG)
        self.print_dot()

        # if (self.DEBUG_FLAG == True):
        #     self.DP_MAP.print_vrtonode()
        # self.graph_consistency_checker()
        if (self.DEBUG_FLAG == True): print("// num roots: " + str(len(self.roots)))
        if (self.DEBUG_FLAG == True): print("// num leaves: " + str(len(self.leaves)))

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
        

        # print(self.DP_MAP.edge_list)
        # print(len(self.DP_MAP.edge_list))

        self.convert_edge_map()
        if (self.DEBUG_FLAG == True): self.print_edge_map()

        for root in self.roots:
            self.set_priorities(root)
        
        if (self.DEBUG_FLAG == True): self.DP_MAP.print_dot()
        # self.DP_MAP.print_dot()

        if (self.DEBUG_FLAG == True):
            self.DP_MAP.print_vrtonode()
        self.DP_MAP.graph_consistency_checker()
        if (self.DEBUG_FLAG == True): print("// num roots: " + str(len(self.roots)))
        if (self.DEBUG_FLAG == True): print("// num leaves: " + str(len(self.leaves)))

    def print_node_list_lines(self, node_list):
        tmp = []
        for node in node_list:
            tmp.append(node.line_num)
        return tmp

   

    
        
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

    def print_ready(self, ready):
        ret = "["
        for node in ready:
            tmp = "<" + str(node.line_num) + " " + str(opcodes_list[node.type]) + " , " + str(node.priority) + ">, "
            ret += tmp
        ret += "]"
        print(ret)
    
    def print_active(self, active):
        ret = "["
        for pair in active:
            tmp = "<" + str(pair[0].line_num) + " " + str(opcodes_list[pair[0].type]) + " , #" + str(pair[1]) + ">, "
            ret += tmp
        ret += "]"
        print(ret)
    


    def get_operations_for_units(self, ready):
        """
            Get an operation for each functional unit based on the highest priority and remove those from ready
                and these constraints:
                Load and store operations: only f0
                loadI: f0 or f1
                Mult: f1
                Output: f0 or f1, but only one per cycle (latency == cycle counts)
            
            returns array where index 0 is node for f0 and index 1 is node for f1
        """
        f0_node = None
        f1_node = None


        if (self.DEBUG_FLAG == True):
            print("[get_operations_for_units]")
            print("READY BEFORE")
            self.print_ready(ready)


        if (len(ready) == 0):
            return [NOP_OP, NOP_OP]
        
        
        num_restricted = 0
        restricted_ready = []
        unrestricted_ready = []
        for node in ready:
            if (node.type == LOAD_OP or node.type == STORE_OP or node.type == MULT_OP or node.type == OUTPUT_OP):
                num_restricted += 1
                node.status = READY
                restricted_ready.append(node)
            else:
                unrestricted_ready.append(node)
                node.status = READY
      
        if (self.DEBUG_FLAG == True):
            print("RESTRICTED READY:")
            self.print_ready(restricted_ready)
            print("UNRESTRICTED READY:")
            self.print_ready(unrestricted_ready)

        # 🔒🔒🔒🔒🔒🔒🔒 First, restricted nodes 🔒🔒🔒🔒🔒🔒🔒🔒
        # f0
        for node in restricted_ready:
            # at least one unit still open
            if (f0_node == None or f1_node == None):
                # only on f0
                if (node.type == LOAD_OP or node.type == STORE_OP):
                    if (f0_node == None): # hasnt been assigned yet
                        f0_node = node
                # only on f1
                if (node.type == MULT_OP):
                    if (f1_node == None): # hasnt been assigned yet
                        f1_node = node
                # takes whole cycle
                if (node.type == OUTPUT_OP):
                    # havent already assigned either unit
                    if (f0_node == None and f1_node == None):
                        f0_node = node
                        f1_node = NOP_OP
                        ready.remove(node)
                        return [f0_node, f1_node]
        
        # check if we have filled f0 and f1
        if (f0_node != None and f1_node != None):
            if (f0_node in ready):  # havent already removed
                ready.remove(f0_node)
            if (f1_node in ready):  # havent already removed
                ready.remove(f1_node)
            return [f0_node, f1_node]

        # check we have removed everything
        if (f0_node != None and f0_node in ready):
            ready.remove(f0_node)
        if (f0_node != None and f0_node in restricted_ready):
            restricted_ready.remove(f0_node)
        if (f1_node != None and f1_node in ready):
            ready.remove(f1_node)
        if (f1_node != None and f1_node in restricted_ready):
            restricted_ready.remove(f1_node)
        

        # 🔒🔒🔒🔒🔒🔒 END OF RESTRICTED READY PRIORITY 🔒🔒🔒🔒🔒🔒🔒🔒🔒

        # ❄️❄️❄️❄️❄️❄️ Next, prioritize loadI ❄️❄️❄️❄️❄️❄️❄️❄️❄️
        # see if there is a loadI we can put in the empty slot
        for node in unrestricted_ready:
            if (node.type == LOADI_OP):
                # check that it is not somehow already one of the issue slots
                if (f0_node != node and f1_node != node):
                    # find the open slot
                    if (f0_node == None):
                        f0_node = node
                    elif (f1_node == None):
                        f1_node = node
        # check we remove everything
        if (f0_node in ready):
            ready.remove(f0_node)
        if (f0_node in unrestricted_ready):
            unrestricted_ready.remove(f0_node)
        if (f1_node in ready):
            ready.remove(f1_node)
        if (f1_node in unrestricted_ready):
            unrestricted_ready.remove(f1_node)
        
        # check if we have filled f0 and f1
        if (f0_node != None and f1_node != None):
            return [f0_node, f1_node]
        
        # ❄️❄️❄️❄️❄️❄️❄️❄️ END OF LOADI PRIORITY ❄️❄️❄️❄️❄️❄️❄️❄️❄️❄️

        # 🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈 Priority based from unrestricted list 🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈
        # check if there is anything in unrestricted_ready
        if (len(unrestricted_ready) == 0):
            # nothing else to do so we need to make the issue slot and return
            if (f0_node == None):
                f0_node = NOP_OP
            if (f1_node == None):
                f1_node = NOP_OP
            # return
            return [f0_node, f1_node]

        # check if there is only one thing in unrestricted ready, so return
        if (len(unrestricted_ready) == 1):
            # find the empty slot
            # both slots open
            if (f0_node == None and f1_node == None):
                f0_node = unrestricted_ready[0]
                f1_node = NOP_OP
            # only one slot open
            elif (f0_node == None):
                f0_node = unrestricted_ready[0]
            elif (f1_node == None):
                f1_node = unrestricted_ready[0]
            
            # check we remove everything
            if (f0_node in ready):
                ready.remove(f0_node)
            if (f0_node in unrestricted_ready):
                unrestricted_ready.remove(f0_node)
            if (f1_node in ready):
                ready.remove(f1_node)
            if (f1_node in unrestricted_ready):
                unrestricted_ready.remove(f1_node)
            # return
            return [f0_node, f1_node]

        if (len(unrestricted_ready) == 2):
            # both open
            if (f0_node == None and f1_node == None):
                f0_node = unrestricted_ready[0]
                f1_node = unrestricted_ready[1]
            elif (f0_node == None):
                # idx 0 is highest priority value
                f0_node = unrestricted_ready[0]
            elif (f1_node == None):
                # idx 0 is highest priority value
                f1_node = unrestricted_ready[0]
            # check we remove everything
            if (f0_node in ready):
                ready.remove(f0_node)
            if (f0_node in unrestricted_ready):
                unrestricted_ready.remove(f0_node)
            if (f1_node in ready):
                ready.remove(f1_node)
            if (f1_node in unrestricted_ready):
                unrestricted_ready.remove(f1_node)
            # return
            return [f0_node, f1_node]
                


        # get highest priority node from unrestricted ready
        if (len(unrestricted_ready) > 2):
            highest_priority = []
            first_node_prior = unrestricted_ready[0].priority    # bc sorted
            # check if there are multiple of the same priority
            for node in unrestricted_ready:
                if (node.priority == first_node_prior):
                    highest_priority.append(node)
            
            if (self.DEBUG_FLAG == True):
                print("HIGHEST PRIORITY:")
                self.print_ready(highest_priority)
                print("READY AFTER:")
                self.print_ready(ready)


            # Find operation for f0
            if (f0_node == None):
                for node in highest_priority:
                    if (node.type != MULT_OP):
                        f0_node = node
                        break

            # if we found an f0 node
            if (f0_node != None):
                # remove from list with highest priority nodes
                if (f0_node in highest_priority):
                    highest_priority.remove(f0_node)
                # remove f0_node from ready
                if (f0_node in ready):
                    ready.remove(f0_node)
                # remove from unrestricted
                if (f0_node in unrestricted_ready):
                    unrestricted_ready.remove(f0_node)

                if (self.DEBUG_FLAG == True):
                    print("HIGHEST PRIORITY AFTER F0NODE:")
                    self.print_ready(highest_priority)
                
                # output can only have one per cycle
                if f0_node.type == OUTPUT_OP:
                    return [f0_node, NOP_OP]
                

                # if f0 took the only highest priority node, recompute highest priority nodes
                if (len(highest_priority) == 0):
                    
                    if (self.DEBUG_FLAG == True):
                        print("READY AFTER REMOVE F0NODE:")
                        self.print_ready(ready)
                    
                    # if nothing left in ready, just return
                    if (len(ready) == 0):
                        return [f0_node, NOP_OP]
                    else:
                        first_node_prior = unrestricted_ready[0].priority    # bc sorted
                        for node in unrestricted_ready:
                            if (node.priority == first_node_prior):
                                highest_priority.append(node)
            else:
                # set to nop if we didn't find anything
                f0_node = NOP_OP
            
            if (self.DEBUG_FLAG == True):
                print("HIGHEST PRIORITY B4 f1:")
                self.print_ready(highest_priority)
                print("READY B4 f1:")
                self.print_ready(ready)
            

            
            # Find operation for f1
            if (f1_node == None):
                for node in highest_priority:
                    if (node.type != LOAD_OP and node.type != STORE_OP):
                        f1_node = node
                        break
            
            # if we didnt find an f1 node
            if (f1_node == None):
                # set to nop if we didn't find anything
                f1_node = NOP_OP
            else:   # if we found an f1 node
                if (f1_node in ready):
                    ready.remove(f1_node)
                if (f1_node in unrestricted_ready):
                    unrestricted_ready.remove(f1_node)
                if (f1_node in highest_priority):
                    highest_priority.remove(f1_node)
            
        # double check that neither are None
        if (f0_node == None):
            f0_node = NOP_OP
        if (f1_node == None):
            f1_node = NOP_OP
        ret = [f0_node, f1_node]
        if (self.DEBUG_FLAG == True):
            print("RETURN VALUE:")
            print(ret)
        
        return ret

    
    
    def schedule_algo(self):
        if (self.DEBUG_FLAG == True): print("[SCHEDULE ALGO]")

        cycle = 1
        # Sort the list in descending order based on the age attribute
        sorted_objects = sorted(self.leaves, key=lambda n: n.priority, reverse=True)
        ready = sorted_objects # array of nodes
        active = [] # array of pairs- (node, cycle that the node will come off the active list)

        # if (self.DEBUG_FLAG == True): self.print_ready(ready)

        if (self.DEBUG_FLAG == True): print("BEGINNING WHILE LOOP")
        if (self.DEBUG_FLAG == True): print(len(ready))
        if (self.DEBUG_FLAG == True): print(len(active))
        # Terminate when active and ready lists are empty
        while ((len(ready) == 0 and len(active) == 0) == False):
            if (self.DEBUG_FLAG == True): self.print_schedule()
            sorted_objects = sorted(ready, key=lambda n: n.priority, reverse=True)
            ready = sorted_objects # array of nodes
            if (self.DEBUG_FLAG == True): print("CYCLE: " + str(cycle))
            # Pick an operation, o, for each functional unit
            ops = self.get_operations_for_units(ready)

            early_release_ops = []
            
            if (self.DEBUG_FLAG == True):
                print(len(ops))
                print("OPS:")
                print(ops)

                self.print_ready(ready)
                self.print_active(active)
            f0_op = ops[F0]
            f1_op = ops[F1]
            # Move o from Ready to Active
            if (f0_op != NOP_OP):
                f0_op.status = ACTIVE
                active.append((f0_op, f0_op.delay + cycle))
                if (f0_op.type == LOAD_OP or f0_op.type == STORE_OP or f0_op.type == OUTPUT_OP):
                    early_release_ops.append(f0_op)
            if (f1_op != NOP_OP):
                f1_op.status = ACTIVE
                active.append((f1_op, f1_op.delay + cycle))
                if (f1_op.type == LOAD_OP or f1_op.type == STORE_OP or f1_op.type == OUTPUT_OP):
                    early_release_ops.append(f1_op)
            self.schedule[F0][cycle] = f0_op
            self.schedule[F1][cycle] = f1_op


            if (self.DEBUG_FLAG == True):
                print("ACTIVE AFTER APPENDING")
                self.print_active(active)

            # Increment cycle
            cycle += 1

            # get active ops that have retired
            retired = []
            for pair in active:
                if (pair[1] == cycle):
                    retired.append(pair)
                    pair[0].status = RETIRED
            

            # Find each op, o, in Active that retires
            for pair in retired:
                # Remove o from Active
                active.remove(pair)
                # For each op, d, that depends on o (into, d = parent)
                for parent_linenum, edge in pair[0].into_edges.items():
                    print("d:")
                    d = edge.parent
                    print(d)
                    
                    all_ready = True
                    # check outof nodes of d
                    for child_linenum, out_e in d.outof_edges.items():
                        # If d is now "ready" (operation that defined that operand is completed/retired- "If a node represents a use of a value, it has an edge to the node that defines that value")
                        if (out_e.child.status != RETIRED):
                            all_ready = False
                    if (all_ready): # Add d to the Ready set
                        if (self.DEBUG_FLAG == True): print("Defining ops ready! Adding " + str(d.line_num) + " to the ready set!")
                        if (d not in ready):
                            d.status = READY
                            ready.append(d)
                    else:
                        if (self.DEBUG_FLAG == True): print("Defining ops of " + str(d.line_num) + " are not ready")


                        
            # If this iteration of the while loop added a load, store, or output operation to the active set, call it x

            # "for each operation y that has a serial dependence back to op in active_set,
            # If all the other dependences for y have been satisfied,
            # then y can move onto the Ready set now that operation op has been scheduled.
            # satisified means: all other non-serial dependences are finished and all serial dependences are scheduled
            multi_cycle_active = []
            for pair in active:
                if (pair[0].type == LOAD_OP or pair[0].type == STORE_OP or pair[0].type == OUTPUT_OP):
                    multi_cycle_active.append(pair)
                
            if (self.DEBUG_FLAG == True): 
                print("len(multi_cycle_active) = " + str(len(multi_cycle_active)) + " vs. len(early_release_ops) = " + str(len(early_release_ops)))
            
            # TODO: this doesnt seem to work
            # Find each multi-cycle (load, store, mult) operation o in Active
            # for node in early_release_ops:
            #     # Check operations that depend on o for early releases (into, parent)
            #     #for each operation y that has a serial dependence back to op in active_set
            #     for parent_linenum, edge in node.into_edges.items():
            #         satisfied = True
            #         if (edge.kind == SERIAL):
            #             y = edge.parent
            #             # check all dependences of edge.parent (y)
            #             for pl, e in y.outof_edges.items():
            #                 # check all non-serial dependences are finished 
            #                 if (e.kind == SERIAL):
            #                     if (e.child.status != ACTIVE):
            #                         satisfied = False
            #                 else:
            #                     if (e.child.status != RETIRED):
            #                         satisfied = False
            #             if (satisfied): # Add y to the Ready set
            #                 if (self.DEBUG_FLAG == True): print("early release- Adding " + str(d.line_num) + " to the ready set!")
            #                 y.status = READY
            #                 ready.append(y)
            #             else:
            #                 if (self.DEBUG_FLAG == True): print("early release- Depending ops of " + str(d.line_num) + " are not ready")

                            



    def print_schedule(self):
        sched_len = len(self.schedule[F0])
        # print(sched_len)
        ret = ""
        for i in range(1, sched_len + 1):
            ret += "[ "
            f0_value = self.schedule[F0][i]
            f1_value = self.schedule[F1][i]
            if f0_value == NOP_OP:
                ret += opcodes_list[NOP_OP]
            elif f0_value != None:
                ret += self.DP_MAP.get_ir_node(f0_value.ir_list_node)
            else:
                ret += "None"
            
            ret += " ; "

            if f1_value == NOP_OP:
                ret += opcodes_list[NOP_OP]
            elif f1_value != None:
                ret += self.DP_MAP.get_ir_node(f1_value.ir_list_node)
            else:
                ret += "None"
            ret += " ]\n"
        print(ret)



    def main_schedule(self):
        if (self.DEBUG_FLAG == True): print("[MAIN SCHEDULE]")
        # set number of nodes
        self.num_nodes = len(self.DP_MAP.nodes_map)
        if (self.DEBUG_FLAG == True):
            print(str(self.num_nodes) + " nodes")
        
        # initialize schedule
        # for i in range(1, self.num_nodes + 1):
        #     self.schedule[F0][i] = None
        #     self.schedule[F1][i] = None

        self.schedule_algo()
        self.print_schedule()
        # print(self.DP_MAP.nodes_map[1])
        # print(self.DP_MAP.get_ir_node(self.DP_MAP.nodes_map[1].ir_list_node))

        




        
    
    
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
            # print(edge)
            if (edge.kind == DATA):
                # print("[check_for_edge] the edge between parent and child is a data edge. do not add new special edge.")
                return True
        return False
                
    def print_retired(self):
        tmp = "[ "
        for node in self.DP_MAP.nodes_map.values():
            if (node.status == RETIRED):
                tmp += str(node.line_num)
                tmp += " "
        tmp += "]"
        print(tmp)
    

    # 🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈 NEW DEPENDENCE GRAPH 🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈
    
    def add_node(self, ir_node):
        """
            Given an ir node object, make a node and add to nodes list
            Node format:
              [IDX, line num, Full OP, type, delay, root boolean, leaf boolean, into edges list, out of edges list, status, arg1, arg2, arg3, priority]

        """
        # 1) Make node
        node = [0] * 14
        node[IDX_NODE] = len(self.nodes_list)   # 0
        node[LINE_NUM_NODE] = ir_node.line  # 1
        node[FULL_OP_NODE] = self.get_full_op(ir_node)  # 2
        node[TYPE_NODE] = ir_node.opcode    # 3
        if (node[TYPE_NODE] == LOAD_OP):
            node[DELAY_NODE] = LOAD_LATENCY # 4
        elif (node[TYPE_NODE] == LOADI_OP):
            node[DELAY_NODE] = LOADI_LATENCY
        elif (node[TYPE_NODE] == STORE_OP):
            node[DELAY_NODE] = STORE_LATENCY
        elif (node[TYPE_NODE] == ADD_OP):
            node[DELAY_NODE] = ADD_LATENCY
        elif (node[TYPE_NODE] == ADD_OP):
            node[DELAY_NODE] = ADD_LATENCY
        elif (node[TYPE_NODE] == SUB_OP):
            node[DELAY_NODE] = SUB_LATENCY
        elif (node[TYPE_NODE] == MULT_OP):
            node[DELAY_NODE] = MULT_LATENCY
        elif (node[TYPE_NODE] == LSHIFT_OP):
            node[DELAY_NODE] = LSHIFT_LATENCY
        elif (node[TYPE_NODE] == RSHIFT_OP):
            node[DELAY_NODE] = RSHIFT_LATENCY
        elif (node[TYPE_NODE] == OUTPUT_OP):
            node[DELAY_NODE] = OUTPUT_LATENCY
        elif (node[TYPE_NODE] == NOP_OP): # shouldnt happen but added just in case
            node[DELAY_NODE] = NOP_LATENCY
        node[ROOT_BOOL_NODE] = False # 5 ; dont know until later
        node[LEAF_BOOL_NODE] = False # 6 ; dont know until later
        node[INTO_EDGES_MAP_NODE] = {} # 7
        node[OUTOF_EDGES_MAP_NODE] = {}    # 8
        node[STATUS_NODE] = NOT_READY   # 9
        node[IR_ARG1_NODE] = ir_node.arg1   # 10
        node[IR_ARG2_NODE] = ir_node.arg2   # 11
        node[IR_ARG3_NODE] = ir_node.arg3   # 12
        node[PRIORITY_NODE] = 0 # 13

        # 2) Add to vr to node mapping but only when it defines
        vr = ir_node.arg3[1]
        if (vr not in self.VR_TO_NODE and vr != None):  # first time
            self.VR_TO_NODE[vr] = node[IDX_NODE]
        
        # 3) Add to nodes list
        self.nodes_list.append(node)
        
        # 4) return the node
        return node

    def add_data_edge(self, node):
        """
            Given a node in the graph, add a data edge
            for each VRj used in o, add an edge from o to the node in M(VRj)
            Edge format:
            [IDX, kind, latency, VR, parent idx, out of line num, child idx, into line num]
        """
        if (node[IR_ARG1_NODE][1] != None):
            into_node_idx = self.VR_TO_NODE[node[IR_ARG1_NODE][1]]
            into_node = self.nodes_list[into_node_idx]
            # print('ARG1 INTO NODE: ')
            # self.print_node(into_node)
            # make the edge
            edge = [0] * 8
            edge[IDX_EDGE] = len(self.edges_list)   # 0
            edge[KIND_EDGE] = DATA  # 1
            edge[LATENCY_EDGE] = into_node[DELAY_NODE]   # 2 ; latency of the edge is the delay of the first operation (into_node)
            edge[VR_EDGE] = node[IR_ARG1_NODE][1]  # 3
            edge[PARENT_IDX_EDGE] = node[IDX_NODE]  # 4
            edge[OUTOF_LINE_NUM_EDGE] = node[LINE_NUM_NODE]
            edge[CHILD_IDX_EDGE] = into_node[IDX_NODE]
            edge[INTO_LINE_NUM_EDGE] = into_node[LINE_NUM_NODE]

            # add the edge to the out of map
            node[OUTOF_EDGES_MAP_NODE][into_node[IDX_NODE]] = edge[IDX_EDGE]
            # add edge to child's into map
            into_node[INTO_EDGES_MAP_NODE][node[IDX_NODE]] = edge[IDX_EDGE]
            # add to edges list
            self.edges_list.append(edge)


        # arg2
        
        if (node[IR_ARG2_NODE][1] != None):
            into_node_idx = self.VR_TO_NODE[node[IR_ARG2_NODE][1]]
            into_node = self.nodes_list[into_node_idx]
            # print('ARG2 INTO NODE: ')
            # self.print_node(into_node)
            # make the edge
            edge = [0] * 8
            edge[IDX_EDGE] = len(self.edges_list)   # 0
            edge[KIND_EDGE] = DATA  # 1
            edge[LATENCY_EDGE] = into_node[DELAY_NODE]    # latency of the edge is the delay of the first operation (into_node)
            edge[VR_EDGE] = node[IR_ARG2_NODE][1]  # 3
            edge[PARENT_IDX_EDGE] = node[IDX_NODE]
            edge[OUTOF_LINE_NUM_EDGE] = node[LINE_NUM_NODE]
            edge[CHILD_IDX_EDGE] = into_node[IDX_NODE]
            edge[INTO_LINE_NUM_EDGE] = into_node[LINE_NUM_NODE]


            # add the edge to the out of map
            node[OUTOF_EDGES_MAP_NODE][into_node[IDX_NODE]] = edge[IDX_EDGE]
            # add edge to child's into map
            into_node[INTO_EDGES_MAP_NODE][node[IDX_NODE]] = edge[IDX_EDGE]
            # add to edges list
            self.edges_list.append(edge)

        
        if (node[IR_ARG3_NODE][1] != None and node[TYPE_NODE] == STORE_OP):
            into_node_idx = self.VR_TO_NODE[node[IR_ARG3_NODE][1]]
            into_node = self.nodes_list[into_node_idx]
            # print('ARG3 INTO NODE: ')
            # self.print_node(into_node)
            # make the edge
            edge = [0] * 8
            edge[IDX_EDGE] = len(self.edges_list)   # 0
            edge[KIND_EDGE] = DATA  # 1
            edge[LATENCY_EDGE] = into_node[DELAY_NODE]    # latency of the edge is the delay of the first operation (into_node)
            edge[VR_EDGE] = node[IR_ARG3_NODE][1]  # 3
            edge[PARENT_IDX_EDGE] = node[IDX_NODE]
            edge[OUTOF_LINE_NUM_EDGE] = node[LINE_NUM_NODE]
            edge[CHILD_IDX_EDGE] = into_node[IDX_NODE]
            edge[INTO_LINE_NUM_EDGE] = into_node[LINE_NUM_NODE]


            # add the edge to the out of map
            node[OUTOF_EDGES_MAP_NODE][into_node[IDX_NODE]] = edge[IDX_EDGE]
            # add edge to child's into map
            into_node[INTO_EDGES_MAP_NODE][node[IDX_NODE]] = edge[IDX_EDGE]
            # add to edges list
            self.edges_list.append(edge)
         
    def add_serial_edge(self, parent_node, child_node):
        """
            Add a serial edge from parent_node to child_node
        """
        # print("ADD SERIAL EDGE")
        edge = [0] * 8
        edge[IDX_EDGE] = len(self.edges_list)   # 0
        edge[KIND_EDGE] = SERIAL
        edge[LATENCY_EDGE] = 1 # "one cycle latency is enough"
        edge[VR_EDGE] = None
        edge[PARENT_IDX_EDGE] = parent_node[IDX_NODE]
        edge[OUTOF_LINE_NUM_EDGE] = parent_node[LINE_NUM_NODE]
        edge[CHILD_IDX_EDGE] = child_node[IDX_NODE]
        edge[INTO_EDGES_MAP_NODE] = child_node[LINE_NUM_NODE]

        # add the edge to the out of map
        parent_node[OUTOF_EDGES_MAP_NODE][child_node[IDX_NODE]] = edge[IDX_EDGE]
        # add edge to child's into map
        child_node[INTO_EDGES_MAP_NODE][parent_node[IDX_NODE]] = edge[IDX_EDGE]
        # add to edges list
        self.edges_list.append(edge)
        
    def add_conflict_edge(self, parent_node, child_node):
        """
            Add a serial edge from parent_node to child_node
            parent_node: second op
            child_node: first op
        """
        # print("ADD CONFLICR EDGE")
        edge = [0] * 8
        edge[IDX_EDGE] = len(self.edges_list)  # 0
        edge[KIND_EDGE] = CONFLICT
        edge[LATENCY_EDGE] = child_node[DELAY_NODE] # latency equal to the latency of the first operation
        edge[VR_EDGE] = None
        edge[PARENT_IDX_EDGE] = parent_node[IDX_NODE]
        edge[OUTOF_LINE_NUM_EDGE] = parent_node[LINE_NUM_NODE]
        edge[CHILD_IDX_EDGE] = child_node[IDX_NODE]
        edge[INTO_EDGES_MAP_NODE] = child_node[LINE_NUM_NODE]


        # add the edge to the out of map
        parent_node[OUTOF_EDGES_MAP_NODE][child_node[IDX_NODE]] = edge[IDX_EDGE]
        # add edge to child's into map
        child_node[INTO_EDGES_MAP_NODE][parent_node[IDX_NODE]] = edge[IDX_EDGE]
        # add to edges list
        self.edges_list.append(edge)
    
    def identify_roots_and_leaves(self):
        """
            To be done after all nodes and edges are added but before priorities computed
            For each node, determines if it is 
                a root (set node.root = true)
                a leaf (set node.leaf = true)
                or neither (do nothing)
            
            Returns mapping. key = 0, value = roots; key = 1, value = leaves
        """
        if (self.DEBUG_FLAG == True): print("[identify_roots_and_leaves]")
        tmp_roots = []
        tmp_leaves = []
        print("[identify_roots_and_leaves]")
        print(self.nodes_list)
        print("num nodes: " + str(len(self.nodes_list)))
        for node in self.nodes_list:
            if (len(node[INTO_EDGES_MAP_NODE]) == 0):
                node[ROOT_BOOL_NODE] = True
                tmp_roots.append(node)
            if (len(node[OUTOF_EDGES_MAP_NODE]) == 0):
                node[LEAF_BOOL_NODE] = True
                tmp_leaves.append(node)
        self.roots = tmp_roots
        self.leaves = tmp_leaves
    

    def get_full_op(self, node):
        """
            Given an IR node, returns the IR string representation
        """
        lh = ""
        rh = ""
        
        if (node.opcode == 0 or node.opcode == 1): # MEMOP
            lh = "r" + str(node.arg1[VR_IDX])
        elif (node.opcode == 2): # LOADI
            lh = str(node.arg1[SR_IDX])
        elif (node.opcode >= 3 and node.opcode <= 7):  # ARITHOP
            lh = "r" + str(node.arg1[VR_IDX]) + ",r" + str(node.arg2[VR_IDX]) 
        elif (node.opcode == 8): # OUTPUT
            lh = str(node.arg1[SR_IDX])
        
        if (node.opcode != 8):
            rh = "=> r" + str(node.arg3[VR_IDX])

        opcode = opcodes_list[node.opcode] + " "

        temp = opcode + lh + " " + rh
        return temp

    def NEW_convert_edge_map(self):
        """
            different graph representation
            convert edge list to map
            {parent idx : [(child idx, edge_latency), ...]}

        """
        print("NEW CONVERT EDGE MAP")
        print(self.edges_list)
        # self.node_edge_map = {node: [] for node in self.nodes_list}
        for node in self.nodes_list:
            self.node_edge_map[node[IDX_NODE]] = []
        for edge in self.edges_list:
            print(edge)
            parent_idx = edge[PARENT_IDX_EDGE]
            print(parent_idx)
            child_idx = edge[CHILD_IDX_EDGE]
            edge_latency = edge[LATENCY_EDGE]
            tuple = (child_idx, edge_latency)
            print(self.node_edge_map[parent_idx])
            self.node_edge_map[parent_idx].append(tuple)
        


    def NEW_print_edge_map(self):
        print("NEW print CONVERT EDGE MAP")

        tmp = "{"
        for parent_idx, edges in self.node_edge_map.items():
            print(parent_idx)
            tmp += str(self.nodes_list[parent_idx][LINE_NUM_NODE])
            tmp += ": ["
            for tuple in edges:
                child = self.nodes_list[tuple[0]]
                cunt = "(" + str(child[LINE_NUM_NODE]) + ", " + str(tuple[1]) + "), "
                tmp += cunt
            tmp += "], "
        tmp += "}"
        print(tmp)
    
    def NEW_set_priorities(self, start):
        """
            Start is a node in node format (list) from the roots
        """
        # initialized stack with the start node and its priority
        stack = [(start[IDX_NODE], 0)]
        print("NEW set priorities")

        while stack:
            # print("pussy- stack:")
            # print(stack)
            # print("end stack")

            current_node_idx, parent_priority = stack.pop()
            # print("current node:")
            # print(current_node_idx)

            # update priority for the current node only if its higher than the current priority
            cur_node = self.nodes_list[current_node_idx]
            current_priority = max(parent_priority, cur_node[PRIORITY_NODE])
            self.nodes_list[current_node_idx][PRIORITY_NODE] = current_priority

            # push neighbors onto stack in reverse order to match th eorder of recursive function
            for neighbor_idx, edge_latency in reversed(self.node_edge_map.get(current_node_idx, [])):
                print("Cunt")
                stack.append((neighbor_idx, current_priority + edge_latency))

    def print_dot(self):
        """
            Prints the dot file.
        """
        print("digraph DG {")
        self.print_nodes()
        # self.print_edges()
        for node in self.nodes_list:
            self.print_edges(node)
        print("}")
    
    def print_nodes(self):
        """
            format:   1 [label="1:  loadI  8 => r3"];
        """
        ret = ""
        for node in self.nodes_list:
            temp = "  " # indent
            temp += str(node[LINE_NUM_NODE])
            temp += ' [ label="'
            temp += str(node[LINE_NUM_NODE])
            temp += ":  "
            poo = node[FULL_OP_NODE]
            temp += poo
            # priority
            temp += '\n'
            temp += "prio:  "
            temp += str(node[PRIORITY_NODE])
            if (self.DEBUG_FLAG == True):
                temp += '\n'
                temp += "delay:  "
                temp += str(node[DELAY_NODE])

                if (node[ROOT_BOOL_NODE]):
                    temp += '\n'
                    temp += "root"
                if (node[LEAF_BOOL_NODE]):
                    temp += '\n'
                    temp += "leaf"
            temp += '"];'
            temp += '\n'
            ret += temp
        print(ret)
    

    def print_edges(self, node):
        """
            format of each node:   3 -> 1 [ label=" Data, vr3"];
              7 -> 6 [ label=" Conflict "];
            <line num of node edge is coming OUT OF (parent)> -> <line num of node edge is going INTO (child)> [ label = " <kind> "];
        """
        ret = ""
        
        for child_idx, edge_idx in node[OUTOF_EDGES_MAP_NODE].items():
            temp = "  " # indent
            temp += str(node[LINE_NUM_NODE])   # line num of node edge is coming OUT OF (parent)
            temp += " -> "
            edge = self.edges_list[edge_idx]
            temp += str(edge[INTO_LINE_NUM_EDGE]) # edge.into_line_num
            temp += ' [ label=" '
            if (edge[KIND_EDGE] != DATA):
                temp += self.kinds[edge[KIND_EDGE]]
            elif (edge[KIND_EDGE] == DATA):
                temp += self.kinds[edge[KIND_EDGE]]
                temp += ', vr'
                temp += str(edge[VR_EDGE])
            
            if (self.DEBUG_FLAG == True):
                temp += " ; Latency = "
                temp += str(edge[LATENCY_EDGE])
            temp += '"];'
            temp += '\n'
            ret += temp
        print(ret)
    

    def graph_consistency_checker(self):
        """
            Make sure that if node A thought it had an edge that ran to node B,
              node B also thought it had an edge that ran to node A
        """
        total_count = 0
        success_count = 0
        fail_count = 0
        for node in self.nodes_list:
            # print(node)
            # for each out edge (ex: edge ran to node b)
            for child_idx, parent_idx in node[OUTOF_EDGES_MAP_NODE].items():
                total_count += 1
                # get the child 
                child = self.nodes_list[child_idx]
                # get child's into edges
                into_edges = child[INTO_EDGES_MAP_NODE]   # key == node.linenum ()
                key_to_check = node[IDX_NODE]
                value_to_check = parent_idx
                # Check if the key is in into_edges and if the corresponding value matches
                if key_to_check in into_edges and into_edges[key_to_check] == value_to_check:
                    success_count += 1
                    # print(f"The key-value (parent node linenum, edge) pair ({key_to_check}: {value_to_check}) exists in into_edges.")
                else:
                    print(f"// The key-value (parent node linenum, edge) pair ({key_to_check}: {value_to_check}) does not exist in into_edges.")
                    fail_count += 1
        if (self.DEBUG_FLAG == True): print("// " + str(success_count) + " / " + str(total_count) + " into/outof edges correct")
    
    
    def NEW_check_for_edge(self, parent_node, child_node):
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
        if (child_node[IDX_NODE] in parent_node[OUTOF_EDGES_MAP_NODE]):
            # print("[check_for_edge] an edge exists already btwn parent and child")
            edge_idx = parent_node[OUTOF_EDGES_MAP_NODE][child_node[IDX_NODE]]
            edge = self.edges_list[edge_idx]
            # print(edge)
            if (edge[KIND_EDGE] == DATA):
                # print("[check_for_edge] the edge between parent and child is a data edge. do not add new special edge.")
                return True
        return False
    

    def NEW_main_schedule(self):
        if (self.DEBUG_FLAG == True): print("[MAIN SCHEDULE]")
        # set number of nodes
        self.num_nodes = len(self.nodes_list)
        if (self.DEBUG_FLAG == True):
            print(str(self.num_nodes) + " nodes")
        
        # initialize schedule
        # for i in range(1, self.num_nodes + 1):
        #     self.schedule[F0][i] = None
        #     self.schedule[F1][i] = None

        self.NEW_schedule_algo()
        self.NEW_print_schedule()
        # print(self.DP_MAP.nodes_map[1])
        # print(self.DP_MAP.get_ir_node(self.DP_MAP.nodes_map[1].ir_list_node))

    def NEW_schedule_algo(self):
        if (self.DEBUG_FLAG == True): print("[SCHEDULE ALGO]")

        cycle = 1
        # Sort the list in descending order based on the age attribute
        sorted_objects = sorted(self.leaves, key=lambda n: n[PRIORITY_NODE], reverse=True)
        ready = sorted_objects # array of nodes
        active = [] # array of pairs- (node, cycle that the node will come off the active list)

        # if (self.DEBUG_FLAG == True): self.print_ready(ready)

        if (self.DEBUG_FLAG == True): print("BEGINNING WHILE LOOP")
        if (self.DEBUG_FLAG == True): print(len(ready))
        if (self.DEBUG_FLAG == True): print(len(active))
        # Terminate when active and ready lists are empty
        while ((len(ready) == 0 and len(active) == 0) == False):
            self.NEW_print_statuses()
            if (self.DEBUG_FLAG == True): self.NEW_print_schedule()
            sorted_objects = sorted(ready, key=lambda n: n[PRIORITY_NODE], reverse=True)
            ready = sorted_objects # array of nodes
            if (self.DEBUG_FLAG == True): print("CYCLE: " + str(cycle))
            # Pick an operation, o, for each functional unit
            ops = self.NEW_get_operations_for_units(ready)

            early_release_ops = []
            
            if (self.DEBUG_FLAG == True):
                print(len(ops))
                print("OPS:")
                print(ops)

                self.NEW_print_ready(ready)
                self.NEW_print_active(active)
            f0_op = ops[F0]
            f1_op = ops[F1]
            # Move o from Ready to Active
            if (f0_op != NOP_OP):
                f0_op[STATUS_NODE] = ACTIVE
                active.append((f0_op, f0_op[DELAY_NODE] + cycle))
                if (f0_op[TYPE_NODE] == LOAD_OP or f0_op[TYPE_NODE] == STORE_OP or f0_op[TYPE_NODE] == OUTPUT_OP):
                    early_release_ops.append(f0_op)
            if (f1_op != NOP_OP):
                f1_op[STATUS_NODE] = ACTIVE
                active.append((f1_op, f1_op[DELAY_NODE] + cycle))
                if (f1_op[TYPE_NODE] == LOAD_OP or f1_op[TYPE_NODE] == STORE_OP or f1_op[TYPE_NODE] == OUTPUT_OP):
                    early_release_ops.append(f1_op)
            self.schedule[F0][cycle] = f0_op
            self.schedule[F1][cycle] = f1_op


            if (self.DEBUG_FLAG == True):
                print("ACTIVE AFTER APPENDING")
                self.NEW_print_active(active)

            # Increment cycle
            cycle += 1

            # get active ops that have retired
            retired = []
            for pair in active:
                if (pair[1] == cycle):
                    retired.append(pair)
                    pair[0][STATUS_NODE] = RETIRED
            

            # Find each op, o, in Active that retires
            for pair in retired:
                # Remove o from Active
                active.remove(pair)
                # For each op, d, that depends on o (into, d = parent)
                for parent_idx, edge_idx in pair[0][INTO_EDGES_MAP_NODE].items():
                    edge = self.edges_list[edge_idx]
                    d = self.nodes_list[edge[PARENT_IDX_EDGE]]
                    print("d:")
                    print(d[FULL_OP_NODE])
                    
                    all_ready = True
                    # check outof nodes of d
                    for child_idx, out_edge_idx in d[OUTOF_EDGES_MAP_NODE].items():
                        out_edge = self.edges_list[out_edge_idx]
                        child = self.nodes_list[child_idx]
                        # If d is now "ready" (operation that defined that operand is completed/retired- "If a node represents a use of a value, it has an edge to the node that defines that value")
                        if (child[STATUS_NODE] != RETIRED):
                            print("child retired")
                            all_ready = False
                    if (all_ready): # Add d to the Ready set
                        if (self.DEBUG_FLAG == True): print("Defining ops ready! Adding " + str(d[LINE_NUM_NODE]) + " to the ready set!")
                        if (d not in ready):
                            d[STATUS_NODE] = READY
                            ready.append(d)
                    else:
                        if (self.DEBUG_FLAG == True): print("Defining ops of " + str(d[LINE_NUM_NODE]) + " are not ready")


                        
            # If this iteration of the while loop added a load, store, or output operation to the active set, call it x

            # "for each operation y that has a serial dependence back to op in active_set,
            # If all the other dependences for y have been satisfied,
            # then y can move onto the Ready set now that operation op has been scheduled.
            # satisified means: all other non-serial dependences are finished and all serial dependences are scheduled
            multi_cycle_active = []
            for pair in active:
                if (pair[0][TYPE_NODE] == LOAD_OP or pair[0][TYPE_NODE] == STORE_OP or pair[0][TYPE_NODE] == OUTPUT_OP):
                    multi_cycle_active.append(pair)
                
            if (self.DEBUG_FLAG == True): 
                print("len(multi_cycle_active) = " + str(len(multi_cycle_active)) + " vs. len(early_release_ops) = " + str(len(early_release_ops)))
            
            # # Find each multi-cycle (load, store, mult) operation o in Active
            # for pair in early_release_ops:
            #     # Check operations that depend on o for early releases (into, parent)
            #     #for each operation y that has a serial dependence back to op in active_set
            #     for parent_linenum, edge in pair[0].into_edges.items():
            #         satisfied = True
            #         if (edge.kind == SERIAL):
            #             y = edge.parent
            #             # check all dependences of edge.parent (y)
            #             for pl, e in y.outof_edges.items():
            #                 # check all non-serial dependences are finished 
            #                 if (e.kind == SERIAL):
            #                     if (e.child.status != ACTIVE):
            #                         satisfied = False
            #                 else:
            #                     if (e.child.status != RETIRED):
            #                         satisfied = False
            #             if (satisfied): # Add y to the Ready set
            #                 if (self.DEBUG_FLAG == True): print("early release- Adding " + str(d.line_num) + " to the ready set!")
            #                 y.status = READY
            #                 ready.append(y)
            #             else:
            #                 if (self.DEBUG_FLAG == True): print("early release- Depending ops of " + str(d.line_num) + " are not ready")

        
    def NEW_get_operations_for_units(self, ready):
        """
            Get an operation for each functional unit based on the highest priority and remove those from ready
                and these constraints:
                Load and store operations: only f0
                loadI: f0 or f1
                Mult: f1
                Output: f0 or f1, but only one per cycle (latency == cycle counts)
            
            returns array where index 0 is node for f0 and index 1 is node for f1
        """
        f0_node = None
        f1_node = None


        if (self.DEBUG_FLAG == True):
            print("[get_operations_for_units]")
            print("READY BEFORE")
            self.NEW_print_ready(ready)


        if (len(ready) == 0):
            return [NOP_OP, NOP_OP]
        
        
        num_restricted = 0
        restricted_ready = []
        unrestricted_ready = []
        for node in ready:
            if (node[TYPE_NODE] == LOAD_OP or node[TYPE_NODE] == STORE_OP or node[TYPE_NODE] == MULT_OP or node[TYPE_NODE] == OUTPUT_OP):
                num_restricted += 1
                node[STATUS_NODE] = READY
                restricted_ready.append(node)
            else:
                unrestricted_ready.append(node)
                node[STATUS_NODE] = READY
      
        if (self.DEBUG_FLAG == True):
            print("RESTRICTED READY:")
            self.NEW_print_ready(restricted_ready)
            print("UNRESTRICTED READY:")
            self.NEW_print_ready(unrestricted_ready)

        # 🔒🔒🔒🔒🔒🔒🔒 First, restricted nodes 🔒🔒🔒🔒🔒🔒🔒🔒
        # f0
        for node in restricted_ready:
            # at least one unit still open
            if (f0_node == None or f1_node == None):
                # only on f0
                if (node[TYPE_NODE] == LOAD_OP or node[TYPE_NODE] == STORE_OP):
                    if (f0_node == None): # hasnt been assigned yet
                        f0_node = node
                # only on f1
                if (node[TYPE_NODE] == MULT_OP):
                    if (f1_node == None): # hasnt been assigned yet
                        f1_node = node
                # takes whole cycle
                if (node[TYPE_NODE] == OUTPUT_OP):
                    # havent already assigned either unit
                    if (f0_node == None and f1_node == None):
                        f0_node = node
                        f1_node = NOP_OP
                        ready.remove(node)
                        return [f0_node, f1_node]
        
        # check if we have filled f0 and f1
        if (f0_node != None and f1_node != None):
            if (f0_node in ready):  # havent already removed
                ready.remove(f0_node)
            if (f1_node in ready):  # havent already removed
                ready.remove(f1_node)
            return [f0_node, f1_node]

        # check we have removed everything
        if (f0_node != None and f0_node in ready):
            ready.remove(f0_node)
        if (f0_node != None and f0_node in restricted_ready):
            restricted_ready.remove(f0_node)
        if (f1_node != None and f1_node in ready):
            ready.remove(f1_node)
        if (f1_node != None and f1_node in restricted_ready):
            restricted_ready.remove(f1_node)
        

        # 🔒🔒🔒🔒🔒🔒 END OF RESTRICTED READY PRIORITY 🔒🔒🔒🔒🔒🔒🔒🔒🔒

        # ❄️❄️❄️❄️❄️❄️ Next, prioritize loadI ❄️❄️❄️❄️❄️❄️❄️❄️❄️
        # see if there is a loadI we can put in the empty slot
        for node in unrestricted_ready:
            if (node[TYPE_NODE] == LOADI_OP):
                # check that it is not somehow already one of the issue slots
                if (f0_node != node and f1_node != node):
                    # find the open slot
                    if (f0_node == None):
                        f0_node = node
                    elif (f1_node == None):
                        f1_node = node
        # check we remove everything
        if (f0_node in ready):
            ready.remove(f0_node)
        if (f0_node in unrestricted_ready):
            unrestricted_ready.remove(f0_node)
        if (f1_node in ready):
            ready.remove(f1_node)
        if (f1_node in unrestricted_ready):
            unrestricted_ready.remove(f1_node)
        
        # check if we have filled f0 and f1
        if (f0_node != None and f1_node != None):
            return [f0_node, f1_node]
        
        # ❄️❄️❄️❄️❄️❄️❄️❄️ END OF LOADI PRIORITY ❄️❄️❄️❄️❄️❄️❄️❄️❄️❄️

        # 🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈 Priority based from unrestricted list 🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈
        # check if there is anything in unrestricted_ready
        if (len(unrestricted_ready) == 0):
            # nothing else to do so we need to make the issue slot and return
            if (f0_node == None):
                f0_node = NOP_OP
            if (f1_node == None):
                f1_node = NOP_OP
            # return
            return [f0_node, f1_node]

        # check if there is only one thing in unrestricted ready, so return
        if (len(unrestricted_ready) == 1):
            # find the empty slot
            # both slots open
            if (f0_node == None and f1_node == None):
                f0_node = unrestricted_ready[0]
                f1_node = NOP_OP
            # only one slot open
            elif (f0_node == None):
                f0_node = unrestricted_ready[0]
            elif (f1_node == None):
                f1_node = unrestricted_ready[0]
            
            # check we remove everything
            if (f0_node in ready):
                ready.remove(f0_node)
            if (f0_node in unrestricted_ready):
                unrestricted_ready.remove(f0_node)
            if (f1_node in ready):
                ready.remove(f1_node)
            if (f1_node in unrestricted_ready):
                unrestricted_ready.remove(f1_node)
            # return
            return [f0_node, f1_node]

        if (len(unrestricted_ready) == 2):
            # both open
            if (f0_node == None and f1_node == None):
                f0_node = unrestricted_ready[0]
                f1_node = unrestricted_ready[1]
            elif (f0_node == None):
                # idx 0 is highest priority value
                f0_node = unrestricted_ready[0]
            elif (f1_node == None):
                # idx 0 is highest priority value
                f1_node = unrestricted_ready[0]
            # check we remove everything
            if (f0_node in ready):
                ready.remove(f0_node)
            if (f0_node in unrestricted_ready):
                unrestricted_ready.remove(f0_node)
            if (f1_node in ready):
                ready.remove(f1_node)
            if (f1_node in unrestricted_ready):
                unrestricted_ready.remove(f1_node)
            # return
            return [f0_node, f1_node]
                


        # get highest priority node from unrestricted ready
        if (len(unrestricted_ready) > 2):
            highest_priority = []
            first_node_prior = unrestricted_ready[0].priority    # bc sorted
            # check if there are multiple of the same priority
            for node in unrestricted_ready:
                if (node[PRIORITY_NODE] == first_node_prior):
                    highest_priority.append(node)
            
            if (self.DEBUG_FLAG == True):
                print("HIGHEST PRIORITY:")
                self.NEW_print_ready(highest_priority)
                print("READY AFTER:")
                self.NEW_print_ready(ready)


            # Find operation for f0
            if (f0_node == None):
                for node in highest_priority:
                    if (node[TYPE_NODE] != MULT_OP):
                        f0_node = node
                        break

            # if we found an f0 node
            if (f0_node != None):
                # remove from list with highest priority nodes
                if (f0_node in highest_priority):
                    highest_priority.remove(f0_node)
                # remove f0_node from ready
                if (f0_node in ready):
                    ready.remove(f0_node)
                # remove from unrestricted
                if (f0_node in unrestricted_ready):
                    unrestricted_ready.remove(f0_node)

                if (self.DEBUG_FLAG == True):
                    print("HIGHEST PRIORITY AFTER F0NODE:")
                    self.NEW_print_ready(highest_priority)
                
                # output can only have one per cycle
                if f0_node[TYPE_NODE] == OUTPUT_OP:
                    return [f0_node, NOP_OP]
                

                # if f0 took the only highest priority node, recompute highest priority nodes
                if (len(highest_priority) == 0):
                    
                    if (self.DEBUG_FLAG == True):
                        print("READY AFTER REMOVE F0NODE:")
                        self.NEW_print_ready(ready)
                    
                    # if nothing left in ready, just return
                    if (len(ready) == 0):
                        return [f0_node, NOP_OP]
                    else:
                        first_node_prior = unrestricted_ready[0].priority    # bc sorted
                        for node in unrestricted_ready:
                            if (node[PRIORITY_NODE] == first_node_prior):
                                highest_priority.append(node)
            else:
                # set to nop if we didn't find anything
                f0_node = NOP_OP
            
            if (self.DEBUG_FLAG == True):
                print("HIGHEST PRIORITY B4 f1:")
                self.print_ready(highest_priority)
                print("READY B4 f1:")
                self.print_ready(ready)
            

            
            # Find operation for f1
            if (f1_node == None):
                for node in highest_priority:
                    if (node[TYPE_NODE] != LOAD_OP and node[TYPE_NODE] != STORE_OP):
                        f1_node = node
                        break
            
            # if we didnt find an f1 node
            if (f1_node == None):
                # set to nop if we didn't find anything
                f1_node = NOP_OP
            else:   # if we found an f1 node
                if (f1_node in ready):
                    ready.remove(f1_node)
                if (f1_node in unrestricted_ready):
                    unrestricted_ready.remove(f1_node)
                if (f1_node in highest_priority):
                    highest_priority.remove(f1_node)
            
        # double check that neither are None
        if (f0_node == None):
            f0_node = NOP_OP
        if (f1_node == None):
            f1_node = NOP_OP
        ret = [f0_node, f1_node]
        if (self.DEBUG_FLAG == True):
            print("RETURN VALUE:")
            print(ret)
        
        return ret
    

    def NEW_print_ready(self, ready):
        ret = "["
        for node in ready:
            tmp = "<" + str(node[LINE_NUM_NODE]) + " " + str(opcodes_list[node[TYPE_NODE]]) + " , " + str(node[PRIORITY_NODE]) + ">, "
            ret += tmp
        ret += "]"
        print(ret)

    
    def NEW_print_active(self, active):
        ret = "["
        for pair in active:
            tmp = "<" + str(pair[0][LINE_NUM_NODE]) + " " + str(opcodes_list[pair[0][TYPE_NODE]]) + " , #" + str(pair[1]) + ">, "
            ret += tmp
        ret += "]"
        print(ret)

    
    def NEW_print_schedule(self):
        sched_len = len(self.schedule[F0])
        print("F0:")
        print(self.schedule[F0])

        for node in self.schedule[F0]:
            print(node)
        print("F1:")
        print(self.schedule[F1])

        for node in self.schedule[F1]:
            print(node)

        print("SCHEDULE LEN: " + str(sched_len))
        ret = ""
        for i in range(1, sched_len + 1):
            ret += "[ "
            f0_value = self.schedule[F0][i]
            f1_value = self.schedule[F1][i]
            if f0_value == NOP_OP:
                ret += opcodes_list[NOP_OP]
            elif f0_value != None:
                ret += f0_value[FULL_OP_NODE]
            else:
                ret += "None"
            
            ret += " ; "

            if f1_value == NOP_OP:
                ret += opcodes_list[NOP_OP]
            elif f1_value != None:
                ret += f1_value[FULL_OP_NODE]
            else:
                ret += "None"
            ret += " ]\n"
        print(ret)

    def NEW_print_statuses(self):
        for node in self.nodes_list:
            print(node[FULL_OP_NODE] + " : " + str(node[STATUS_NODE]))

    # 🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈

       



    

    


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
        print("     -g [filename]       Runs lab3 but only builds the graph (i.e. doesn't do scheduling)")
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
        GRAPH_ONLY = False
        if (sys.argv[1] == '-x'):
            DEBUG_FLAG = True
        
        if (sys.argv[1] == '-g'):
            GRAPH_ONLY = True


        
        Lab_3 = Lab3(Lab_2.IR_LIST, DEBUG_FLAG, GRAPH_ONLY)
        # if (sys.argv[1] == '-n'):
        #     GRAPH_ONLY = True
        #     DEBUG_FLAG = True
        #     Lab_3.build_new_graph()
        # else:
        #     Lab_3.build_graph()

        Lab_3.build_new_graph()

        # Lab_3.build_graph()
        

        if (GRAPH_ONLY == False):
            Lab_3.NEW_main_schedule()
            # Lab_3.main_schedule()
    
    # pr.disable()
    # s = StringIO()
    # sortby = 'cumulative'
    # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    # ps.print_stats()
    # sys.stdout.write(s.getvalue())



if __name__ == "__main__":
  main()
