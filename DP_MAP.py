
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
        self.parent = None  # type- Node; where the edge is coming OUT OF
        self.outof_line_num = None  # line num of parent node
        self.child = None   # type- Node; where the edge is going INTO (i.e. the side that has the arrow)
        self.into_line_num = None   # line num of child node


class Node:
    def __init__(self):
        self.line_num = None  # type- INT
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

            
            


