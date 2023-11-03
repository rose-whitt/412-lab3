import math


MEMOP = 0   # load, store
LOADI = 1   # loadI
ARITHOP = 2 # add, sub, mult, lshift, rshift
OUTPUT = 3  # output, prints MEM(x) to stdout
NOP = 4     # nop, idle for one second
CONSTANT = 5    # a non-negative integer
REGISTER = 6    # 'r' followed by a constant
COMMA = 7   # ','
INTO = 8    # "=>"
EOF = 9     # input has been exhausted
EOL = 10    # end of current line ("\r\n" or "\n")


SR = 0
VR = 1
PR = 2
NU = 3
opcodes_list = ["load", "store", "loadI", "add", "sub", "mult", "lshift", "rshift", "output", "nop"]

# TODO: classes slow it down so make these not classes later
# class Operand:
#     def __init__(self):
#         self.sr = None
#         self.vr = None
#         self.pr = None
#         self.nu = math.inf
#     def __str__(self):
#         return "[ SR: " + str(self.sr) + " , VR: " + str(self.vr) + " , PR: " + str(self.pr) + " , NU: " + str(self.nu) + " ]"



class Node:
    """
    A node in the IR's doubly linked list.
    """
    def __init__(self):
        """
        - value: representation of block record for operation ([line num, opcode, [sr, vr, pr, nu], [sr, vr, pr, nu], [sr, vr, pr, nu]])
        - next: next record pointer
        - prev: previous record pointer
        """
        # line num, opcode, [sr, vr, pr, nu], [sr, vr, pr, nu], [sr, vr, pr, nu]
        # TODO: possibly not do a nested list structure and do class for operand for speed
        # self.value = [None, None, Operand(), Operand(), Operand()]
        self.line = None
        self.opcode = None
        # self.arg1 = Operand()
        self.arg1 = [None, None, None, -1]
        # self.arg2 = Operand()
        self.arg2 = [None, None, None, -1]
        # self.arg3 = Operand()
        self.arg3 = [None, None, None, -1]

        self.next = None
        self.prev = None
    
    

    
    def __str__(self):
        l0 = self.arg1.sr   # SR slot in first record list
        opcode = self.opcode  # value[1] = (category, opcode)- we want the opcode
        # print("opcode: " + str(opcode))
        if (opcode == 0 or opcode == 1 or (opcode >= 3 and opcode <= 7)):
            l0 = "sr" + str(l0)
        elif (opcode == 2 or opcode == 8):
            l0 = "val " + str(l0)
        else:
            l0 = ""
        
        # List 1- fourth elem in record list
        l1 = self.arg2.sr
        if (opcode >= 3 and opcode <= 7):
            l1 = "sr" + str(l1)
        else:
            l1 = ""
        
        # List 2- fifth element in record list
        l2 = self.arg3.sr
        if (opcode >= 0 and opcode <= 7):
            l2 = "sr" + str(l2)
        else:
            l2 = ""
        
        # temp_str = str(self.line) + " : " +  opcodes_list[opcode] + " : [ "  + l0 + " ] , [ " + l1 + " ], [ " + l2 + " ]\n"
        temp_str = str(self.line) + " : " +  opcodes_list[opcode] + " : [ "  + l0 + " ] , [ " + l1 + " ], [ " + l2 + " ]"

            
        return temp_str
        

    

    # to str
    #     st jskfgldksfg;dgsjlfn value\n
    #     return str


