
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

# EDGE KIND
DATA = 0
SERIAL = 1
CONFLICT = 2

# INDEXES
SR_IDX = 0
VR_IDX = 1
PR_IDX = 2
NU_IDX = 3

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

opcodes_list = ["load", "store", "loadI", "add", "sub", "mult", "lshift", "rshift", "output", "nop"]

# STATUSES
NOT_READY = 1
READY = 2
ACTIVE = 3
RETIRED = 4



class Edge:
    """
        format:   3 -> 1 [ label=" Data, vr3"];
        <line num of node edge is coming OUT OF (parent)> -> <line num of node edge is going INTO (child)> [ label = " <kind> "];
    """
    def __init__(self):
        """
            kind: type- INT; Data, Serial, Conflict
            latency: 
        """
        self.kind = None    # type- INT; Data, Serial, Conflict
        self.latency = None # type- INT
        self.vr = None      # type- INT; Which value is flowing on the edge; Only defined if kind is Data
        
        # bidirectional
        self.parent = None  # type- OperationNode; where the edge is coming OUT OF
        self.outof_line_num = None  # line num of parent node
        self.child = None   # type- OperationNode; where the edge is going INTO (i.e. the side that has the arrow)
        self.into_line_num = None   # line num of child node
    def __str__(self):
        temp_str = ""
        if (self.kind == DATA):
            tmp = "DATA, vr" + str(self.vr)
            temp_str += tmp
        elif (self.kind == SERIAL):
            tmp = "SERIAL"
            temp_str += tmp
        elif (self.kind == CONFLICT):
            tmp = "CONFLICT"
            temp_str += tmp

        temp = " - parent line num: " + str(self.outof_line_num) + "; child line num: " + str(self.into_line_num)
        temp_str += temp
        return temp_str


class OperationNode:
    def __init__(self):
        self.line_num = None  # type- INT
        self.ir_list_node = None # type- Node in IR_List.py; reference to the node in the IR_List that corresponds to this operation node
        self.type = None    # opcode
        self.delay = None     # latency of that opcode
        self.latency_weighted_len = []  # array in case there are multiple roots
        self.max_latency_weighted_length = 0    # longest path from this node to root
        self.root = False   # true if this node is a root (len(into_edges) == 0), false otherwise
        self.leaf = False   # true if this node is a leaf (len(outof_edges) == 0), false otherwise
        self.priority = 0
        self.into_edges = {}      # Edges going INTO this node; line num of parent mapped to edge between this node and parent
        self.outof_edges = {}       # Edges coming OUT OF this node; line num of child mapped to edge between this node and child

        # scheduling
        self.status = NOT_READY
    
    def __str__(self):
        temp_str = ""
        temp_str += str(self.line_num)
        temp_str += ": "
        ir_node = self.node_get_ir_node(self.ir_list_node)
        temp_str += ir_node
        temp_str += " num into edges: "
        temp_str += str(len(self.into_edges))
        temp_str += " ; num out of edges: "
        temp_str += str(len(self.outof_edges))
        return temp_str





    def node_get_ir_node(self, node):
        """
            Given a dependence graph node, returns the IR representation
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
    # def add_into_edge(self, edge):
    #     """

    #     """
        
    #     self.into_edges.append(edge)
    
    # def add_outof_edge(self, edge):
    #     self.outof_edges.append(edge)




