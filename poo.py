#!/usr/bin/python -u
import sys
import os
from collections import deque
import random

token_list = deque()
opcode_list = ['load', 'loadI', 'store', 'add', 'sub', 'mult', 'lshift', 'rshift', 'output', 'nop', 'newline', "reg", "const", "comma", "into", "endfile"]
# Opcode indexes
LOAD_IDX = 0
LOADI_IDX = 1
STORE_IDX = 2
ADD_IDX = 3
SUB_IDX = 4
MULT_IDX = 5
LSHIFT_IDX = 6
RSHIFT_IDX = 7
OUTPUT_IDX = 8
NOP_IDX = 9
NEWLINE_IDX = 10
REG_IDX = 11
CONST_IDX = 12
COMMA_IDX = 13
INTO_IDX = 14
ENDFILE_IDX = 15

# IR List Indexes
IR_LIST_OP_IDX = 0
OPCODE_IDX = 1
SR1_IDX = 2
VR1_IDX = 3
PR1_IDX = 4
NU1_IDX = 5
SR2_IDX = 6
VR2_IDX = 7
PR2_IDX = 8
NU2_IDX = 9
SR3_IDX = 10
VR3_IDX = 11
PR3_IDX = 12
NU3_IDX = 13

# Scanning/Parsing
line_count = 0
num_errors = 0
word = False

# Allocation
max_sr_num = 0 
max_vr_number = 0
max_pr_number = 0
num_registers_k = 0
max_live = 0
free_pr_stack = deque()
alloc_pr_to_nu = None
alloc_vr_to_pr = None
alloc_pr_to_vr = None
vr_to_spill_loc = None
reserved_register = None
curr_spill_location = 32764
rematerializable_vrs = None

# Scheduling
most_recent_load_idx = None
most_recent_store_idx = None
most_recent_output_idx = None
op_idx_to_latency = [5, 1, 5, 1, 1, 3, 1, 1, 1, 1]  
curr_edge_idx = 0
edges_list = []
nodes_list = []
vr_to_node_idx = {}
loads_list = []

# Node Status
NOT_YET_READY = 1
READY = 2
ACTIVE = 3
RETIRED = 4

# Node indexes
NODE_IDX = 0
NODE_OP_IDX = 1
NODE_FULL_OP_IDX = 2
NODE_PRED_IDX = 3
NODE_SUCC_IDX = 4
NODE_DELAY_IDX = 5
NODE_PRIORITY_IDX = 6
NODE_STATUS_IDX = 7

# Edge indexes
EDGE_IDX = 0
EDGE_FROM_IDX = 1
EDGE_TO_IDX = 2
EDGE_PRED_IDX = 3
EDGE_SUCC_IDX = 4
EDGE_LATENCY_IDX = 5
EDGE_TYPE_IDX = 6



'''
*******************************************************************************
*********************** DOUBLY LINKED LIST: ***********************************
*******************************************************************************
'''
class IR:
    def __init__(self, ir):
        self.prev = None
        self.ir = ir
        self.next = None

class IRDoublyLinkedList:
    def __init__(self):
        self.len = 0

    def append(self, ir):
        new_node = IR(ir)
        if self.len == 0:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
        self.len += 1

    def insert(self, position, ir):

        if position < 0 or position > self.len:
            raise ValueError("Invalid position")

        new_node = IR(ir)

        if position == 0:
            # If inserting at the beginning
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
        elif position == self.len:
            # If inserting at the end
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node
        else:
            # Inserting in the middle
            current_node = self.head
            for i in range(position - 1):
                current_node = current_node.next

            new_node.prev = current_node
            new_node.next = current_node.next
            current_node.next.prev = new_node
            current_node.next = new_node

        self.len += 1

    def print_ir_list(self):
        print()
        print("INTERMEDIATE REPRESENTATION LABELS:")
        print(["Line", "Opcode", "SR", "VR", "PR", "NU", "SR", "VR", "PR", "NU", "SR", "VR", "PR", "NU"])
        print()

        print("INTERMEDIATE REPRESENTATIONS:")
        readble_ir_list = []
        current = self.head
        while current is not None:
            readable_ir = current.ir.copy()
            readable_ir[1] = opcode_list[readable_ir[1]]
            print(readable_ir)
            current = current.next

    def print_renamed_output(self):
        current = self.head
        while current is not None:
            if current.ir[1] == 1: #loadI
                print("loadI " + str(current.ir[2]) + " => r" + str(current.ir[11]))
            elif current.ir[1] == 0 or current.ir[1] == 2: #Load or Store
                print(opcode_list[current.ir[1]] + " r" + str(current.ir[3]) + " => r" + str(current.ir[11]))
            elif current.ir[1] == 8: #output
                print("output " + str(current.ir[2]))
            elif current.ir[1] == 9: #nop
                print("nop")
            else: # Add, sub, mult, lshift, rshift
                print(opcode_list[current.ir[1]] + " r" + str(current.ir[3]) + ", r" + str(current.ir[7]) + " => r" + str(current.ir[11]))
            current = current.next

    def print_allocated_output(self):
        current = self.head
        while current is not None:
            if current.ir[1] == 1: #loadI
                print("loadI " + str(current.ir[2]) + " => r" + str(current.ir[12]))
            elif current.ir[1] == 0 or current.ir[1] == 2: #Load or Store
                print(opcode_list[current.ir[1]] + " r" + str(current.ir[4]) + " => r" + str(current.ir[12]))
            elif current.ir[1] == 8: #output
                print("output " + str(current.ir[2]))
            elif current.ir[1] == 9: #nop
                print("nop")
            else: # Add, sub, mult, lshift, rshift
                print(opcode_list[current.ir[1]] + " r" + str(current.ir[4]) + ", r" + str(current.ir[8]) + " => r" + str(current.ir[12]))
            current = current.next

    def traverse_backward(self):
        current = self.tail
        while current is not None:
            yield current.ir
            current = current.prev

    def traverse_forward(self):
        current = self.head
        while current is not None:
            yield current.ir
            current = current.next

ir_list = IRDoublyLinkedList()
prev_ir = ir_list.traverse_backward()
next_ir = ir_list.traverse_forward()

'''
****************************************************************************
************************** HELPER FUNCTIONS: *******************************
****************************************************************************
'''
def add_edge(from_node, to_node, op_latency, edge_type):
    global curr_edge_idx

    edge = [curr_edge_idx, from_node[NODE_IDX], to_node[NODE_IDX], '-', '-', op_latency, edge_type]
    edges_list.append(edge)
    curr_edge_idx += 1

    if from_node[NODE_SUCC_IDX] == '-':
        from_node[NODE_SUCC_IDX] = edge[EDGE_IDX]
    else:
        curr_from_edge_idx = from_node[NODE_SUCC_IDX]
        while edges_list[curr_from_edge_idx][EDGE_SUCC_IDX] != '-':
            curr_from_edge_idx = edges_list[curr_from_edge_idx][EDGE_SUCC_IDX]
        edges_list[curr_from_edge_idx][EDGE_SUCC_IDX] = edge[EDGE_IDX]
    
    if to_node[NODE_PRED_IDX] == '-':
        to_node[NODE_PRED_IDX] = edge[EDGE_IDX]
    else:
        curr_to_edge_idx = to_node[NODE_PRED_IDX]
        while edges_list[curr_to_edge_idx][EDGE_PRED_IDX] != '-':
            curr_to_edge_idx = edges_list[curr_to_edge_idx][EDGE_SUCC_IDX]
        edges_list[curr_to_edge_idx][EDGE_SUCC_IDX] = edge[EDGE_IDX]

def remove_duplicate_edges(edges_list):
    unique_edges = {}

    for edge in edges_list:
        from_node, to_node, latency = edge[1], edge[2], edge[5]
        key = (from_node, to_node)

        if key not in unique_edges or latency > unique_edges[key][5]:
            unique_edges[key] = edge

    unique_edges_list = list(unique_edges.values())
    return unique_edges_list

