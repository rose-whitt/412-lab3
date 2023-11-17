
# ASSUMED DELAYS
LOAD_DELAY = 3  # TODO: need to do calculation on pag 637
LOADI_DELAY = 1
LSHIFT_DELAY = 1
ADD_DELAY = 2
STORE_DELAY = 4

# EDGE KIND
DATA = 0
SERIAL = 1
CONFLICT = 2

# INDEXES
SR_IDX = 0
VR_IDX = 1
PR_IDX = 2
NU_IDX = 3


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


class OperationNode:
    def __init__(self):
        self.line_num = None  # type- INT
        self.ir_list_node = None # type- Node in IR_List.py; reference to the node in the IR_List that corresponds to this operation node
        self.type = None    # opcode
        self.delay = None     # latency of that opcode
        self.into_edges = []       # array of Edges going INTO this node
        self.outof_edges = []       # array of Edges coming OUT OF this node
    
    # def add_into_edge(self, edge):
    #     """

    #     """
        
    #     self.into_edges.append(edge)
    
    # def add_outof_edge(self, edge):
    #     self.outof_edges.append(edge)




class DependenceGraph:
    def __init__(self):
        """
            nodes: map line num (from renamed block) of node to operation node; contains type Node
            edges: map line num of node that the edge is coming OUT OF (parent) to the edge; contains type Edge
        """
        self.VR_TO_NODE = {}
        self.nodes_list = []

        # map line num of node that the edge is coming OUT OF (parent) to the edge; contains type Edge
        self.kinds = ["Data", "Serial", "Conflict"]
        self.opcodes_list = ["load", "store", "loadI", "add", "sub", "mult", "lshift", "rshift", "output", "nop"]
    

    def add_node(self, ir_list_node):
        """
            Currently only implementing for data nodes
            Add node to nodes map that is keyed by node's line number
            node: node to add to the nodes map
        """
        # Make node
        node = OperationNode()
        node.line_num = ir_list_node.line
        node.ir_list_node = ir_list_node
        node.type = ir_list_node.opcode
        
        


        # TODO: delay

        # Add to mapping
        # TODO: only do this when it defines
        vr = ir_list_node.arg3[1]
        if vr not in self.VR_TO_NODE and vr != None:   # first time
            self.VR_TO_NODE[vr] = node
        # add to node list
        self.nodes_list.append(node);

    
    
    def add_edge(self, node):
        print('ADD EDGE')
        print(node.ir_list_node.arg1)
        print(node.ir_list_node.arg2)
        print(node.ir_list_node.arg3)
        # add out of nodes- data
        # for each VRj used in o, add an edge from o to the node in M(VRj)
        # arg1
        if (node.ir_list_node.arg1[1] != None):
            into_node = self.VR_TO_NODE[node.ir_list_node.arg1[1]]
            print('ARG1 INTO NODE: ')
            self.print_node(into_node)
            # make the edge
            edge = Edge()
            edge.kind = DATA
            edge.latency = 0    # idk
            edge.vr = node.ir_list_node.arg1[1]
            edge.parent = node
            edge.outof_line_num = node.line_num
            edge.child = into_node
            edge.into_line_num = into_node.line_num

            # add the edge to the out of list
            node.outof_edges.append(edge)
            # add edge to child's into list
            into_node.into_edges.append(edge)

        # arg2
        
        if (node.ir_list_node.arg2[1] != None):
            into_node = self.VR_TO_NODE[node.ir_list_node.arg2[1]]
            print('ARG2 INTO NODE: ')
            self.print_node(into_node)
            # make the edge
            edge = Edge()
            edge.kind = DATA
            edge.latency = 0    # idk
            edge.vr = node.ir_list_node.arg2[1]
            edge.parent = node
            edge.outof_line_num = node.line_num
            edge.child = into_node
            edge.into_line_num = into_node.line_num

            # add the edge to the out of list
            node.outof_edges.append(edge)
            # add edge to child's into list
            into_node.into_edges.append(edge)
    
    def get_ir_node(self, node):
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

        opcode = self.opcodes_list[node.opcode] + " "

        temp = opcode + lh + " " + rh
        return temp
    
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
            temp += str(node.line_num)
            temp += ' [ label="'
            temp += str(node.line_num)
            temp += ":  "
            poo = self.get_ir_node(node.ir_list_node)
            temp += poo
            temp += ' "];'
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
        
        for edge in node.outof_edges:
            temp = "  " # indent
            temp += str(node.line_num)   # line num of node edge is coming OUT OF (parent)
            temp += " -> "
            temp += str(edge.into_line_num)
            temp += ' [ label=" '
            if (edge.kind != DATA):
                temp += self.kinds[edge.kind]
                temp += ' "];'
            elif (edge.kind == DATA):
                temp += self.kinds[edge.kind]
                temp += ', vr'
                temp += str(edge.vr)
                temp += ' "];'
            temp += '\n'
            ret += temp
        print(ret)

            
            


