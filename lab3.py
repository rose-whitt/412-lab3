import scanner
from IR_List import *
import lab1
import lab2
import sys
import math
import cProfile, pstats
from io import StringIO

class Lab3:
    """
    
        is_rematerializable: list of loadI nodes that are rematerializable 
    """
    def __init__(self):

        print("HELLO!")
        self.Lab_2 = lab2.Lab2()
        self.Lab_2.main()

def main():
    # pr = cProfile.Profile()
    # pr.enable() 
    print("in lab3 main")
    print(sys.argv)
    if (sys.argv[1] == '-h'):
        print("TODO: MAKE HELP FLAG!")
    else:
        lab3 = Lab3()
    # if (sys.argv[1] == '-h'):
    #     print("\n")
    #     print("Command Syntax:")
    #     print("     ./412alloc [flag or number of registers] <filename>")
    #     print("\n")
    #     print("Required arguments:")
    #     print("     filename is the pathname (absolute or relative) to the input file. When the flag is '-h', no filename should be specified and nothing after the flag is processed.")
    #     print("\n")
    #     print("Optional flags:")
    #     print("     -h      prints this message")
    #     print("\n")
    #     print("At most one of the following three flags:")
    #     print("     -x      Performs scanning, parsing, renaming on the file and then prints the renamed block to the stdout.")
    #     print("     [k]       Where k is the number of registers available to the allocator (3<=k<=64).")
    #     print("                     Scan, parse, rename, and allocate code in the input block given in filename so that it uses")
    #     print("                     only registers r0 to rk-1 and prints the resulting code in the stdout.")


    # elif (sys.argv[1] == '-x'):
    #     lab2.print_renamed_block()
    # elif (int(sys.argv[1]) >= 3 and int(sys.argv[1]) <= 64):
    #     # lab2.allocate(int(sys.argv[1]))
    #     lab2.dif_alloc(int(sys.argv[1]))
    #     lab2.print_allocated_file()
        # lab2.IR_LIST.print_table(lab2.IR_LIST)
    # pr.disable()
    # s = StringIO()
    # sortby = 'cumulative'
    # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    # ps.print_stats()
    # sys.stdout.write(s.getvalue())



if __name__ == "__main__":
  main()