def convert_to_adjacency_list(edges_list):
    edge_pairs = []
    all_nodes = set()

    unique_edges_list = remove_duplicate_edges(edges_list)
    for edge in unique_edges_list:
        from_node, to_node, latency = edge[EDGE_FROM_IDX], edge[EDGE_TO_IDX], edge[EDGE_LATENCY_IDX]
        edge_pair = (from_node, to_node, latency)
        edge_pairs.append(edge_pair)
        all_nodes.add(from_node)
        all_nodes.add(to_node)

    parent_to_child_map = {}
    child_to_parent_map = {}
    potential_roots = all_nodes.copy()
    
    for edge in edge_pairs:
        from_node, to_node, latency = edge
        # Remove to_node from potential roots if it appears as a to_node in an edge
        if to_node in potential_roots:
            potential_roots.remove(to_node)

        # Add from_node to parent_to_child_map if not present
        if from_node not in parent_to_child_map:
            parent_to_child_map[from_node] = []
        if to_node not in child_to_parent_map:
            child_to_parent_map[to_node] = []
        # Add the edge as a tuple (neighbor, latency) to the parent_to_child_map
        parent_to_child_map[from_node].append((to_node, latency))
        child_to_parent_map[to_node].append((from_node, latency))

    # The remaining potential_roots are nodes that are not to_node in any edge
    root_nodes = list(potential_roots)

    return parent_to_child_map, child_to_parent_map, root_nodes

def set_priorities(parent_to_child_map, start, nodes_list):
    stack = [(start, 0)]  # Initialize the stack with the start node and its priority

    while stack:
        current, parent_priority = stack.pop()

        # Update priority for the current node only if it's higher than the current priority
        current_priority = max(parent_priority, nodes_list[current][NODE_PRIORITY_IDX])
        nodes_list[current][NODE_PRIORITY_IDX] = current_priority

        # Push neighbors onto the stack in reverse order to match the order of recursive function
        for neighbor, edge_latency in reversed(parent_to_child_map.get(current, [])):
            stack.append((neighbor, current_priority + edge_latency))

def generate_dot_script(nodes_list, edges_list):
    dot_script = "digraph G {\n"

    # Add nodes
    for node in nodes_list:
        idx, NODE_OP_IDX, node_full_op, pred, succ, delay, priority, status = node
        label = f"{idx}: {node_full_op}\\nDelay: {delay}\\nPriority: {priority}"
        dot_script += f'  {idx} [label="{label}"];\n'

    # Add edges
    for edge in edges_list:
        idx, source, sink, pred, succ, latency, edge_type = edge
        dot_script += f'  {source} -> {sink} [label="{latency}, {edge_type}"];\n'

    dot_script += "}\n"
    return dot_script

def remove_from_graph(parent_to_child_map, node):
    for _, neighbors in parent_to_child_map.items():
        for node_tuple in neighbors:
            if node == node_tuple[0]:
                # print("REMOVING", node_tuple)
                neighbors.remove(node_tuple)

def print_schedule(schedule):
    for cycle, op0, op1 in schedule:
        print("[" + op0[NODE_FULL_OP_IDX] + "; " + op1[NODE_FULL_OP_IDX] + "]")

def is_valid_first_op(opcode_idx):
    if opcode_idx in [LOAD_IDX, STORE_IDX, ADD_IDX, SUB_IDX, MULT_IDX, LSHIFT_IDX, RSHIFT_IDX]:
        return True
    else:
        return False

def is_valid_second_op(opcode_idx):
    if opcode_idx in [STORE_IDX, ADD_IDX, SUB_IDX, MULT_IDX, LSHIFT_IDX, RSHIFT_IDX]:
        return True
    else:
        return False

def is_valid_third_op(opcode_idx):
    if opcode_idx in [LOAD_IDX, LOADI_IDX, ADD_IDX, SUB_IDX, MULT_IDX, LSHIFT_IDX, RSHIFT_IDX]:
        return True
    else:
        return False

def get_pr(vr, nu, is_first_op, curr_ir):
    global alloc_vr_to_pr
    global alloc_pr_to_vr
    global alloc_pr_to_nu
    global free_pr_stack

    if free_pr_stack:
        pr = free_pr_stack.popleft()
    else: # Spill
        if not is_first_op:
            temp_pr_to_nu = alloc_pr_to_nu[:]
            # print(curr_ir)
            # print(curr_ir[PR1_IDX])
            curr_pr1 = curr_ir[PR1_IDX]
            if(curr_pr1 == '-'):
                pr1 = -1
            else:
                pr1 = curr_pr1
            temp_pr_to_nu[pr1] = -1
            pr = temp_pr_to_nu.index(max(temp_pr_to_nu)) 
        else:
            pr = alloc_pr_to_nu.index(max(alloc_pr_to_nu))

        spill(pr)
        alloc_vr_to_pr[alloc_pr_to_vr[pr]] = "-"

    alloc_vr_to_pr[vr] = pr
    alloc_pr_to_vr[pr] = vr
    alloc_pr_to_nu[pr] = nu
    return pr

def free_pr(pr):
    global alloc_vr_to_pr
    global alloc_pr_to_vr
    global alloc_pr_to_nu
    global free_pr_stack
    
    alloc_vr_to_pr[alloc_pr_to_vr[pr]] = '-'
    alloc_pr_to_vr[pr] = '-'
    alloc_pr_to_nu[pr] = float('inf')
    free_pr_stack.appendleft(pr)

def spill(pr):
    global reserved_register
    global curr_spill_location

    spill_vr = alloc_pr_to_vr[pr]

    if rematerializable_vrs[spill_vr] == '-':
        curr_spill_location = curr_spill_location + 4
        vr_to_spill_loc[spill_vr] = curr_spill_location

        print("loadI " + str(curr_spill_location) + " => r" + str(reserved_register))
        print("store r" + str(pr) + " => r" + str(reserved_register))

def restore(vr, pr):
    global reserved_register
    global rematerializable_vrs

    if rematerializable_vrs[vr] != '-': # Rematerialize loadI
        print("loadI " + str(rematerializable_vrs[vr]) + " => r" + str(pr))

    else: # Regular Restore
        retrieved_spill_location = vr_to_spill_loc[vr]

        print("loadI " + str(retrieved_spill_location) + " => r" + str(reserved_register))
        print("load r" + str(reserved_register) + " => r" + str(pr))

def get_next_token():
    return token_list.popleft()

def finish_memop(line_num, opcode_idx):
    global num_errors
    global word
    global max_sr_num
    word = get_next_token()
    if(word[1] != 11):
        # handle_print_statements("ERROR " + str(line_num) + ": Missing source register in load or store.", "p")
        num_errors = num_errors + 1
        return False
    else:
        reg1 = word[2]
        word = get_next_token()
        if(word[1] != 14):
            # handle_print_statements("ERROR " + str(line_num) + ": Missing '=>' in load or store.", "p")
            num_errors = num_errors + 1
            return False
        else:
            word = get_next_token()
            if(word[1] != 11):
                # handle_print_statements("ERROR " + str(line_num) + ": Missing target register in load or store.", "p")
                num_errors = num_errors + 1
                return False
            else:
                reg2 = word[2]
                word = get_next_token()
                if(word[1] == 10 or word[1] == 15):
                    #Build IR for this Op and add to list of Ops
                    ir = ['-'] * 14 # 14 main slots
                    ir[0] = ir_list.len # Line number
                    ir[1] = opcode_idx # int for load or store
                    ir[2] = reg1
                    ir[10] = reg2
                    ir[5] = float('inf')
                    ir[9] = float('inf')
                    ir[-1] = float('inf')
                    ir_list.append(ir)
                    max_sr_num = max(reg1, reg2, max_sr_num)
                    return
                else:
                    # handle_print_statements("ERROR " + str(line_num) + ": Unexpected token; Expected NEWLINE in load or store.", "p")
                    num_errors = num_errors + 1
                    return False

def finish_loadi(line_num):
    global num_errors
    global word
    global max_sr_num
    word = get_next_token()
    if(word[1] != 12):
        # handle_print_statements("ERROR " + str(line_num) + ": Missing constant in loadi.", "p")
        num_errors = num_errors + 1
        return False
    else:
        const = word[2]
        word = get_next_token()
        if(word[1] != 14):
            # handle_print_statements("ERROR " + str(line_num) + ": Missing '=>' in loadi.", "p")
            num_errors = num_errors + 1
            return False
        else:
            word = get_next_token()
            if(word[1] != 11):
                # handle_print_statements("ERROR " + str(line_num) + ": Missing target register in loadi.", "p")
                num_errors = num_errors + 1
                return False
            else:
                reg2 = word[2]
                word = get_next_token()
                if(word[1] == 10 or word[1] == 15):
                    # #Build IR for this Op and add to list of Ops
                    ir = ['-'] * 14 # 14 main slots
                    ir[0] = ir_list.len # Line number
                    ir[1] = 1 # loadi index
                    ir[2] = const
                    ir[10] = reg2
                    ir[5] = float('inf')
                    ir[9] = float('inf')
                    ir[-1] = float('inf')
                    ir_list.append(ir)
                    max_sr_num = max(reg2, max_sr_num)
                    return
                else:
                    # handle_print_statements("ERROR " + str(line_num) + ": Unexpected token; Expected NEWLINE in loadi.", "p")
                    num_errors = num_errors + 1
                    return False