class DependenceGraph:
    def __init__(self, DEBUG_FLAG):
        """
            nodes: map line num (from renamed block) of node to operation node; contains type Node
            edges: map line num of node that the edge is coming OUT OF (parent) to the edge; contains type Edge
        """
        self.DEBUG_FLAG = DEBUG_FLAG
        self.VR_TO_NODE = {}
        self.nodes_map = {} # line num to node
        self.edge_list = []

        # map line num of node that the edge is coming OUT OF (parent) to the edge; contains type Edge
        self.kinds = ["Data", "Serial", "Conflict"]
        self.opcodes_list = ["load", "store", "loadI", "add", "sub", "mult", "lshift", "rshift", "output", "nop"]

    

    def add_node(self, ir_list_node):
        """
            Currently only implementing for data nodes
            Add node to nodes map that is keyed by node's line number
            node: node to add to the nodes map
        """
        # print("ADD NODE")
        # Make node
        node = OperationNode()
        node.line_num = ir_list_node.line
        node.ir_list_node = ir_list_node
        node.type = ir_list_node.opcode
  
        
        if (node.type == LOAD_OP):
            node.delay = LOAD_LATENCY
        elif (node.type == LOADI_OP):
            node.delay = LOADI_LATENCY
        elif (node.type == STORE_OP):
            node.delay = STORE_LATENCY
        elif (node.type == ADD_OP):
            node.delay = ADD_LATENCY
        elif (node.type == ADD_OP):
            node.delay = ADD_LATENCY
        elif (node.type == SUB_OP):
            node.delay = SUB_LATENCY
        elif (node.type == MULT_OP):
            node.delay = MULT_LATENCY
        elif (node.type == LSHIFT_OP):
            node.delay = LSHIFT_LATENCY
        elif (node.type == RSHIFT_OP):
            node.delay = RSHIFT_LATENCY
        elif (node.type == OUTPUT_OP):
            node.delay = OUTPUT_LATENCY
        elif (node.type == NOP_OP): # shouldnt happen but added just in case
            node.delay = NOP_LATENCY
        

        # TODO: priority, but i think that is not at intially adding the node,but this is a reminder that it is a field in Node
            


        # Add to mapping
        # only do this when it defines
        vr = ir_list_node.arg3[1]
        if vr not in self.VR_TO_NODE and vr != None:   # first time
            self.VR_TO_NODE[vr] = node
        # add to node list
        self.nodes_map[node.line_num]= node
        return node

    def add_conflict_edge(self, parent_node, child_node):
        """
            Add a serial edge from parent_node to child_node
            parent_node: second op
            child_node: first op
        """
        # print("ADD CONFLICR EDGE")
        edge = Edge()
        edge.kind = CONFLICT
        edge.latency = child_node.delay # latency equal to the latency of the first operation
        edge.parent = parent_node
        edge.outof_line_num = parent_node.line_num
        edge.child = child_node
        edge.into_line_num = child_node.line_num

        # add the edge to the out of map
        parent_node.outof_edges[child_node.line_num] = edge
        # add edge to child's into map
        child_node.into_edges[parent_node.line_num] = edge
        self.edge_list.append(edge)

    def add_serial_edge(self, parent_node, child_node):
        """
            Add a serial edge from parent_node to child_node
        """
        # print("ADD SERIAL EDGE")
        edge = Edge()
        edge.kind = SERIAL
        edge.latency = 1 # "one cycle latency is enough"
        edge.parent = parent_node
        edge.outof_line_num = parent_node.line_num
        edge.child = child_node
        edge.into_line_num = child_node.line_num

        # add the edge to the out of map
        parent_node.outof_edges[child_node.line_num] = edge
        # add edge to child's into map
        child_node.into_edges[parent_node.line_num] = edge
        self.edge_list.append(edge)





    
    def add_data_edge(self, node):
        """
            Add a data edge
            for each VRj used in o, add an edge from o to the node in M(VRj)
        """
        # print('ADD DATA EDGE')
        # print(node.ir_list_node.arg1)
        # print(node.ir_list_node.arg2)
        # print(node.ir_list_node.arg3)
        # add out of nodes- data
        # for each VRj used in o, add an edge from o to the node in M(VRj)
        # arg1
        if (node.ir_list_node.arg1[1] != None):
            into_node = self.VR_TO_NODE[node.ir_list_node.arg1[1]]
            # print('ARG1 INTO NODE: ')
            # self.print_node(into_node)
            # make the edge
            edge = Edge()
            edge.kind = DATA
            edge.latency = into_node.delay    # latency of the edge is the delay of the first operation (into_node)
            edge.vr = node.ir_list_node.arg1[1]
            edge.parent = node
            edge.outof_line_num = node.line_num
            edge.child = into_node
            edge.into_line_num = into_node.line_num

            # add the edge to the out of map
            node.outof_edges[into_node.line_num] = edge
            # add edge to child's into map
            into_node.into_edges[node.line_num] = edge
            self.edge_list.append(edge)


        # arg2
        
        if (node.ir_list_node.arg2[1] != None):
            into_node = self.VR_TO_NODE[node.ir_list_node.arg2[1]]
            # print('ARG2 INTO NODE: ')
            # self.print_node(into_node)
            # make the edge
            edge = Edge()
            edge.kind = DATA
            edge.latency = into_node.delay    # latency of the edge is the delay of the first operation (into_node)
            edge.vr = node.ir_list_node.arg2[1]
            edge.parent = node
            edge.outof_line_num = node.line_num
            edge.child = into_node
            edge.into_line_num = into_node.line_num

            # add the edge to the out of map
            node.outof_edges[into_node.line_num] = edge
            # add edge to child's into map
            into_node.into_edges[node.line_num] = edge
            self.edge_list.append(edge)

        
        if (node.ir_list_node.arg3[1] != None and node.ir_list_node.opcode == STORE_OP):
            into_node = self.VR_TO_NODE[node.ir_list_node.arg3[1]]
            # print('ARG3 INTO NODE: ')
            # self.print_node(into_node)
            # make the edge
            edge = Edge()
            edge.kind = DATA
            edge.latency = into_node.delay    # latency of the edge is the delay of the first operation (into_node)
            edge.vr = node.ir_list_node.arg3[1]
            edge.parent = node
            edge.outof_line_num = node.line_num
            edge.child = into_node
            edge.into_line_num = into_node.line_num

            # add the edge to the out of map
            node.outof_edges[into_node.line_num] = edge
            # add edge to child's into map
            into_node.into_edges[node.line_num] = edge
            self.edge_list.append(edge)

    
    def get_ir_node(self, node):
        """
            Given an IR node, returns the IR representation
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

        opcode = self.opcodes_list[node.opcode] + " "

        temp = opcode + lh + " " + rh
        return temp


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
        roots = []
        leaves = []
        for line_num, node in self.nodes_map.items():
            if (len(node.into_edges) == 0):
                node.root = True
                roots.append(node)
            if (len(node.outof_edges) == 0):
                node.leaf = True
                leaves.append(node)
        roots_and_leaves = {0: roots, 1: leaves}
        return roots_and_leaves




    
    def print_dot(self):
        """
            Prints the dot file.
        """
        print("digraph DG {")
        self.print_nodes()
        # self.print_edges()
        for line_num, node in self.nodes_map.items():
            self.print_edges(node)
        print("}")

    def print_nodes(self):
        """
            format:   1 [label="1:  loadI  8 => r3"];
        """
        ret = ""
        for line_num, node in self.nodes_map.items():
            temp = "  " # indent
            temp += str(node.line_num)
            temp += ' [ label="'
            temp += str(node.line_num)
            temp += ":  "
            poo = self.get_ir_node(node.ir_list_node)
            temp += poo
            # priority
            temp += '\n'
            temp += "prio:  "
            temp += str(node.priority)
            if (self.DEBUG_FLAG == True):
                temp += '\n'
                temp += "delay:  "
                temp += str(node.delay)

                if (node.root):
                    temp += '\n'
                    temp += "root"
                if (node.leaf):
                    temp += '\n'
                    temp += "leaf"
            temp += '"];'
            temp += '\n'
            ret += temp
        print(ret)
    
    def print_node(self, node):
        print("  " + str(node.line_num) + ' [ label="' + str(node.line_num) + ":  " + self.get_ir_node(node.ir_list_node) + ' "];')

    def print_vrtonode(self):
        print("VR_TO_NODE = {")
        for key, value in self.VR_TO_NODE.items():
            print("r" + str(key) + ": (" + str(value.line_num) + ' [ label="' + str(value.line_num) + ":  " + self.get_ir_node(value.ir_list_node) + ' "];' +")")
        
        print("}")


    
    def print_edges(self, node):
        """
            format of each node:   3 -> 1 [ label=" Data, vr3"];
              7 -> 6 [ label=" Conflict "];
            <line num of node edge is coming OUT OF (parent)> -> <line num of node edge is going INTO (child)> [ label = " <kind> "];
        """
        ret = ""
        
        for key, edge in node.outof_edges.items():
            temp = "  " # indent
            temp += str(node.line_num)   # line num of node edge is coming OUT OF (parent)
            temp += " -> "
            temp += str(key) # edge.into_line_num
            temp += ' [ label=" '
            if (edge.kind != DATA):
                temp += self.kinds[edge.kind]
            elif (edge.kind == DATA):
                temp += self.kinds[edge.kind]
                temp += ', vr'
                temp += str(edge.vr)
            
            if (self.DEBUG_FLAG == True):
                temp += " ; Latency = "
                temp += str(edge.latency)
            temp += '"];'
            temp += '\n'
            ret += temp
        print(ret)
    

    # CHECKING FUNCTIONS
    def graph_consistency_checker(self):
        """
            Make sure that if node A thought it had an edge that ran to node B,
              node B also thought it had an edge that ran to node A
        """
        total_count = 0
        success_count = 0
        fail_count = 0
        for line_num, node in self.nodes_map.items():
            # print(node)
            # for each out edge (ex: edge ran to node b)
            for child_linenum, edge in node.outof_edges.items():
                total_count += 1
                # get the child 
                child = edge.child
                # get child's into edges
                into_edges = child.into_edges   # key == node.linenum ()
                key_to_check = node.line_num
                value_to_check = edge
                # Check if the key is in into_edges and if the corresponding value matches
                if key_to_check in into_edges and into_edges[key_to_check] == value_to_check:
                    success_count += 1
                    # print(f"The key-value (parent node linenum, edge) pair ({key_to_check}: {value_to_check}) exists in into_edges.")
                else:
                    print(f"// The key-value (parent node linenum, edge) pair ({key_to_check}: {value_to_check}) does not exist in into_edges.")
                    fail_count += 1
        if (self.DEBUG_FLAG == True): print("// " + str(success_count) + " / " + str(total_count) + " into/outof edges correct")

                

            
            


