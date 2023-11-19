import scanner
from IR_List import *
import lab1
import sys
import math
import cProfile, pstats
from io import StringIO



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
BLANK = 11     # not an opcode, but used to signal blank space or tab
SCANNER_ERROR = 12

SR_IDX = 0
VR_IDX = 1
PR_IDX = 2
NU_IDX = 3

class Lab2:
    """
    
        is_rematerializable: list of loadI nodes that are rematerializable 
    """
    def __init__(self, file):
        # print("LAB 2 INIT")
        self.file = file
        # Get IR
        self.Lab_1 = lab1.Lab1()  # init

        self.Lab_1.main(self.file, True, False)
        # self.Lab_1 = Lab_1

        self.IR_LIST = self.Lab_1.ir_list
        # self.IR_LIST = ir_list

        # self.IR_LIST.print_table(self.IR_LIST)

        self.max_sr_num = self.Lab_1.max_reg
        # self.max_sr_num = max_reg

        self.num_srs_filled = self.Lab_1.num_srs
        # self.num_srs_filled = num_srs


        self.VR_name = 0    # renaming
        self.SR_to_VR = []  # renaming
        self.LU = []    # renaming


        # ALLOCATION STUFF
        self.max_vr_num = 0
        self.k = 0
        # Allocator maps
        self.VRToPR = {}    # vr is the index, pr is the value
        
        self.PRToVR = {}    # pr is the index, vr is the value
        self.VRToSpillLoc = {}
        self.PRNU = {}

        self.PRStack = [] # for spilling- (push and pop in algo)
        # self.PRMark = {}  # make sure you're not reusing a pr in the current line
        self.cur_PR = -1
        self.spilled = []
        self.spill_loc = 32768  # and higher reserved for allocator
        self.reserved_reg = -1
        self.max_live = 0
        self.count_live = 0

        self.opcodes_list = ["load", "store", "loadI", "add", "sub", "mult", "lshift", "rshift", "output", "nop"]

        self.stop_running = False

        self.is_rematerializable = []   # add loadIs from renaming, kinda redundant but dont move bc when stopped using the cc5 cycles went up a lot
        self.remat_VRs = {} # map of just the vr of the rematerializable vrs (loadi defined) to the constant of the loadi
        self.remat_spilled = [] # stores the spilled rematerializable vrs for restoring
    

    """
        operand: argument to get based on opnum
    
    """
    def allocate_use(self, op_num, node, operand):
        # self.IR_LIST.print_full_line(node)
        virt_reg = operand[VR_IDX]

        # not spilled, get pr
        # virt reg comes from node, which comes from head in while loop in dif_alloc
        if (virt_reg not in self.spilled):   # virtual register of cur operation not spilled
            phys_reg = self.VRToPR[virt_reg]
            operand[PR_IDX] = phys_reg
            self.PRNU[phys_reg] = operand[NU_IDX]
        # spilled, restore
        else:
            phys_reg = self.restore(node, operand)
            self.spilled.remove(virt_reg)
        return phys_reg
    
    def free_use(self, op_num, node, operand):
        
        old_phys_reg = operand[PR_IDX]

        # check if able to free
        if (operand[NU_IDX] == INF):
            self.PRStack.append(old_phys_reg)
            # free pr in maps
            old_virt_reg = self.PRToVR[old_phys_reg]
            self.PRToVR[old_phys_reg] = None
            self.VRToPR[old_virt_reg] = None


    """
        Called in allocate_use if value of node has been spilled

    """
    def restore(self, node, operand):
        
        VR = operand[VR_IDX]

        # get new pr to hold restored vr
        if (len(self.PRStack) > 0):
            PR = self.PRStack.pop()
        else:
            PR = self.spill(node)
   
        # what kind of restore we gonna do
        if (VR in self.remat_spilled):    # just restore the loadi
            # create and add load immediate instruction
            loadi_node = Node()
            loadi_node.opcode = 2
            loadi_node.arg1[SR_IDX] = self.VRToSpillLoc[VR]
            loadi_node.arg3[PR_IDX] = PR
            self.IR_LIST.insert_before(loadi_node, node)
            self.remat_spilled.remove(VR)
        else:
            # create and add loadI
            loadi_node = Node()
            loadi_node.opcode = LOADI_OP
            loadi_node.arg1[SR_IDX] = self.VRToSpillLoc[VR]
            loadi_node.arg3[PR_IDX] = PR
            self.IR_LIST.insert_before(loadi_node, node)
            # create and add load
            load_node = Node()
            load_node.opcode = LOAD_OP
            load_node.arg1[PR_IDX] = PR
            load_node.arg3[VR_IDX] = VR
            load_node.arg3[PR_IDX] = PR
            self.IR_LIST.insert_before(load_node, node)

        # update maps
        self.VRToPR[VR] = PR
        self.PRToVR[PR] = VR
        self.PRNU[PR] = operand[NU_IDX]
        operand[PR_IDX] = PR

        return PR
    
    def spill(self, node):
        
        # get PR to free
        free_PR = max(self.PRNU, key=self.PRNU.get)
        if (free_PR == self.cur_PR):
            PRNU_copy = self.PRNU.copy()
            PRNU_copy.pop(free_PR)
            free_PR = max(PRNU_copy, key=PRNU_copy.get)
        
        spill_VR = self.PRToVR[free_PR]
        self.VRToPR[spill_VR] = None
        
        # dont spill twice
        if (spill_VR in self.spilled):
            return free_PR
        
        if (spill_VR in self.remat_VRs):
            self.remat_spilled.append(spill_VR)
            self.VRToSpillLoc[spill_VR] = self.remat_VRs[spill_VR]    # spill location (the loadi constant) is this loadI's constant, so dont need to increment
        else:
            # create and add loadI- put spill location addy into reserved reg; Q: should I still update spil location?
            loadi_node = Node()
            loadi_node.opcode = LOADI_OP
            loadi_node.arg1[SR_IDX] = self.spill_loc
            loadi_node.arg3[PR_IDX] = self.reserved_reg
            self.IR_LIST.insert_before(loadi_node, node)
            # create and add store- move spilled value from spill location into its new PR
            store_node = Node()
            store_node.opcode = STORE_OP
            store_node.arg1[VR_IDX] = spill_VR
            store_node.arg1[PR_IDX] = free_PR
            store_node.arg3[PR_IDX] = self.reserved_reg
            self.IR_LIST.insert_before(store_node, node)
            # update spill location
            self.VRToSpillLoc[spill_VR] = self.spill_loc
            self.spill_loc += 4

        # add to spilled array whether remat or not
        self.spilled.append(spill_VR)


        return free_PR
    
    def print_allocated_file(self):
        """
        Prints allocated file in human readable format
        """

        node = self.IR_LIST.head

        ret = ""

        while (node != None):
            # load or store
            if (node.opcode == LOAD_OP or node.opcode == STORE_OP):
                temp = self.opcodes_list[node.opcode] + "  r" + str(node.arg1[PR_IDX]) + "  =>   r" + str(node.arg3[PR_IDX]) + "\n"
                ret += temp
            # loadI
            elif (node.opcode == LOADI_OP):
                temp = self.opcodes_list[node.opcode] + "  " + str(node.arg1[SR_IDX]) + "  =>   r" + str(node.arg3[PR_IDX]) + "\n"
                ret += temp
            # arithop
            elif (node.opcode >= ADD_OP and node.opcode <= RSHIFT_OP):
                temp = self.opcodes_list[node.opcode] + "  r" + str(node.arg1[PR_IDX]) + ", r" + str(node.arg2[PR_IDX]) + "  =>   r" + str(node.arg3[PR_IDX]) + "\n"
                ret += temp
            # output
            elif (node.opcode == OUTPUT_OP):
                temp = self.opcodes_list[node.opcode] + "  " + str(node.arg1[SR_IDX]) + "\n"
                ret += temp
            # nop- WONT HAPPEN BC OF MY RENAME BUT JUST IN CASE
            elif (node.opcode == NOP_OP):
                temp = self.opcodes_list[node.opcode] + "\n"
                ret += temp
                # print(f"{self.opcodes_list[node.opcode] : <7}")
            
            node = node.next
        print(ret)
    
    def dif_alloc(self, k):

        # -----------initialization-----------
        self.max_vr_num = self.get_max_vr()
        self.k = k
        self.VRToPR = {i: None for i in range(self.max_vr_num + 1)}
        self.PRToVR = {i: None for i in range(self.k - 1)}  # keep it as normal k
        self.VRToSpillLoc = {}
        self.PRNU = {i: INF for i in range(self.k - 1)}
        self.PRStack = []
        # for i in range(0, self.k - 1):
        #     self.PRStack.append(i)
        self.PRStack = [i for i in range(0, self.k - 1)]    # list comprehension is faster

        self.PRStack.reverse()
        self.reserved_reg = self.k - 1
        if (self.max_live > self.k):
            self.k = self.k - 1
            self.reserved_reg = self.k
        # get remat VRs
        # for x in self.is_rematerializable:
        #     # self.remat_VRs.append(x.arg3.vr)
        #     self.remat_VRs[x.arg3[VR_IDX]] = x.arg1[SR_IDX]
        # list comprehension faster
        self.remat_VRs = {x.arg3[VR_IDX]: x.arg1[SR_IDX] for x in self.is_rematerializable}
        
        # print("REMAT VRS: " + str(self.remat_VRs))

        # -----------end initialization-----------


        head = self.IR_LIST.head
        line_num = 1

        while (head != None and self.stop_running != True):
            # self.print_allocated_line(head)
            # self.IR_LIST.print_full_line(head)


            # ----- USES --------
            if (head.opcode == LOAD_OP):  # load
                self.allocate_use(STORE_OP, head, head.arg1)    # allocate store
                self.free_use(STORE_OP, head, head.arg1)  # free store
            if (head.opcode >= ADD_OP and head.opcode <= RSHIFT_OP): # arithop
                self.cur_PR = self.allocate_use(STORE_OP, head, head.arg1)   # allocate store
                self.allocate_use(LOADI_OP, head, head.arg2)    # allocate loadI
                self.cur_PR = -1
                self.free_use(STORE_OP, head, head.arg1)  # free store
                self.free_use(LOADI_OP, head, head.arg2)  # free loadi
            if (head.opcode == STORE_OP):  # store
                self.cur_PR = self.allocate_use(STORE_OP, head, head.arg1)   # allocate store
                self.allocate_use(ADD_OP, head, head.arg3)    # allocate add
                self.cur_PR = -1
                self.free_use(STORE_OP, head, head.arg1)  # free store
                self.free_use(ADD_OP, head, head.arg3)  # free add
            
            # ----- DEFS --------
            if (head.arg3[SR_IDX] != None and head.opcode != 1): # sr is not invalid and opcode is not a store
                VR = head.arg3[VR_IDX]
                # get phys reg
                if (len(self.PRStack) > 0):
                    PR = self.PRStack.pop()
                else:
                    PR = self.spill(head)
                # update maps
                head.arg3[PR_IDX] = PR
                self.VRToPR[VR] = PR
                self.PRToVR[PR] = VR
                self.PRNU[PR] = head.arg3[NU_IDX]
            

            # error = self.check_maps(head)
            # if (error == -1):
            #     print("error: " + str(error))

            # self.check_remat(head)

            # iterate
            head = head.next
            line_num += 1

    
    #🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈
    #🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈
    #🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈helpers🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈
    #🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈
    #🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈

    """
        Checks things possibly related to rematerialzaion

    """
    def check_remat(self, head):
        print(str(head.line) + ": opcode: " + self.opcodes_list[head.opcode] + "; IS_SPILLED:")
        print(self.spilled)
        print(str(head.line) + ": opcode: " + self.opcodes_list[head.opcode] + "; VRTOSPILLLOC:")
        print(self.VRToSpillLoc)

   
    def op_defines(self, operand):
        """
            The operation defines the register
        """
        # print("operand: " + str(operand))
        # print("SR_to_VR len: " + str(len(self.SR_to_VR)))
        # print("[op_defines] operand.sr: " + str(operand.sr))
        if (self.SR_to_VR[operand[SR_IDX]] == INVALID):  # Unused DEF
            self.SR_to_VR[operand[SR_IDX]] = self.VR_name
            self.VR_name += 1
        operand[VR_IDX] = self.SR_to_VR[operand[SR_IDX]]
        operand[NU_IDX] = self.LU[operand[SR_IDX]]
        self.SR_to_VR[operand[SR_IDX]] = INVALID # kill OP3
        self.LU[operand[SR_IDX]] = INF
        # update maxlive counter
        self.count_live -= 1
        return operand
  
    def op_uses(self, operand):
        if (self.SR_to_VR[operand[SR_IDX]] == INVALID):  # Last use
            self.SR_to_VR[operand[SR_IDX]] = self.VR_name
            self.VR_name += 1
            # update maxlive counter
            self.count_live += 1
            # if (self.DEBUG):
            #     print("op_uses: " + str(self.count_live))
            if self.count_live > self.max_live:
                # if (self.DEBUG):
                #     print("op_uses: count live greater than max live. assigning count live to max live.")
                self.max_live = self.count_live
        operand[VR_IDX] = self.SR_to_VR[operand[SR_IDX]]
        operand[NU_IDX] = self.LU[operand[SR_IDX]]

    def get_max_vr(self):
        start = self.IR_LIST.head
        max = 0
        while (start != None):
            if (start.arg1[VR_IDX] != None and start.arg1[VR_IDX] > max):
                max = start.arg1[VR_IDX]
            if (start.arg2[VR_IDX] != None and start.arg2[VR_IDX] > max):
                max = start.arg2[VR_IDX]
            if (start.arg3[VR_IDX] != None and start.arg3[VR_IDX] > max):
                max = start.arg3[VR_IDX]
            start = start.next
        return max


    
    def print_renamed_block(self):
        start = self.IR_LIST.head
        while (start != None):
            # print(start)
            lh = ""
            rh = ""
            
            if (start.opcode == 0 or start.opcode == 1): # MEMOP
                lh = "r" + str(start.arg1[VR_IDX])
            elif (start.opcode == 2): # LOADI
                lh = str(start.arg1[SR_IDX])
            elif (start.opcode >= 3 and start.opcode <= 7):  # ARITHOP
                lh = "r" + str(start.arg1[VR_IDX]) + ",r" + str(start.arg2[VR_IDX]) 
            elif (start.opcode == 8): # OUTPUT
                lh = str(start.arg1[SR_IDX])
            
            if (start.opcode != 8):
                rh = "=> r" + str(start.arg3[VR_IDX])

            opcode = opcodes_list[start.opcode] + " "


            print(opcode + lh + " " + rh)

            start = start.next
  
    def print_allocated_line(self, node):
        # load or store
            if (node.opcode == 0 or node.opcode == 1):
                print(f"//{self.opcodes_list[node.opcode] : <7} r{node.arg1[PR_IDX]}  =>   r{node.arg3[PR_IDX]}")
            # loadI
            elif (node.opcode == 2):
                print(f"//{self.opcodes_list[node.opcode] : <7} {node.arg1[SR_IDX]}  =>   r{node.arg3[PR_IDX]}")
            # arithop
            elif (node.opcode >= 3 and node.opcode <= 7):
                print(f"//{self.opcodes_list[node.opcode] : <7} r{node.arg1[PR_IDX]}, r{node.arg2[PR_IDX]}  =>   r{node.arg3[PR_IDX]}")
            # output
            elif (node.opcode == 8):
                print(f"//{self.opcodes_list[node.opcode] : <7} {node.arg1[SR_IDX]}")
            # nop
            elif (node.opcode == 9):
                print(f"//{self.opcodes_list[node.opcode] : <7}")
        

    def check_maps(self, line):
        print("[CHECK_MAPS]")
        # self.print_renamed_block()
        # self.IR_LIST.print_table(self.IR_LIST)
        self.IR_LIST.print_full_line(line)
        # print(line)
        self.print_allocated_line(line)

        print("IS REMATERIALIZABLE:")
        for x in self.is_rematerializable:
            self.IR_LIST.print_full_line(x)
        print("REMAT VRS:")
        print(self.remat_VRs)



        print("VR TO PR:")  # vr is th index, pr is the value
        print(self.VRToPR)
        print("PR STACK:")
        print(self.PRStack)

        # for each vr, v, if vrtopr[v] is defined, prtovr[vrtopr[v]] = v
        print("PR TO VR:")  # pr is the index, vr is the value
        print(self.PRToVR)

        for key, val in self.VRToPR.items():
            if (val in self.PRToVR and self.PRToVR[val] != key):
                print(f"ERROR {line.line}: the pair ({key}, {val}) in self.VRToPR does not match the pair ({val}, {self.PRToVR[val]}) in self.PRToVR")
                return -1
        for key, val in self.PRToVR.items():
            if (val in self.VRToPR and self.VRToPR[val] != key):
                print(f"ERROR {line.line}: the pair ({key}, {val}) in self.PRToVR does not match the pair ({val}, {self.VRToPR[val]}) in self.VRToPR")
                return -1
        if (line.arg1[PR_IDX] != None):
            print("ARG1 LINE " + str(line.line) + ": PR: " + str(line.arg1[PR_IDX]) + " ; PRNU[PR]: " + str(self.PRNU[line.arg1[PR_IDX]]))
        if (line.arg2[PR_IDX] != None):
            print("ARG2 LINE " + str(line.line) + ": PR: " + str(line.arg2[PR_IDX]) + " ; PRNU[PR]: " + str(self.PRNU[line.arg2[PR_IDX]]))
        if (line.arg3[PR_IDX] != None):
            print("ARG3 LINE " + str(line.line) + ": PR: " + str(line.arg3[PR_IDX]) + " ; PRNU[PR]: " + str(self.PRNU[line.arg3[PR_IDX]]))
        
        return 0
    
    #🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈
    #🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈
    #🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈rename🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈
    #🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈
    #🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈

    def rename(self):

        self.SR_to_VR = [INVALID for i in range(self.max_sr_num + 1)] # register numbers start at 0 so must be plus one the max register
        self.LU = [INF for i in range(self.max_sr_num + 1)]



        index = self.IR_LIST.length - 1

        OP = self.IR_LIST.tail
        while (OP != None):  # For each OPCODE (OP) in the block, bottom to top
            # print(OP.opcode)

            # Only want opcodes with registers: MEMOP, LOADI, and ARITHOP
            # registers in each:
            # MEMOP: arg1 and arg3
            # LOADI: arg3
            # ARTIHOP: arg1, arg2, arg3
            # OUTPUT: none, constant only
            if (OP.opcode >= 0 and OP.opcode <= 7):
                #-------------
                # For each Operand (O) that OPCODE (OP) defines- third operand
                # if (OP.arg1.sr != None and OP.opcode != 2): # LOADI stores constant at first sr
                #   OP.arg1 = self.op_defines(OP.arg1)
                # if (OP.arg2.sr != None and OP.opcode != 0 and OP.opcode != 1 and OP.opcode != 2): # only ARITHOPs populate sr2
                #   OP.arg2 = self.op_defines(OP.arg2)
                if (OP.opcode == LOADI_OP):
                    self.is_rematerializable.append(OP)

                
                if (OP.arg3[SR_IDX] != None and OP.opcode != 1):  # all of them populate sr3, store's arg3 is a use, so dont define
                    OP.arg3 = self.op_defines(OP.arg3)
                #-------------
                # For each Operand (O) that OPCODE (OP) uses- first and second operand
                
                if (OP.arg1[SR_IDX] != None and OP.opcode != 2): # LOADI stores constant at first sr
                    self.op_uses(OP.arg1)
                    self.LU[OP.arg1[SR_IDX]] = index
                if (OP.arg2[SR_IDX] != None and OP.opcode != 0 and OP.opcode != 1 and OP.opcode != 2): # only ARITHOPs populate sr2
                    self.op_uses(OP.arg2)
                    self.LU[OP.arg2[SR_IDX]] = index
                if (OP.arg3[SR_IDX] != None and OP.opcode == 1): # third operand is a use for store
                    self.op_uses(OP.arg3)
                    self.LU[OP.arg3[SR_IDX]] = index

            
            index -= 1
            OP = OP.prev

        # self.IR_LIST.print_table(self.IR_LIST)




    # def main(self):
    #     # pr = cProfile.Profile()
    #     # pr.enable() 
    #     # print("LAB2 MAIN")
    #     # arg_len = len(sys.argv)

    #     # if (sys.argv[1] == '-h'):
    #     #         print("\n")
    #     #         print("Command Syntax:")
    #     #         print("     ./412alloc [flag or number of registers] <filename>")
    #     #         print("\n")
    #     #         print("Required arguments:")
    #     #         print("     filename is the pathname (absolute or relative) to the input file. When the flag is '-h', no filename should be specified and nothing after the flag is processed.")
    #     #         print("\n")
    #     #         print("Optional flags:")
    #     #         print("     -h      prints this message")
    #     #         print("\n")
    #     #         print("At most one of the following three flags:")
    #     #         print("     -x      Performs scanning, parsing, renaming on the file and then prints the renamed block to the stdout.")
    #     #         print("     [k]       Where k is the number of registers available to the allocator (3<=k<=64).")
    #     #         print("                     Scan, parse, rename, and allocate code in the input block given in filename so that it uses")
    #     #         print("                     only registers r0 to rk-1 and prints the resulting code in the stdout.")
    #     # else:
    #     #     if (arg_len <= 2):
    #     #         print("Must specify a file name after the flag.")
    #     #     else:
    #     #         # __file__ = sys.argv[2]
            
    #     #         # # open file
    #     #         # try:
    #     #         #     f = open(__file__, 'r')
    #     #         # except FileNotFoundError:  # FileNotFoundError in Python 3
    #     #         #     print(f"ERROR input file not found", file=sys.stderr)
    #     #         #     sys.exit()
    #     #         # Reading a file
    #     #         # f = open(__file__, 'r')
    #     #         # Lab_1 = lab1.Lab1()
    #     #         # Lab_1.main(f, True, False)
    #     #         # ir_list = Lab_1.ir_list
    #     #         # max_reg = Lab_1.max_reg
    #     #         # num_srs = Lab_1.num_srs
    #     #         # f.close()

    #     #         # lab2 = Lab2(ir_list, max_reg, num_srs)

    #     #         self.rename()

    #     #         if (sys.argv[1] == '-x'):
    #     #             self.print_renamed_block()
    #     #         elif (int(sys.argv[1]) >= 3 and int(sys.argv[1]) <= 64):
    #     #             # lab2.allocate(int(sys.argv[1]))
    #     #             self.dif_alloc(int(sys.argv[1]))
    #     #             self.print_allocated_file()
    #             # lab2.IR_LIST.print_table(lab2.IR_LIST)
    #         # pr.disable()
    #         # s = StringIO()
    #         # sortby = 'cumulative'
    #         # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    #         # ps.print_stats()
    #         # sys.stdout.write(s.getvalue())



# if __name__ == "__main__":
#   main()