def finish_arithop(line_num, opcode_idx):
    global num_errors
    global word
    global max_sr_num
    word = get_next_token()
    if(word[1] != 11):
        # handle_print_statements("ERROR " + str(line_num) + ": Missing first source register in arithop.", "p")
        num_errors = num_errors + 1
        return False
    else:
        reg1 = word[2]
        word = get_next_token()
        if(word[1] != 13):
            # handle_print_statements("ERROR " + str(line_num) + ": Missing comma in arithop.", "p")
            num_errors = num_errors + 1
            return False
        else:
            word = get_next_token()
            if(word[1] != 11):
                # handle_print_statements("ERROR " + str(line_num) + ": Missing second source register in arithop.", "p")
                num_errors = num_errors + 1
                return False
            else:
                reg2 = word[2]
                word = get_next_token()
                if(word[1] != 14):
                    # handle_print_statements("ERROR " + str(line_num) + ": Missing '=>' in arithop.", "p")
                    num_errors = num_errors + 1
                    return False
                else:
                    word = get_next_token()
                    if(word[1] != 11):
                        # handle_print_statements("ERROR " + str(line_num) + ": Missing target register in arithop.", "p")
                        num_errors = num_errors + 1
                        return False
                    else:
                        reg3 = word[2]
                        word = get_next_token()
                        if(word[1] == 10 or word[1] == 15):
                            #Build IR for this Op and add to list of Ops
                            ir = ['-'] * 14 # 14 main slots
                            ir[0] = ir_list.len # Line number
                            ir[1] = opcode_idx # int for add sub mult lshift or rshift
                            ir[2] = reg1
                            ir[6] = reg2
                            ir[10] = reg3
                            ir[5] = float('inf')
                            ir[9] = float('inf')
                            ir[-1] = float('inf')
                            ir_list.append(ir)
                            max_sr_num = max(reg1, reg2, reg3, max_sr_num)
                            return
                        else:
                            # handle_print_statements("ERROR " + str(line_num) + ": Unexpected token; Expected NEWLINE in arithop.", "p")
                            num_errors = num_errors + 1
                            return False

def finish_output(line_num):
    global num_errors
    global word
    word = get_next_token()
    if(word[1] != 12):
        # handle_print_statements("ERROR " + str(line_num) + ": Missing constant in output.", "p")
        num_errors = num_errors + 1
        return False
    else:
        const = word[2]
        word = get_next_token()
        if(word[1] == 10 or word[1] == 15):
            #Build IR for this Op and add to list of Ops
            ir = ['-'] * 14 # 14 main slots
            ir[0] = ir_list.len # Line number;
            ir[1] = 8 # output index
            ir[2] = const
            ir[5] = float('inf')
            ir[9] = float('inf')
            ir[-1] = float('inf')
            ir_list.append(ir)
            return
        else:
            print(word)
            # handle_print_statements("ERROR " + str(line_num) + ": Unexpected token; Expected NEWLINE in output.", "p")
            num_errors = num_errors + 1
            return False

def finish_nop(line_num):
    global num_errors
    global word
    word = get_next_token()
    if(word[1] == 10 or word[1] == 15):
        #Build IR for this Op and add to list of Ops
        ir = ['-'] * 14 # 14 main slots
        ir[0] = ir_list.len # Line number
        ir[1] = 9 # nop index
        ir[5] = float('inf')
        ir[9] = float('inf')
        ir[-1] = float('inf')
        ir_list.append(ir)
        return
    else:
        # handle_print_statements("ERROR " + str(line_num) + ": Unexpected token; Expected NEWLINE in nop.", "p")
        num_errors = num_errors + 1
        return False


'''
******************************************************************
********************** FLAG HANDLING: ****************************
******************************************************************
'''
def handle_scheduling(filename):
    scan(filename)
    parse()
    if(num_errors == 0):
        rename()
        # ir_list.print_ir_list() 
        # print()
        # ir_list.print_renamed_output()
        # print()
    else:
        print("ERROR: Terminating due to ILOC syntax errors discovered by the scanner/parser")
        sys.exit(1)

    build_graph()
    parent_to_child_map, child_to_parent_map, root_nodes = convert_to_adjacency_list(edges_list)
    # print(parent_to_child_map)
    # print(child_to_parent_map)
    for root_node in root_nodes:
        set_priorities(parent_to_child_map, root_node, nodes_list)
    # print()
    # print("VR To Node Map: ", vr_to_node_idx)
    # print()
    # print("Node format [IDX, op IDX, Full OP, PRED, SUCC, Delay, Priority, Status]")
    # print("Nodes List: ", nodes_list)
    # print()
    # print("Edge format [idx, from, to, pred, succ, latency, type]")
    # print("Edges List: ", edges_list)
    # dot_script = generate_dot_script(nodes_list, edges_list)
    # print()
    # print(dot_script)
    # print("Schedule: ")
    schedule = make_schedule(parent_to_child_map, child_to_parent_map)
    # print(schedule)
    # print()
    print_schedule(schedule)

def handle_allocation(filename):
    global max_live
    global num_registers_k
    global max_pr_number
    global reserved_register

    scan(filename)
    parse()
    if(num_errors == 0):
        rename()
        # ir_list.print_ir_list() 
        # print()
        # ir_list.print_renamed_output()
    else:
        print("ERROR: Terminating due to ILOC syntax errors discovered by the scanner/parser")
        sys.exit(1)

    # print("Max Live: ", max_live)
    if (max_live > num_registers_k): # Check if it will have spills; if so reserve a register
        reserved_register = num_registers_k - 1 # Set the last register to be reserved
        max_pr_number = max_pr_number - 1 # Decrement the number of available registers

    allocate()
    # ir_list.print_ir_list()
    # print()
    # ir_list.print_allocated_output()

def handle_h_flag():
    print("COMP 412, Fall 2023, Allocator")
    print("Command Syntax:")
    print("    412alloc [-h] filename\n")
    print("Required arguments:")
    print("    filename  is the pathname (absolute or relative) to the input file\n")
    print("Optional flags:")
    print("    -h        prints this message")

def handle_x_flag(filename):
    scan(filename)
    parse()
    if(num_errors == 0):
        rename()
        # ir_list.print_ir_list() 
        # print()
        ir_list.print_renamed_output()
    else:
        print("ERROR: Terminating due to syntax errors")
        sys.exit(1)

def handle_flags(filename):
    if ('-x' in sys.argv):
        handle_x_flag(filename)
    elif('-h' in sys.argv):
        handle_h_flag()



