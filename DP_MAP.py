
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
    
    def add_into_edge(self, edge):
        self.into_edges.append(edge)
    
    def add_outof_edge(self, edge):
        self.outof_edges.append(edge)




class DependenceGraph:
    def __init__(self):
        """
            nodes: map line num (from renamed block) of node to operation node; contains type Node
            edges: map line num of node that the edge is coming OUT OF (parent) to the edge; contains type Edge
        """
        self.nodes = {} 
        # map line num of node that the edge is coming OUT OF (parent) to the edge; contains type Edge
        self.edges = {} 
        self.kinds = ["Data", "Serial", "Conflict"]
        self.opcodes_list = ["load", "store", "loadI", "add", "sub", "mult", "lshift", "rshift", "output", "nop"]
    
    def add_node(self, node):
        """
            Add node to nodes map that is keyed by node's line number
            node: node to add to the nodes map
        """
        self.nodes[node.line_num] = node
    

    def add_edge(self, edge):
        """
            Add edge to edges map that is keyed by the line number of the parent node
        """
        self.edges[edge.outof_line_num] = edge
    
    def get_ir_node(self, node):
        # print(start)
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
    
    def print_dg_map(self):
        print("digraph DG {")
        self.print_nodes()
        self.print_edges()
        print("}")

    def print_nodes(self):
        """
            format:   1 [label="1:  loadI  8 => r3"];
        """
        ret = ""
        for key, value in self.nodes:
            temp = "  " # indent
            temp += str(key)
            temp += ' [ label="'
            temp += str(value.line_num)
            temp += ":  "
            poo = self.get_ir_node(value.ir_list_node)
            temp += poo
            temp += ' "];'
            temp += '\n'
            ret += temp
        print(ret)
        

    
    def print_edges(self):
        """
            format of each node:   3 -> 1 [ label=" Data, vr3"];
              7 -> 6 [ label=" Conflict "];
            <line num of node edge is coming OUT OF (parent)> -> <line num of node edge is going INTO (child)> [ label = " <kind> "];
        """
        ret = ""
        for key, value in self.edges:
            temp = "  " # indent
            temp += str(key)   # line num of node edge is coming OUT OF (parent)
            temp += " -> "
            temp += str(value.into_line_num)
            temp += ' [ label=" '
            if (value.kind != DATA):
                temp += self.kinds[value.kind]
                temp += ' "];'
            elif (value.kind == DATA):
                temp += self.kinds[value.kind]
                temp += ', vr'
                temp += value.vr
                temp += ' "];'
            temp += '\n'
            ret += temp
        print(ret)

            
            