class LinkedList:
    """
    Represents doubly linked list for the IR.
    """
    def __init__(self):
        self.head = None
        self.tail = None
        self.categories = ["MEMOP", "LOADI", "ARITHOP", "OUTPUT", "NOP", "CONST", "REG", "COMMA", "INTO", "ENDFILE", "NEWLINE"]
        self.opcodes = ["load", "store", "loadI", "add", "sub", "mult", "lshift", "rshift", "output", "nop"]
        self.length = 0

    def append(self, node: Node):
        self.length += 1
        if self.head == None and self.tail == None: # empty
            self.head = node
            self.tail = node
        else:
            self.tail.next = node
            node.prev = self.tail
            self.tail = node
    
    def insert_before(self, new_node: Node, aft_node: Node):
        """
        Insert a node before the specified node

        Inputs:
        - new_node: the node being inserted
        - aft_node: the node that will come after new_node
        """
        # print("aft node line num: " + str(aft_node.line))

        if (aft_node == self.head):
            new_node.next = aft_node
            aft_node.prev = new_node
            self.head = new_node
        else:
            new_node.prev = aft_node.prev
            new_node.next = aft_node
            aft_node.prev.next = new_node
            aft_node.prev = new_node
        
        # handle line nums
        # print("new node line num: " + str(new_node.line))
        # print("aft node line num: " + str(aft_node.line))
        # NOTE: this doesnt seem to change the print_allocated_file output, but it does change the actual IR 
        # new_node.line = aft_node.line
        # start = aft_node
        # while (start != None):
        #     start.line += 1
        #     start = start.next


        self.length += 1
    
    def print_list(self):
        start = self.head
        temp_string = ""
        while (start != None):
            temp_string += str(start)
            start = start.next
        print(temp_string)
    
    def print_table(self, list):

        print('//' + "{:<8} {:<8} {:<10} | {:<5} {:<5} {:<5} {:<5} | {:<5} {:<5} {:<5} {:<5} | {:<5} {:<5} {:<5} {:<5} | {:<15} ".format("index", "line", "OPCODE", "SR", "VR", "PR", "NU", "SR", "VR", "PR", "NU", "SR", "VR", "PR", "NU", "NEXT OP"))

        start = list.head

        i = 0
        while (start != None):
            # temp_line = start.line
            # if (temp_line == None):
            #     temp_line = -1
            # temp_opcode = self.opcodes[start.opcode]
            # if (temp_opcode):
            #     temp_opcode = -1
            
            
            # print('//' + "{:<8} {:<8} {:<10} | {:<5} {:<5} {:<5} {:<5} | {:<5} {:<5} {:<5} {:<5} | {:<5} {:<5} {:<5} {:<5} | {:<15} ".format(i, start.line, self.opcodes[start.opcode], str(start.arg1.sr), str(start.arg1.vr), str(start.arg1.pr), str(start.arg1.nu), str(start.arg2.sr), str(start.arg2.vr), str(start.arg2.pr), str(start.arg2.nu),  str(start.arg3.sr), str(start.arg3.vr), str(start.arg3.pr), str(start.arg3.nu), i))
            temp_line = start.line if start.line is not None else -1
            temp_opcode = self.opcodes[start.opcode] if start.opcode is not None else -1
            temp_arg1_sr = str(start.arg1.sr) if start.arg1.sr is not None else -1
            temp_arg1_vr = str(start.arg1.vr) if start.arg1.vr is not None else -1
            temp_arg1_pr = str(start.arg1.pr) if start.arg1.pr is not None else -1
            temp_arg1_nu = str(start.arg1.nu) if start.arg1.nu is not None else -1
            temp_arg2_sr = str(start.arg2.sr) if start.arg2.sr is not None else -1
            temp_arg2_vr = str(start.arg2.vr) if start.arg2.vr is not None else -1
            temp_arg2_pr = str(start.arg2.pr) if start.arg2.pr is not None else -1
            temp_arg2_nu = str(start.arg2.nu) if start.arg2.nu is not None else -1
            temp_arg3_sr = str(start.arg3.sr) if start.arg3.sr is not None else -1
            temp_arg3_vr = str(start.arg3.vr) if start.arg3.vr is not None else -1
            temp_arg3_pr = str(start.arg3.pr) if start.arg3.pr is not None else -1
            temp_arg3_nu = str(start.arg3.nu) if start.arg3.nu is not None else -1
            print('//' + "{:<8} {:<8} {:<10} | {:<5} {:<5} {:<5} {:<5} | {:<5} {:<5} {:<5} {:<5} | {:<5} {:<5} {:<5} {:<5} | {:<15} ".format(i, temp_line, temp_opcode, temp_arg1_sr, temp_arg1_vr, temp_arg1_pr, temp_arg1_nu, temp_arg2_sr, temp_arg2_vr, temp_arg2_pr, temp_arg2_nu, temp_arg3_sr, temp_arg3_vr, temp_arg3_pr, temp_arg3_nu, i))
            start = start.next
            i += 1


    def human_readable(self, value):
        """
        Convert values to human readable strings and print them in IR format
        """
        # List 0- third elem in record list
        # print("line: " + str(value[0]))
        l0 = value[2][SR]   # SR slot in first record list
        opcode = value[1]  # value[1] = (category, opcode)- we want the opcode
        if (opcode == 0 or opcode == 1 or (opcode >= 3 and opcode <= 7)):
            l0 = "sr" + str(l0)
        elif (opcode == 2 or opcode == 8):
            l0 = "val " + str(l0)
        else:
            l0 = ""
        
        # List 1- fourth elem in record list
        l1 = value[3][SR]
        if (opcode >= 3 and opcode <= 7):
            l1 = "sr" + str(l1)
        else:
            l1 = ""
        
        # List 2- fifth element in record list
        l2 = value[4][SR]
        if (opcode >= 0 and opcode <= 7):
            l2 = "sr" + str(l2)
        else:
            l2 = ""
        
        temp_str = str(value[0]) + " : " +  self.opcodes[opcode] + " : [ "  + l0 + " ] , [ " + l1 + " ], [ " + l2 + " ]\n"

        return temp_str
        # print(f"{self.opcodes[opcode] : <6}  [ {l0} ], [ {l1} ], [ {l2} ]")
    
    def print_full_line(self, node):
        temp_line = node.line if node.line is not None else -1
        temp_opcode = self.opcodes[node.opcode] if node.opcode is not None else -1
        temp_arg1_sr = str(node.arg1.sr) if node.arg1.sr is not None else -1
        temp_arg1_vr = str(node.arg1.vr) if node.arg1.vr is not None else -1
        temp_arg1_pr = str(node.arg1.pr) if node.arg1.pr is not None else -1
        temp_arg1_nu = str(node.arg1.nu) if node.arg1.nu is not None else -1
        temp_arg2_sr = str(node.arg2.sr) if node.arg2.sr is not None else -1
        temp_arg2_vr = str(node.arg2.vr) if node.arg2.vr is not None else -1
        temp_arg2_pr = str(node.arg2.pr) if node.arg2.pr is not None else -1
        temp_arg2_nu = str(node.arg2.nu) if node.arg2.nu is not None else -1
        temp_arg3_sr = str(node.arg3.sr) if node.arg3.sr is not None else -1
        temp_arg3_vr = str(node.arg3.vr) if node.arg3.vr is not None else -1
        temp_arg3_pr = str(node.arg3.pr) if node.arg3.pr is not None else -1
        temp_arg3_nu = str(node.arg3.nu) if node.arg3.nu is not None else -1
        print('//' + "{:<8} {:<10} | {:<5} {:<5} {:<5} {:<5} | {:<5} {:<5} {:<5} {:<5} | {:<5} {:<5} {:<5} {:<5}".format(temp_line, temp_opcode, temp_arg1_sr, temp_arg1_vr, temp_arg1_pr, temp_arg1_nu, temp_arg2_sr, temp_arg2_vr, temp_arg2_pr, temp_arg2_nu, temp_arg3_sr, temp_arg3_vr, temp_arg3_pr, temp_arg3_nu))
        