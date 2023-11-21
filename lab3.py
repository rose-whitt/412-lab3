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

        # scheduling
        # initialize both unit dictionaries to have number of nodes issue slots
        #  each keyed 1 - number of nodes, with the value being None, but will be replaced by node
        self.schedule = {F0: {}, F1: {}}    
        self.num_nodes = 0

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
            self.debuprint("RESTRICTED READY:")
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
            if (f1_op != NOP_OP):
                f1_op.status = ACTIVE
                active.append((f1_op, f1_op.delay + cycle))
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
                    d = edge.parent
                    
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


                        
            
            # # TODO: (DO LATER BC ITS FOR EFFECTIVENESS NOT CORRECTNESS)
            # multi_cycle_active = []
            # for pair in active:
            #     if (pair[0].type == LOAD_OP or pair[0].type == STORE_OP or pair[0].type == MULT_OP):
            #         multi_cycle_active.append(pair)
            # # Find each multi-cycle (load, store, mult) operation o in Active
            # for pair in multi_cycle_active:
            #     # Check operations that depend on o for early releases (into, parent)
            #     for parent_linenum, edge in pair[0].into_edges.items():
            #         if (edge.kind == SERIAL):
            #             # Add any early release to ready
            #             if (edge.parent not in ready):
            #                 edge.parent.status = READY
            #                 ready.append(edge.parent)



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
        Lab_3.main_schedule()



if __name__ == "__main__":
  main()