'''
*******************************************************************
********************** MAIN FUNCTIONS: ****************************
*******************************************************************
'''
def scan(filename):
    try:
        with open(filename, 'r') as file:
            while True:
                line_buffer = file.readline()
                global line_count
                line_count += 1
                i = 0
                if not line_buffer:  # Check for EOF case
                    token_list.append((line_count, 15, ""))
                    # # handle_print_statements(str(line_count) + ': < ENDFILE, "" >', "s")
                    break
                last_buffer_idx = len(line_buffer)   
                while i < last_buffer_idx:
                    if line_buffer[i] == " " or line_buffer[i] == "\t": # Skip space characters, move to the next character
                        i += 1
                    elif line_buffer[i] == "a" and (i+2) < last_buffer_idx:
                        i += 1
                        if line_buffer[i] == "d":
                            i += 1
                            if line_buffer[i] == "d":
                                i += 1
                                token_list.append((line_count, 3, "add"))
                                # # handle_print_statements(str(line_count) + ': < ARITHOP, "add" >', "s")
                            else:
                                # handle_print_statements("ERROR " + str(line_count) + ": Found 'ad', but not followed by 'd'", "s")
                                token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'ad', but not followed by 'd'"))
                                break
                        else:
                            # handle_print_statements("ERROR " + str(line_count) + ": Found 'a', but not followed by 'd'", "s")
                            token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'a', but not followed by 'd'"))
                            break
                    elif line_buffer[i] == "=" and (i+1) < last_buffer_idx:
                        i += 1
                        if line_buffer[i] == ">":
                            i += 1
                            token_list.append((line_count, 14, "into"))
                            # # handle_print_statements(str(line_count) + ': < INTO, "=>" >', "s")
                        else:
                            # handle_print_statements("ERROR " + str(line_count) + ": Found '=', but not followed by '>'", "s")
                            token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found '=', but not followed by '>'"))
                            break
                    elif line_buffer[i] == ",":
                        i += 1
                        token_list.append((line_count, 13, ","))
                        # # handle_print_statements(str(line_count) + ': < COMMA, "," >', "s")
                    elif line_buffer[i] == "r":
                        i += 1
                        # If the next character is a digit, it's a register
                        if line_buffer[i].isdigit():
                            register_number = ""
                            # Continue reading characters as long as they are integers
                            while i < last_buffer_idx and line_buffer[i].isdigit():
                                register_number += line_buffer[i]
                                i += 1
                            # Check if at least one digit was found
                            if register_number:
                                token_list.append((line_count, 11, int(register_number)))
                                # # handle_print_statements(str(line_count) + ': < REG, "' + register + '" >', "s")
                            else:
                                # handle_print_statements("ERROR " + str(line_count) + ": Found 'r', but no digits followed", "s")
                                token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'r', but no digits followed"))
                                break
                        elif line_buffer[i] == "s" and (i+4) < last_buffer_idx:
                            i += 1
                            if line_buffer[i] == "h":
                                i += 1
                                if line_buffer[i] == "i":
                                    i += 1
                                    if line_buffer[i] == "f":
                                        i += 1
                                        if line_buffer[i] == "t":
                                            i += 1
                                            token_list.append((line_count, 7, "rshift"))
                                            # # handle_print_statements(str(line_count) + ': < ARITHOP, "rshift" >', "s")
                                        else:
                                            # handle_print_statements("ERROR " + str(line_count) + ": Found 'rshif', but not followed by 't'", "s")
                                            token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'rshif', but not followed by 't'"))
                                            break
                                    else:
                                        # handle_print_statements("ERROR " + str(line_count) + ": Found 'rshi', but not followed by 'f'", "s")
                                        token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'rshi', but not followed by 'f'"))
                                        break
                                else:
                                    # handle_print_statements("ERROR " + str(line_count) + ": Found 'rsh', but not followed by 'i'", "s")
                                    token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'rsh', but not followed by 'i'"))
                                    break
                            else:
                                # handle_print_statements("ERROR " + str(line_count) + ": Found 'rs', but not followed by 'h'", "s")
                                token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'rs', but not followed by 'h'"))
                                break
                        else:
                            # handle_print_statements("ERROR " + str(line_count) + ": Found 'r', but not followed by 's' or a digit", "s")
                            token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'r', but not followed by 's' or a digit"))
                            break
                    elif line_buffer[i] == "/" and (i+1) < last_buffer_idx:
                        i += 1
                        if line_buffer[i] == "/":
                            # Found a comment, so break out of the inner loop to skip the rest of the line; But keep newline
                            token_list.append((line_count, 10, "\\n"))
                            # # handle_print_statements(str(line_count) + ': < NEWLINE, "\\n" >', "s")
                            break
                        else:
                            # handle_print_statements("ERROR " + str(line_count) + ": Found '/', but not followed by '/'", "s")
                            token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found '/', but not followed by '/'"))
                            break
                    elif line_buffer[i] == "s":
                        i += 1
                        if line_buffer[i] == "t" and (i+3) < last_buffer_idx:
                            i += 1
                            if line_buffer[i] == "o":
                                i += 1
                                if line_buffer[i] == "r":
                                    i += 1
                                    if line_buffer[i] == "e":
                                        i += 1
                                        token_list.append((line_count, 2, "store"))
                                        # # handle_print_statements(str(line_count) + ': < MEMOP, "store" >', "s")
                                    else:
                                        # handle_print_statements("ERROR " + str(line_count) + ": Found 'stor', but not followed by 'e'", "s")
                                        token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'stor', but not followed by 'e'"))
                                        break
                                else:
                                    # handle_print_statements("ERROR " + str(line_count) + ": Found 'sto', but not followed by 'r'", "s")
                                    token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'sto', but not followed by 'r'"))
                                    break
                            else:
                                # handle_print_statements("ERROR " + str(line_count) + ": Found 'st', but not followed by 'o'", "s")
                                token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'st', but not followed by 'o'"))
                                break
                        elif line_buffer[i] == "u" and (i+1) < last_buffer_idx:
                            i += 1
                            if line_buffer[i] == "b":
                                i += 1
                                token_list.append((line_count, 4, "sub"))
                                # # handle_print_statements(str(line_count) + ': < ARITHOP, "sub" >', "s")
                            else:
                                # handle_print_statements("ERROR " + str(line_count) + ": Found 'su', but not followed by 'b'", "s")
                                token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'su', but not followed by 'b'"))
                                break
                        else:
                            # handle_print_statements("ERROR " + str(line_count) + ": Found 's', but not followed by 't' or 'u'", "s")
                            token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 's', but not followed by 't' or 'u'"))
                            break
                    elif line_buffer[i].isdigit():
                        const = ""
                        # Continue reading characters as long as they are integers
                        while i < last_buffer_idx and line_buffer[i].isdigit():
                            # print("Adding :", line_buffer[i])
                            const += line_buffer[i]
                            i += 1
                        # Check if at least one digit was found
                        if const:
                            token_list.append((line_count, 12, int(const)))
                            # # handle_print_statements(str(line_count) + ': < CONST, "' + const + '" >', "s")
                    elif line_buffer[i] == "\n":
                        i += 1
                        token_list.append((line_count, 10, "\\n"))
                        # # handle_print_statements(str(line_count) + ': < NEWLINE, "\\n" >', "s")
                    elif line_buffer[i] == "m" and (i+3) < last_buffer_idx:
                        i += 1
                        if line_buffer[i] == "u":
                            i += 1
                            if line_buffer[i] == "l":
                                i += 1
                                if line_buffer[i] == "t":
                                    i += 1
                                    token_list.append((line_count, 5, "mult"))
                                    # # handle_print_statements(str(line_count) + ': < ARITHOP, "mult" >', "s")
                                else:
                                    # handle_print_statements("ERROR " + str(line_count) + ": Found 'mul', but not followed by 't'", "s")
                                    token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'mul', but not followed by 't'"))
                                    break
                            else:
                                # handle_print_statements("ERROR " + str(line_count) + ": Found 'mu', but not followed by 'l'", "s")
                                token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'mu', but not followed by 'l'"))
                                break
                        else:
                            # handle_print_statements("ERROR " + str(line_count) + ": Found 'm', but not followed by 'u'", "s")
                            token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'm', but not followed by 'u'"))
                            break
                    elif line_buffer[i] == "l" and (i+4) < last_buffer_idx:
                        i += 1
                        if line_buffer[i] == "o":
                            i += 1
                            if line_buffer[i] == "a":
                                i += 1
                                if line_buffer[i] == "d":
                                    i += 1
                                    if line_buffer[i] == "I":
                                        i += 1
                                        token_list.append((line_count, 1, "loadI"))
                                        # # handle_print_statements(str(line_count) + ': < LOADI, "loadI" >', "s")
                                    else:
                                        token_list.append((line_count, 0, "load"))
                                        # # handle_print_statements(str(line_count) + ': < MEMOP, "load" >', "s")
                                else:
                                    # handle_print_statements("ERROR " + str(line_count) + ": Found 'loa', but not followed by 'd'", "s")
                                    token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'loa', but not followed by 'd'"))
                                    break
                            else:
                                # handle_print_statements("ERROR " + str(line_count) + ": Found 'lo', but not followed by 'a'", "s")
                                token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'lo', but not followed by 'a'"))
                                break
                        elif line_buffer[i] == "s" and (i+4) < last_buffer_idx:
                            i += 1
                            if line_buffer[i] == "h":
                                i += 1
                                if line_buffer[i] == "i":
                                    i += 1
                                    if line_buffer[i] == "f":
                                        i += 1
                                        if line_buffer[i] == "t":
                                            i += 1
                                            token_list.append((line_count, 6, "lshift"))
                                            # # handle_print_statements(str(line_count) + ': < ARITHOP, "lshift" >', "s")
                                        else:
                                            # handle_print_statements("ERROR " + str(line_count) + ": Found 'lshif', but not followed by 't'", "s")
                                            token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'lshif', but not followed by 't'"))
                                            break
                                    else:
                                        # handle_print_statements("ERROR " + str(line_count) + ": Found 'lshi', but not followed by 'f'", "s")
                                        token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'lshi', but not followed by 'f'"))
                                        break
                                else:
                                    # handle_print_statements("ERROR " + str(line_count) + ": Found 'lsh', but not followed by 'i'", "s")
                                    token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'lsh', but not followed by 'i'"))
                                    break
                            else:
                                # handle_print_statements("ERROR " + str(line_count) + ": Found 'ls', but not followed by 'h'", "s")
                                token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'ls', but not followed by 'h'"))
                                break
                        else:
                            # handle_print_statements("ERROR " + str(line_count) + ": Found 'l', but not followed by 'o' or 's' or is incomplete", "s")
                            token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'l', but not followed by 'o' or 's' or is incomplete"))
                            break
                    elif line_buffer[i] == "o" and (i+5) < last_buffer_idx:
                        i += 1
                        if line_buffer[i] == "u":
                            i += 1
                            if line_buffer[i] == "t":
                                i += 1
                                if line_buffer[i] == "p":
                                    i += 1
                                    if line_buffer[i] == "u":
                                        i += 1
                                        if line_buffer[i] == "t":
                                            i += 1
                                            token_list.append((line_count, 8, "output"))
                                            # # handle_print_statements(str(line_count) + ': < OUTPUT, "output" >', "s")
                                        else:
                                            # handle_print_statements("ERROR " + str(line_count) + ": Found 'outpu', but not followed by 't'", "s")
                                            token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'outpu', but not followed by 't'"))
                                            break
                                    else:
                                        # handle_print_statements("ERROR " + str(line_count) + ": Found 'outp', but not followed by 'u'", "s")
                                        token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'outp', but not followed by 'u'"))
                                        break
                                else:
                                    # handle_print_statements("ERROR " + str(line_count) + ": Found 'out', but not followed by 'p'", "s")
                                    token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'out', but not followed by 'p'"))
                                    break
                            else:
                                # handle_print_statements("ERROR " + str(line_count) + ": Found 'ou', but not followed by 't'", "s")
                                token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'ou', but not followed by 't'"))
                                break
                        else:
                            # handle_print_statements("ERROR " + str(line_count) + ": Found 'o', but not followed by 'u'", "s")
                            token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'o', but not followed by 'u'"))
                            break
                    elif line_buffer[i] == "n" and (i+2) < last_buffer_idx:
                        i += 1
                        if line_buffer[i] == "o":
                            i += 1
                            if line_buffer[i] == "p":
                                i += 1
                                token_list.append((line_count, 9, "nop"))
                                # # handle_print_statements(str(line_count) + ': < NOP, "nop" >', "s")
                            else:
                                # handle_print_statements("ERROR " + str(line_count) + ": Found 'no', but not followed by 'p'", "s")
                                token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'no', but not followed by 'p'"))
                                break
                        else:
                            # handle_print_statements("ERROR " + str(line_count) + ": Found 'n', but not followed by 'o'", "s")
                            token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Found 'n', but not followed by 'o'"))
                            break
                    else:
                        i += 1
                        # handle_print_statements("ERROR " + str(line_count) + ": Unexpected token " + line_buffer[i - 1], "s")
                        token_list.append((line_count, -1, "ERROR " + str(line_count) + ": Unexpected token " + line_buffer[i - 1]))
                        break
    except UnicodeDecodeError as e:
        print(f"ERROR decoding the file: {e}")
        sys.exit(1)

