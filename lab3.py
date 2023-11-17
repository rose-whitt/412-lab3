import scanner
# from IR_List import *
import lab1
import lab2
import sys
import math
import cProfile, pstats
from io import StringIO
from DP_MAP import *


# KINDS
DATA = 0
SERIAL = 1
CONFLICT = 2


class Lab3:
    """
    
    """
    def __init__(self, IR_LIST):
        self.IR_LIST = IR_LIST
        self.DP_MAP = DependenceGraph()
        self.kinds = ["Data", "Serial", "Conflict"]

    def dummy(self):
        print("WASSUP BITCH")
        start = self.IR_LIST.head
        while (start != None):
            self.DP_MAP.add_node(start)
            start = start.next
        
        self.DP_MAP.print_dot()


    

    


def main():
    # pr = cProfile.Profile()
    # pr.enable() 
    print("in lab3 main")
    print(sys.argv)
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
        Lab_3 = Lab3(Lab_2.IR_LIST)
        Lab_3.dummy()



if __name__ == "__main__":
  main()