def parse():
    global word
    word = get_next_token()

    while word[1] != 15:  # Loop until EOF is encountered
        error_occurred = False
        curr_line_num = word[0]
        while word[1] != 10:  # Continue until a newline is encountered
            if word[1] == -1: # Check for error tokens
                # handle_print_statements(word[2], "p")
                global num_errors
                num_errors = num_errors + 1
                word = get_next_token()
                break
            elif word[1] == 0 or word[1] == 2:
                if not finish_memop(word[0], word[1]):
                    error_occurred = True
                    break
            elif word[1] == 1:
                if not finish_loadi(word[0]):
                    error_occurred = True
                    break
            elif 3 <= word[1] <= 7:
                if not finish_arithop(word[0], word[1]):
                    error_occurred = True
                    break
            elif word[1] == 8:
                if not finish_output(word[0]):
                    error_occurred = True
                    break
            elif word[1] == 9:
                if not finish_nop(word[0]):
                    error_occurred = True
                    break
            else:
                # handle_print_statements("ERROR " + str(word[0]) + ": Unexpected Token, " + word[2], "p")
                num_errors = num_errors + 1
                error_occurred = True
                break
            word = get_next_token()

        if error_occurred: # Skip processing the rest of the tokens on this line
            while word[0] <= curr_line_num:
                word = get_next_token()

        if word[1] == 10:  # Check for newline
            word = get_next_token()

def rename():
    global max_sr_num
    global max_vr_number
    global max_live

    sr_to_vr = ['-'] * (max_sr_num + 1)
    lu = [float('inf')] * (max_sr_num + 1)

    VRNum = 0
    ir_list_idx = ir_list.len - 1
    curr_ir = ir_list.tail.ir

    try:
        while True:
            curr_opcode_idx = curr_ir[OPCODE_IDX]
            valid_first_op = False
            valid_second_op = False

            if curr_ir[OPCODE_IDX] == STORE_IDX:
                if is_valid_first_op(curr_opcode_idx):
                    valid_first_op = True
                    curr_sr_num = curr_ir[SR1_IDX]
                    if sr_to_vr[curr_sr_num] == '-':
                        sr_to_vr[curr_sr_num] = VRNum
                        # print("sr 1; added " + str(VRNum) + " to idx " + str(curr_ir[curr_opcode_idx]))
                        VRNum+=1
                    curr_ir[VR1_IDX] = sr_to_vr[curr_sr_num]
                    max_vr_number = max(sr_to_vr[curr_sr_num], max_vr_number)
                    curr_ir[NU1_IDX] = lu[curr_sr_num]

                if is_valid_second_op(curr_opcode_idx):
                    valid_second_op = True
                    curr_sr_num = curr_ir[SR3_IDX]
                    if sr_to_vr[curr_sr_num] == '-':
                        sr_to_vr[curr_sr_num] = VRNum
                        # print("sr 2; added " + str(VRNum) + " to idx " + str(curr_ir[curr_opcode_idx]))
                        VRNum+=1
                    curr_ir[VR3_IDX] = sr_to_vr[curr_sr_num]
                    max_vr_number = max(sr_to_vr[curr_sr_num], max_vr_number)
                    curr_ir[NU3_IDX] = lu[curr_sr_num]

                if valid_first_op:
                    curr_sr_num = curr_ir[SR1_IDX]
                    # print("lu; added " + str(ir_list_idx) + " to idx " + str(curr_ir[sr_idx]))
                    lu[curr_sr_num] = ir_list_idx

                if valid_second_op:
                    curr_sr_num = curr_ir[SR3_IDX]
                    # print("lu; added " + str(ir_list_idx) + " to idx " + str(curr_ir[sr_idx]))
                    lu[curr_sr_num] = ir_list_idx
            else: # Not a store
                # Defs
                if is_valid_third_op(curr_opcode_idx):
                    curr_sr_num = curr_ir[SR3_IDX]
                    if sr_to_vr[curr_sr_num] == '-':
                        sr_to_vr[curr_sr_num] = VRNum
                        # print("sr 1; added " + str(VRNum) + " to idx " + str(curr_ir[curr_opcode_idx]))
                        VRNum+=1
                    curr_ir[VR3_IDX] = sr_to_vr[curr_sr_num]
                    max_vr_number = max(sr_to_vr[curr_sr_num], max_vr_number)
                    curr_ir[NU3_IDX] = lu[curr_sr_num]
                    sr_to_vr[curr_sr_num] = '-'
                    lu[curr_sr_num] = float('inf')
                # Uses
                if is_valid_first_op(curr_opcode_idx):
                    valid_first_op = True
                    curr_sr_num = curr_ir[SR1_IDX]
                    if sr_to_vr[curr_sr_num] == '-':
                        sr_to_vr[curr_sr_num] = VRNum
                        # print("sr 2; added " + str(VRNum) + " to idx " + str(curr_ir[curr_opcode_idx]))
                        VRNum+=1
                    curr_ir[VR1_IDX] = sr_to_vr[curr_sr_num]
                    max_vr_number = max(sr_to_vr[curr_sr_num], max_vr_number)
                    curr_ir[NU1_IDX] = lu[curr_sr_num]
                
                if is_valid_second_op(curr_opcode_idx):
                    valid_second_op = True
                    curr_sr_num = curr_ir[SR2_IDX]
                    if sr_to_vr[curr_sr_num] == '-':
                        sr_to_vr[curr_sr_num] = VRNum
                        # print("sr 2; added " + str(VRNum) + " to idx " + str(curr_ir[curr_opcode_idx]))
                        VRNum+=1
                    curr_ir[VR2_IDX] = sr_to_vr[curr_sr_num]
                    max_vr_number = max(sr_to_vr[curr_sr_num], max_vr_number)
                    curr_ir[NU2_IDX] = lu[curr_sr_num]

                if valid_first_op:
                    curr_sr_num = curr_ir[SR1_IDX]
                    # print("lu; added " + str(ir_list_idx) + " to idx " + str(curr_ir[sr_idx]))
                    lu[curr_sr_num] = ir_list_idx

                if valid_second_op:
                    curr_sr_num = curr_ir[SR2_IDX]
                    # print("lu; added " + str(ir_list_idx) + " to idx " + str(curr_ir[sr_idx]))
                    lu[curr_sr_num] = ir_list_idx
            
            ir_list_idx-=1
            # print("lu: ", lu)
            # print("Sr to Vr table: ", sr_to_vr)
            # print("Last used table: ", lu)
            # print()
            max_live = max(len(sr_to_vr) - sr_to_vr.count('-'), max_live)

            curr_ir = next(prev_ir)
            # print(curr_ir)
    except StopIteration:
        pass
        # print("Done renaming")
        # print("Max Live: ", max_live)

def allocate():
    global max_vr_number
    global max_pr_number
    global alloc_vr_to_pr
    global alloc_pr_to_vr
    global alloc_pr_to_nu
    global free_pr_stack
    global vr_to_spill_loc
    global rematerializable_vrs

    # Initialize VRToPR and PRToVR
    alloc_vr_to_pr = ['-'] * (max_vr_number + 1)
    alloc_pr_to_vr = ['-'] * (max_pr_number)
    alloc_pr_to_nu = [float('inf')] * (max_pr_number)
    rematerializable_vrs = ['-'] * (max_vr_number + 1)
    vr_to_spill_loc = [-1] * (max_vr_number + 1)
    # Initialize PRNU and push PRs
    for pr in range(max_pr_number):
        free_pr_stack.append(pr)
    # print(free_pr_stack)
    # curr_ir = ir_list.head.ir
    curr_ir = next(next_ir)
    # print("IR: ", curr_ir)

    if reserved_register == None: # No Spills
        try:
            while True:
                # print()
                # print("CURR IR: ", curr_ir)
                # print(alloc_vr_to_pr)
                curr_opcode_idx = curr_ir[OPCODE_IDX]
                valid_first_op = False
                valid_second_op = False

                if is_valid_first_op(curr_opcode_idx):
                    valid_first_op = True
                    vr1_num = curr_ir[VR1_IDX]
                    curr_ir[PR1_IDX] = alloc_vr_to_pr[vr1_num]

                if is_valid_second_op(curr_opcode_idx):
                    valid_second_op = True
                    if curr_opcode_idx == STORE_IDX:
                        vr3_num = curr_ir[VR3_IDX]
                        curr_ir[PR3_IDX] = alloc_vr_to_pr[vr3_num]
                    else:
                        vr2_num = curr_ir[VR2_IDX]
                        curr_ir[PR2_IDX] = alloc_vr_to_pr[vr2_num]

                # Free first op if last use
                if valid_first_op:
                    # if not isinstance(curr_ir[VR1_IDX], int):
                    if curr_ir[NU1_IDX] == float('inf'):
                        free_pr(curr_ir[PR1_IDX])

                # Free second op if last use
                if valid_second_op:
                    if curr_opcode_idx == STORE_IDX:
                        if curr_ir[NU3_IDX] == float('inf') and curr_ir[VR1_IDX] != curr_ir[VR3_IDX]:
                            free_pr(curr_ir[PR3_IDX])
                    else:
                        if curr_ir[NU2_IDX] == float('inf') and curr_ir[VR1_IDX] != curr_ir[VR2_IDX]:
                            free_pr(curr_ir[PR2_IDX])

                # Defs
                if is_valid_third_op(curr_opcode_idx):
                    is_first_op = False
                    vr3_num = curr_ir[VR3_IDX]
                    pr3_num = get_pr(vr3_num, curr_ir[NU3_IDX], is_first_op, curr_ir)
                    curr_ir[PR3_IDX] = pr3_num

                    if curr_ir[NU3_IDX] == float('inf'):
                        free_pr(pr3_num)

                if curr_ir[OPCODE_IDX] == LOADI_IDX: #loadI
                    print("loadI " + str(curr_ir[SR1_IDX]) + " => r" + str(curr_ir[PR3_IDX]))
                elif curr_ir[OPCODE_IDX] == LOAD_IDX or curr_ir[OPCODE_IDX] == STORE_IDX: #Load or Store
                    print(opcode_list[curr_ir[OPCODE_IDX]] + " r" + str(curr_ir[PR1_IDX]) + " => r" + str(curr_ir[PR3_IDX]))
                elif curr_ir[OPCODE_IDX] == OUTPUT_IDX: #output
                    print("output " + str(curr_ir[SR1_IDX]))
                elif curr_ir[OPCODE_IDX] == NOP_IDX: #nop
                    print("nop")
                else: # Add, sub, mult, lshift, rshift
                    print(opcode_list[curr_ir[OPCODE_IDX]] + " r" + str(curr_ir[PR1_IDX]) + ", r" + str(curr_ir[PR2_IDX]) + " => r" + str(curr_ir[PR3_IDX]))

                curr_ir = next(next_ir)

        except StopIteration:
            pass
    else: # Spills
        try:
            while True:
                # print()
                # print("CURR IR: ", curr_ir)
                # print(alloc_vr_to_pr)
                curr_opcode_idx = curr_ir[OPCODE_IDX]
                valid_first_op = False
                valid_second_op = False

                # First Op
                if is_valid_first_op(curr_opcode_idx):
                    is_first_op = True
                    valid_first_op = True
                    # if not isinstance(curr_ir[VR1_IDX], int):
                    vr1_num = curr_ir[VR1_IDX]
                    if alloc_vr_to_pr[vr1_num] == '-':
                        pr1_num = get_pr(vr1_num, curr_ir[NU1_IDX], is_first_op, curr_ir)
                        curr_ir[PR1_IDX] = pr1_num
                        restore(vr1_num, pr1_num)
                    else:
                        curr_pr_num = alloc_vr_to_pr[vr1_num]
                        curr_ir[PR1_IDX] = curr_pr_num
                        alloc_pr_to_nu[curr_pr_num] = curr_ir[NU1_IDX]

                # Second Op
                if is_valid_second_op(curr_opcode_idx):
                    is_first_op = False
                    valid_second_op = True
                    if curr_opcode_idx == STORE_IDX:
                        vr3_num = curr_ir[VR3_IDX]
                        if alloc_vr_to_pr[vr3_num] == '-':
                            pr3_num = get_pr(vr3_num, curr_ir[NU3_IDX], is_first_op, curr_ir)
                            curr_ir[PR3_IDX] = pr3_num
                            restore(vr3_num, pr3_num)
                        else:
                            curr_pr_num = alloc_vr_to_pr[vr3_num]
                            curr_ir[PR3_IDX] = curr_pr_num
                            alloc_pr_to_nu[curr_pr_num] = curr_ir[NU3_IDX]
                    else:
                        vr2_num = curr_ir[VR2_IDX]
                        if alloc_vr_to_pr[vr2_num] == '-':
                            pr2_num = get_pr(vr2_num, curr_ir[NU2_IDX], is_first_op, curr_ir)
                            curr_ir[PR2_IDX] = pr2_num
                            restore(vr2_num, pr2_num)
                        else:
                            curr_pr_num = alloc_vr_to_pr[vr2_num]
                            curr_ir[PR2_IDX] = curr_pr_num
                            alloc_pr_to_nu[curr_pr_num] = curr_ir[NU2_IDX]

                # Free first op if last use
                if valid_first_op:
                    if curr_ir[NU1_IDX] == float('inf'):
                        free_pr(curr_ir[PR1_IDX])

                # Free second op if last use
                if valid_second_op:
                    if curr_opcode_idx == STORE_IDX:
                        if curr_ir[NU3_IDX] == float('inf') and curr_ir[VR1_IDX] != curr_ir[VR3_IDX]:
                            free_pr(curr_ir[PR3_IDX])
                    else:
                        if curr_ir[NU2_IDX] == float('inf') and curr_ir[VR1_IDX] != curr_ir[VR2_IDX]:
                            free_pr(curr_ir[PR2_IDX])

                # Defs
                if is_valid_third_op(curr_opcode_idx):
                    is_first_op = False
                    if curr_opcode_idx == LOADI_IDX:
                        vr3_num = curr_ir[VR3_IDX]
                        pr3_num = get_pr(vr3_num, curr_ir[NU3_IDX], is_first_op, curr_ir)
                        curr_ir[PR3_IDX] = pr3_num
                        rematerializable_vrs[vr3_num] = curr_ir[SR1_IDX]
                    else:
                        vr3_num = curr_ir[VR3_IDX]
                        pr3_num = get_pr(vr3_num, curr_ir[NU3_IDX], is_first_op, curr_ir)
                        curr_ir[PR3_IDX] = pr3_num
                        rematerializable_vrs[vr3_num] = "-"

                if curr_ir[OPCODE_IDX] == LOADI_IDX: #loadI
                    print("loadI " + str(curr_ir[SR1_IDX]) + " => r" + str(curr_ir[PR3_IDX]))
                elif curr_ir[OPCODE_IDX] == LOAD_IDX or curr_ir[OPCODE_IDX] == STORE_IDX: #Load or Store
                    print(opcode_list[curr_ir[OPCODE_IDX]] + " r" + str(curr_ir[PR1_IDX]) + " => r" + str(curr_ir[PR3_IDX]))
                elif curr_ir[OPCODE_IDX] == OUTPUT_IDX: #output
                    print("output " + str(curr_ir[SR1_IDX]))
                elif curr_ir[OPCODE_IDX] == NOP_IDX: #nop
                    print("nop")
                else: # Add, sub, mult, lshift, rshift
                    print(opcode_list[curr_ir[OPCODE_IDX]] + " r" + str(curr_ir[PR1_IDX]) + ", r" + str(curr_ir[PR2_IDX]) + " => r" + str(curr_ir[PR3_IDX]))

                curr_ir = next(next_ir)
        except StopIteration:
            pass

def build_graph():
    global most_recent_output_idx
    global most_recent_load_idx
    global most_recent_store_idx

    for i in range(ir_list.len):
        curr_node = [i, '-', '-', '-', '-', '-']
        nodes_list.append(curr_node)

    vr_to_node_idx = ['-' for i in range(ir_list.len + 1)]

    curr_ir = next(next_ir)
    curr_ir_idx = 0
    default_priority = -1
    try:
        while True:
            curr_opcode_idx = curr_ir[OPCODE_IDX]
            if curr_ir[1] == 1: #loadI
                node_full_op = "loadI " + str(curr_ir[2]) + " => r" + str(curr_ir[11])
            elif curr_ir[1] == 0 or curr_ir[1] == 2: #Load or Store
                node_full_op = opcode_list[curr_ir[1]] + " r" + str(curr_ir[3]) + " => r" + str(curr_ir[11])
            elif curr_ir[1] == 8: #output
                node_full_op = "output " + str(curr_ir[2])
            elif curr_ir[1] == 9: #nop
                node_full_op = "nop"
            else: # Add, sub, mult, lshift, rshift
                node_full_op = opcode_list[curr_ir[1]] + " r" + str(curr_ir[3]) + ", r" + str(curr_ir[7]) + " => r" + str(curr_ir[11])

            node = [curr_ir_idx, curr_opcode_idx, node_full_op, '-', '-', op_idx_to_latency[curr_opcode_idx], default_priority, NOT_YET_READY]
            nodes_list[curr_ir_idx] = node

            if is_valid_third_op(curr_opcode_idx):
                vr_to_node_idx[curr_ir[VR3_IDX]] = node[NODE_IDX]
            if is_valid_first_op(curr_opcode_idx):
                node_idx = vr_to_node_idx[curr_ir[VR1_IDX]]
                add_edge(node, nodes_list[node_idx], nodes_list[node_idx][NODE_DELAY_IDX], "Data")
            if is_valid_second_op(curr_opcode_idx):
                if curr_opcode_idx == STORE_IDX:
                    node_idx = vr_to_node_idx[curr_ir[VR3_IDX]]
                else:
                    node_idx = vr_to_node_idx[curr_ir[VR2_IDX]]
                add_edge(node, nodes_list[node_idx], nodes_list[node_idx][NODE_DELAY_IDX], "Data")




            if curr_opcode_idx == LOAD_IDX:
                most_recent_load_idx = curr_ir[IR_LIST_OP_IDX]
                loads_list.append(most_recent_load_idx)
                if most_recent_store_idx:
                    add_edge(node, nodes_list[most_recent_store_idx], 5, "Conflict")
            elif curr_opcode_idx == STORE_IDX:
                if most_recent_store_idx: # TODO: This is causing self loop???; Fixed but double check
                    add_edge(node, nodes_list[most_recent_store_idx], 1, "Serial")
                most_recent_store_idx = curr_ir_idx
                if most_recent_output_idx:
                    add_edge(node, nodes_list[most_recent_output_idx], 1, "Serial")
                for i in loads_list:
                    to_node = nodes_list[i]
                    add_edge(node, to_node, 1, "Serial") # TODO Causing extra edge; Also need to check other places
            elif curr_opcode_idx == OUTPUT_IDX:
                if most_recent_store_idx: 
                    add_edge(node, nodes_list[most_recent_store_idx], 5, "Conflict")
                if most_recent_output_idx: # TODO: This is causing self loop???; Fixed but double check
                    add_edge(node, nodes_list[most_recent_output_idx], 1, "Serial")
                most_recent_output_idx = curr_ir_idx
            curr_ir_idx += 1
            curr_ir = next(next_ir)

    except StopIteration:
        pass

def make_schedule(parent_to_child_map, child_to_parent_map):
    global nodes_list
    active = []
    schedule = []
    ready = []
    for node in nodes_list:
        if node[NODE_SUCC_IDX] == '-':
            ready.append(node)
    
    sorted_ready = sorted(ready, key=lambda x: x[6], reverse=True)
    ready = sorted_ready

    curr_cycle = 1

    while (len(ready) != 0 or len(active) != 0):
        sorted_ready = sorted(ready, key=lambda x: x[6], reverse=True)
        ready = sorted_ready

        # print(curr_cycle)
        # print(ready)
        op0, op1 = get_scheduled_ops(ready)
        # print(op0, op1)
        # print()
    
        if (op0[NODE_OP_IDX] != NOP_IDX):
            op0[NODE_STATUS_IDX] = ACTIVE
            active.append((op0, op0[NODE_DELAY_IDX] + curr_cycle))
        if (op1[NODE_OP_IDX] != NOP_IDX):
            op1[NODE_STATUS_IDX] = ACTIVE
            active.append((op1, op1[NODE_DELAY_IDX] + curr_cycle))
        # print(curr_cycle)
        # print()
        schedule.append((curr_cycle, op0, op1))

        curr_cycle += 1

        retired = []
        for active_node, active_cycle in active:
            if (active_cycle == curr_cycle):
                retired.append((active_node, active_cycle))
                active_node[NODE_STATUS_IDX] = RETIRED

        for retired_node, retired_cycle in retired:
            active.remove((retired_node, retired_cycle))
            # print(child_to_parent_map)
            if retired_node[NODE_IDX] in child_to_parent_map:
                for parent, latency in child_to_parent_map[retired_node[NODE_IDX]]:    
                    is_ready = True
                    for child, latency in parent_to_child_map[parent]:
                        if (nodes_list[child][NODE_STATUS_IDX] != RETIRED):
                            is_ready = False
                    if (is_ready):
                        if (nodes_list[parent] not in ready):
                            nodes_list[parent][NODE_STATUS_IDX] = READY
                            ready.append(nodes_list[parent])

        # for active_node, active_cycle in active:
        #     if active_node[NODE_OP_IDX] in [LOAD_IDX, STORE_IDX, MULT_IDX]: # Multicycle: Load store and mult ops
        #         if active_node[NODE_IDX] in child_to_parent_map:
        #             for parent, latency in child_to_parent_map[active_node[NODE_IDX]]:
        #                 is_ready = True
        #                 for child, latency in parent_to_child_map[parent]:
        #                     if (nodes_list[child][NODE_STATUS_IDX] != RETIRED):
        #                         is_ready = False
        #                 if (is_ready):
        #                     # Add any early release to ready
        #                     if (nodes_list[parent] not in ready):
        #                         nodes_list[parent][NODE_STATUS_IDX] = READY
        #                         ready.append(nodes_list[parent])

    return schedule

def get_scheduled_ops(ready):
        op0 = None
        op1 = None

        if (len(ready) == 0):
            return [['-', NOP_IDX, "nop", "-", "-", "-", "-", "-"], ['-', NOP_IDX, "nop", "-", "-", "-", "-", "-"]]
        
        restricted_ready = []
        unrestricted_ready = []
        for node in ready:
            if (node[NODE_OP_IDX] == LOAD_IDX or node[NODE_OP_IDX] == STORE_IDX or node[NODE_OP_IDX] == MULT_IDX or node[NODE_OP_IDX] == OUTPUT_IDX):
                node[NODE_STATUS_IDX] = READY
                restricted_ready.append(node)
            else:
                unrestricted_ready.append(node)
                node[NODE_STATUS_IDX] = READY

        for node in restricted_ready:
            if (op0 == None or op1 == None):
                if (node[NODE_OP_IDX] == LOAD_IDX or node[NODE_OP_IDX] == STORE_IDX):
                    if (op0 == None):
                        op0 = node
                if (node[NODE_OP_IDX] == MULT_IDX):
                    if (op1 == None):
                        op1 = node
                if (node[NODE_OP_IDX] == OUTPUT_IDX):
                    if (op0 == None and op1 == None):
                        op0 = node
                        op1 = ['-', NOP_IDX, "nop", "-", "-", "-", "-", "-"]
                        ready.remove(node)
                        return op0, op1
        
        if (op0 != None and op1 != None):
            if (op0 in ready):
                ready.remove(op0)
            if (op1 in ready):
                ready.remove(op1)
            return op0, op1

        if (op0 != None and op0 in ready):
            ready.remove(op0)
        if (op0 != None and op0 in restricted_ready):
            restricted_ready.remove(op0)
        if (op1 != None and op1 in ready):
            ready.remove(op1)
        if (op1 != None and op1 in restricted_ready):
            restricted_ready.remove(op1)

        for node in unrestricted_ready:
            if (node[NODE_OP_IDX] == LOADI_IDX):
                if (op0 != node and op1 != node):
                    if (op0 == None):
                        op0 = node
                    elif (op1 == None):
                        op1 = node

        if (op0 in ready):
            ready.remove(op0)
        if (op0 in unrestricted_ready):
            unrestricted_ready.remove(op0)
        if (op1 in ready):
            ready.remove(op1)
        if (op1 in unrestricted_ready):
            unrestricted_ready.remove(op1)
        
        if (op0 != None and op1 != None):
            return op0, op1
        

        if (len(unrestricted_ready) == 0):
            if (op0 == None):
                op0 = ['-', NOP_IDX, "nop", "-", "-", "-", "-", "-"]
            if (op1 == None):
                op1 = ['-', NOP_IDX, "nop", "-", "-", "-", "-", "-"]
            return op0, op1

        if (len(unrestricted_ready) == 1):
            if (op0 == None and op1 == None):
                op0 = unrestricted_ready[0]
                op1 = ['-', NOP_IDX, "nop", "-", "-", "-", "-", "-"]
            elif (op0 == None):
                op0 = unrestricted_ready[0]
            elif (op1 == None):
                op1 = unrestricted_ready[0]
            
            if (op0 in ready):
                ready.remove(op0)
            if (op0 in unrestricted_ready):
                unrestricted_ready.remove(op0)
            if (op1 in ready):
                ready.remove(op1)
            if (op1 in unrestricted_ready):
                unrestricted_ready.remove(op1)
            return op0, op1

        if (len(unrestricted_ready) == 2):
            if (op0 == None and op1 == None):
                op0 = unrestricted_ready[0]
                op1 = unrestricted_ready[1]
            elif (op0 == None):
                op0 = unrestricted_ready[0]
            elif (op1 == None):
                op1 = unrestricted_ready[0]

            if (op0 in ready):
                ready.remove(op0)
            if (op0 in unrestricted_ready):
                unrestricted_ready.remove(op0)
            if (op1 in ready):
                ready.remove(op1)
            if (op1 in unrestricted_ready):
                unrestricted_ready.remove(op1)
            return op0, op1
                

        if (len(unrestricted_ready) > 2):
            highest_priority_nodes = []
            highest_priority = unrestricted_ready[0][NODE_PRIORITY_IDX]

            for node in unrestricted_ready:
                if (node[NODE_PRIORITY_IDX] == highest_priority):
                    highest_priority_nodes.append(node)


            if (op0 == None):
                for node in highest_priority_nodes:
                    if (node[NODE_OP_IDX] != MULT_IDX):
                        op0 = node
                        break

            if (op0 != None):
                if (op0 in highest_priority_nodes):
                    highest_priority_nodes.remove(op0)
                if (op0 in ready):
                    ready.remove(op0)
                if (op0 in unrestricted_ready):
                    unrestricted_ready.remove(op0)
                
                if op0[NODE_OP_IDX] == OUTPUT_IDX:

                    return [op0, ['-', NOP_IDX, "nop", "-", "-", "-", "-", "-"]]
                

                if (len(highest_priority_nodes) == 0):
                    if (len(ready) == 0):
                        return [op0, ['-', NOP_IDX, "nop", "-", "-", "-", "-", "-"]]
                    else:
                        highest_priority = unrestricted_ready[0][NODE_PRIORITY_IDX]
                        for node in unrestricted_ready:
                            if (node[NODE_PRIORITY_IDX] == highest_priority):
                                highest_priority_nodes.append(node)
            else:
                op0 = ['-', NOP_IDX, "nop", "-", "-", "-", "-", "-"]
            
            if (op1 == None):
                for node in highest_priority_nodes:
                    if (node[NODE_OP_IDX] != LOAD_IDX and node[NODE_OP_IDX] != STORE_IDX):
                        op1 = node
                        break
            
            if (op1 == None):
                op1 = ['-', NOP_IDX, "nop", "-", "-", "-", "-", "-"]
            else:
                if (op1 in ready):
                    ready.remove(op1)
                if (op1 in unrestricted_ready):
                    unrestricted_ready.remove(op1)
                if (op1 in highest_priority_nodes):
                    highest_priority_nodes.remove(op1)
            
        if (op0 == None):
            op0 = ['-', NOP_IDX, "nop", "-", "-", "-", "-", "-"]
        if (op1 == None):
            op1 = ['-', NOP_IDX, "nop", "-", "-", "-", "-", "-"]
        return op0, op1



'''
*********************************************************************
********************** CMD LINE PARSING: ****************************
*********************************************************************
'''
args = sys.argv
if len(sys.argv) > 1:
    filename = sys.argv[-1]
    if not os.path.exists(filename):
        print(f"ERROR: Could not open file '{filename}' as the input file.")
        handle_h_flag()
        sys.exit(1)
    flags = ['-h']
    detected_flags = []
    for arg in sys.argv[1:]:
        if arg.startswith('-'):
            if arg == '-h':
                handle_h_flag()
                sys.exit(1)
    if len(detected_flags) == 0:
        handle_scheduling(filename)
    elif(len(detected_flags) > 1):
        print("ERROR: Multiple flags detected:", ', '.join(detected_flags))
        handle_h_flag()
        sys.exit(1)
else:
    print("ERROR: Incorrect or incompatible command-line")
    handle_h_flag()
    sys.exit(1)