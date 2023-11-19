#!/usr/bin/python -u

import scanner
from IR_List import *
import sys

COMMENT = "// ILOC Front End \n"

SR_IDX = 0
VR_IDX = 1
PR_IDX = 2
NU_IDX = 3

class Lab1:
  def __init__(self):
    # print("LAB1 init")

    self.ir_list = LinkedList()
    self.EOF_FLAG = False
    self.num_srs = 0
    self.max_reg = 0


  def run(self, input_file, flag):
    

    scan = scanner.Scanner(input_file)

    scan.mode_flag = flag
    scan.cur_line = scan.convert_line_to_ascii_list(input_file.readline())
    scan.char_idx = -1

    i = 0

    token = scan.get_token()

    if (flag == '-s'):
      
      while (token[0] != scan.EOF):
        while (token[0] != scan.EOL and token[0] != scan.SCANNER_ERROR):
          i += 1
          token = scan.get_token()
        scan.cur_line = scan.convert_line_to_ascii_list(input_file.readline())
        token = scan.get_token()  
    else:
      while (token[0] != scan.EOF):
        i += 1
        if (token[0] == scan.MEMOP):
          memop_node = Node()
          memop_node.line = scan.line_num
          memop_node.opcode = token[1]

          MEM_OP_FLAG = False
          token = scan.get_token()
          while (token[0] == scan.BLANK):
              token = scan.get_token()
          if (token[0] != scan.REGISTER):
              sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing first REGISTER in MEMOP (load or store); token: ' + str(token[0]) +  ' - [PARSER]\n')
              scan.num_parser_errors += 1
              MEM_OP_FLAG = False
          else:
              memop_node.arg1[SR_IDX] = token[1]  # first register
              if (token[1] > self.max_reg):
                self.max_reg = token[1]

              token = scan.get_token()
              while (token[0] == scan.BLANK):
                  token = scan.get_token()
              if (token[0] != scan.INTO):
                  sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing INTO in MEMOP (load or store); token: ' + str(token[0]) +  ' - [PARSER]\n')
                  scan.num_parser_errors += 1
                  MEM_OP_FLAG = False
              else:
                token = scan.get_token()
                while (token[0] == scan.BLANK):
                    token = scan.get_token()
                if (token[0] != scan.REGISTER): # register in scanner returns self.REGISTER, reg_num
                    sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing target (second) REGISTER in MEMOP (load or store); token: ' + str(token[0]) +  ' - [PARSER]\n')
                    scan.num_parser_errors += 1
                    MEM_OP_FLAG = False
                else:
                    memop_node.arg3[SR_IDX] = token[1]  # second register
                    if (token[1] > self.max_reg):
                      self.max_reg = token[1]
                    token = scan.get_token()
                    while (token[0] == scan.BLANK):
                        token = scan.get_token()
                    if (token[0] == scan.EOL):
                        # build IR
                        self.num_srs += 2

                        self.ir_list.append(memop_node)

                        scan.num_iloc_ops += 1
                        scan.cur_line = scan.convert_line_to_ascii_list(scan.input_file.readline())
                        
                        
                        MEM_OP_FLAG = True
                    elif (token[0] == scan.SCANNER_ERROR):
                        return False
                    else:
                        sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing EOL in MEMOP (load or store); token: ' + str(token[0]) +  ' - [PARSER]\n')
                        scan.num_parser_errors += 1
                        MEM_OP_FLAG =  False
          if (MEM_OP_FLAG == False):  # error on line
            scan.num_error_lines += 1
            scan.cur_line = scan.convert_line_to_ascii_list(scan.input_file.readline())

          scan.char_idx = -1
        elif (token[0] == scan.LOADI):
          loadi_node = Node()
          loadi_node.line = scan.line_num
          loadi_node.opcode = token[1]
          # temp_line = []
          # temp_line.append(token)
          LOADI_FLAG = False
          token = scan.get_token()
          while (token[0] == scan.BLANK):
              token = scan.get_token()
          if (token[0] != scan.CONSTANT):
              sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing CONSTANT in LOADI; token: ' + str(token[0]) +  ' - [PARSER]\n')
              scan.num_parser_errors += 1
              LOADI_FLAG = False
          else:
              loadi_node.arg1[SR_IDX] = token[1]  # first constant
              
              # temp_line.append(token)
              token = scan.get_token()
              while (token[0] == scan.BLANK):
                  token = scan.get_token()
              if (token[0] != scan.INTO):
                  sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing INTO in LOADI; token: ' + str(token[0]) +  ' - [PARSER]\n')
                  scan.num_parser_errors += 1
                  LOADI_FLAG = False
              else:
                  # temp_line.append(token)
                  token = scan.get_token()
                  while (token[0] == scan.BLANK):
                      token = scan.get_token()
                  if (token[0] != scan.REGISTER):
                      sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing REGISTER in LOADI; token: ' + str(token[0]) +  ' - [PARSER]\n')
                      scan.num_parser_errors += 1
                      LOADI_FLAG = False
                  else:
                    loadi_node.arg3[SR_IDX] = token[1]  # second register
                    if (token[1] > self.max_reg):
                      self.max_reg = token[1]
                    # temp_line.append(token)
                    token = scan.get_token()
                    while (token[0] == scan.BLANK):
                        token = scan.get_token()
                    if (token[0] == scan.EOL):
                        # build ir
                        # add_ir_block(scan, scan.line_num, temp_line)
                        # loadi_node = Node()
                        # loadi_node.value[0] = scan.line_num
                        # loadi_node.value[1] = temp_line[0][1]
                        # loadi_node.value[2][0] = temp_line[1][1]  # first register
                        # loadi_node.value[4][0] = temp_line[3][1]  # second register
                        self.num_srs += 2

                        self.ir_list.append(loadi_node)


                        scan.num_iloc_ops += 1
                        # scan.line_num += 1
                        # scan.char_idx = -1
                        scan.cur_line = scan.convert_line_to_ascii_list(scan.input_file.readline())
                        LOADI_FLAG = True
                    elif (token[0] == scan.SCANNER_ERROR):
                        LOADI_FLAG = True
                    else:
                        sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing EOL in LOADI; token: ' + str(token[0]) +  ' - [PARSER]\n')
                        scan.num_parser_errors += 1
                        LOADI_FLAG = False
          if (LOADI_FLAG == False): # error on line
            # scan.line_num += 1
            # scan.char_idx = -1
            scan.num_error_lines += 1
            scan.cur_line = scan.convert_line_to_ascii_list(scan.input_file.readline())
          # else:
          #   print("[PARSE] " + str(scan.line_num - 1) + ": LOADI")
          scan.char_idx = -1
        elif (token[0] == scan.ARITHOP):
          ari_node = Node()
          ari_node.line = scan.line_num
          ari_node.opcode = token[1]
          # temp_line = []
          # temp_line.append(token)
          ARITHOP_FLAG = False
          token = scan.get_token() 

          while (token[0] == scan.BLANK):
              token = scan.get_token()
          if (token[0] != scan.REGISTER):
              sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing first REGISTER in ARITHOP; token: ' + str(token[0]) +  ' - [PARSER]\n')
              scan.num_parser_errors += 1
              ARITHOP_FLAG = False
          else:
              ari_node.arg1[SR_IDX] = token[1]
              if (token[1] > self.max_reg):
                self.max_reg = token[1]
              # temp_line.append(token)
              token = scan.get_token()
              while (token[0] == scan.BLANK):
                  token = scan.get_token()
              if (token[0] != scan.COMMA):
                sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing COMMA in ARITHOP; token: ' + str(token[0]) +  ' - [PARSER]\n')
                scan.num_parser_errors += 1
                ARITHOP_FLAG = False
              else:
                # temp_line.append(token)
                token = scan.get_token()
                while (token[0] == scan.BLANK):
                    token = scan.get_token()
                # ARITHOP REG COMMA 
                if (token[0] != scan.REGISTER):
                    sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing second REGISTER in ARITHOP; token: ' + str(token[0]) +  ' - [PARSER]\n')
                    scan.num_parser_errors += 1
                    ARITHOP_FLAG = False
                else:
                  ari_node.arg2[SR_IDX] = token[1]
                  if (token[1] > self.max_reg):
                    self.max_reg = token[1]
                  # temp_line.append(token)
                  token = scan.get_token()
                  while (token[0] == scan.BLANK):
                      token = scan.get_token()
                  if (token[0] != scan.INTO):
                      sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing INTO in ARITHOP; token: ' + str(token[0]) +  ' - [PARSER]\n')
                      scan.num_parser_errors += 1
                      ARITHOP_FLAG = False
                  else:
                    # temp_line.append(token)
                    token = scan.get_token()
                    while (token[0] == scan.BLANK):
                        token = scan.get_token()
                    if (token[0] != scan.REGISTER):
                        sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing target (third) REGISTER in ARITHOP; token: ' + str(token[0]) +  ' - [PARSER]\n')
                        scan.num_parser_errors += 1
                        ARITHOP_FLAG = False
                    else:
                      ari_node.arg3[SR_IDX] = token[1]
                      if (token[1] > self.max_reg):
                        self.max_reg = token[1]
                      
                      # temp_line.append(token)
                      token = scan.get_token()
                      while (token[0] == scan.BLANK):
                          token = scan.get_token()
                      if (token[0] == scan.EOL):
                          # add_ir_block(scan, scan.line_num, temp_line)
                          # ari_node = Node()
                          # ari_node.value[0] = scan.line_num
                          # ari_node.value[1] = temp_line[0][1]
                          # ari_node.value[2][0] = temp_line[1][1]
                          # ari_node.value[3][0] = temp_line[3][1]
                          # ari_node.value[4][0] = temp_line[5][1]
                          self.num_srs += 3
                          self.ir_list.append(ari_node)

                          scan.num_iloc_ops += 1
                          # scan.line_num += 1
                          # scan.char_idx = -1
                          scan.cur_line = scan.convert_line_to_ascii_list(scan.input_file.readline())
                          ARITHOP_FLAG = True
                      elif (token[0] == scan.SCANNER_ERROR):
                          ARITHOP_FLAG = False
                      else:
                          sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing EOL in ARITHOP; token: ' + str(token[0]) +  ' - [PARSER]\n')
                          scan.num_parser_errors += 1
                          ARITHOP_FLAG = False
        
          if (ARITHOP_FLAG == False):  # error on line
            # scan.line_num += 1
            # scan.char_idx = -1
            scan.num_error_lines += 1
            scan.cur_line = scan.convert_line_to_ascii_list(scan.input_file.readline())
          # else:
          #   print("[PARSE] " + str(scan.line_num - 1) + ": ARITHOP")
          scan.char_idx = -1
        elif (token[0] == scan.OUTPUT):
          output_node = Node()
          output_node.line = scan.line_num
          output_node.opcode = token[1]
          # temp_line = []
          # temp_line.append(token)
          OUTPUT_FLAG = False
          token = scan.get_token()
          while (token[0] == scan.BLANK):
              token = scan.get_token()
          if (token[0] != scan.CONSTANT):
              sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing CONSTANT in OUTPUT; token: ' + str(token[0]) +  ' - [PARSER]\n')
              scan.num_parser_errors += 1
              OUTPUT_FLAG = False
          else:
            # temp_line.append(token)
            output_node.arg1[SR_IDX] = token[1]

            token = scan.get_token()
            while (token[0] == scan.BLANK):
                token = scan.get_token()
            if (token[0] == scan.EOL):
                # add_ir_block(scan, scan.line_num, temp_line)
                # output_node = Node()

                # output_node.value[0] = scan.line_num
                # output_node.value[1] = temp_line[0][1]
                # output_node.value[2][0] = temp_line[1][1]
                self.num_srs += 1

                self.ir_list.append(output_node)

                scan.num_iloc_ops += 1
                # scan.line_num += 1
                # scan.char_idx = -1
                scan.cur_line = scan.convert_line_to_ascii_list(scan.input_file.readline())
                OUTPUT_FLAG = True
            elif (token[0] == scan.SCANNER_ERROR):
                OUTPUT_FLAG = False
            else:   # NOTE: i think that i should add a case to see if its a scanner error so then i woudlnt print it out, and if its soemthing else, then print out the char
                sys.stderr.write("ERROR " + str(scan.line_num) + ':               Missing EOL in OUTPUT; token: ' + str(token[0]) +  ' - [PARSER]\n')
                scan.num_parser_errors += 1
                OUTPUT_FLAG = False
          if (OUTPUT_FLAG == False):  # error on line
            scan.num_error_lines += 1
            scan.cur_line = scan.convert_line_to_ascii_list(scan.input_file.readline())
          scan.char_idx = -1
        elif (token[0] == scan.NOP):
          NOP_FLAG = False
          token = scan.get_token()
          while (token[0] == scan.BLANK):
              token = scan.get_token()
          if (token[0] == scan.SCANNER_ERROR):
              NOP_FLAG = False
          elif (token[0] != scan.EOL and token[0] != scan.EOF):
              sys.stderr.write("ERROR " + str(scan.line_num) + ':               wrong thing after NOP; token: ' + str(token[0]) +  ' - [PARSER]\n')
              scan.num_parser_errors += 1
              NOP_FLAG = False
          else:
              scan.num_iloc_ops += 1
              # scan.line_num += 1
              # scan.char_idx = -1
              scan.cur_line = scan.convert_line_to_ascii_list(scan.input_file.readline())
              NOP_FLAG = True
          if (NOP_FLAG == False): # error on line
            scan.num_error_lines += 1
            scan.cur_line = scan.convert_line_to_ascii_list(scan.input_file.readline())
          scan.char_idx = -1
        elif (token[0] == scan.EOL):
          scan.cur_line = scan.convert_line_to_ascii_list(scan.input_file.readline())
        elif (token[0] == scan.BLANK):
          token = scan.get_token()
          continue
        elif (token[0] == scan.SCANNER_ERROR):  # dont continue to parse if scanner error
          scan.num_error_lines += 1
          scan.cur_line = scan.convert_line_to_ascii_list(scan.input_file.readline())
        else:
          sys.stderr.write("ERROR " + str(scan.line_num - 1) + ": no OPCODE - [PARSER]\n")
          # scan.line_num += 1
          # scan.char_idx = -1
          scan.cur_line = scan.convert_line_to_ascii_list(scan.input_file.readline())
        token = scan.get_token()
      
      # print(str(len(scan.OPS)) + " valid ILOC operations: " + str(scan.OPS))
      # if ((scan.num_parser_errors + scan.num_scanner_errors) == 0):
      #   print("//Parse succeeded, finding " + str(scan.num_iloc_ops) + " ILOC operations.")
      # else:
      #   sys.stderr.write("Found " + str(scan.num_parser_errors + scan.num_scanner_errors) + " errors on " + str(scan.num_error_lines) + " lines\n")
      
      if ((scan.num_parser_errors + scan.num_scanner_errors) != 0):
        sys.stderr.write("Found " + str(scan.num_parser_errors + scan.num_scanner_errors) + " errors on " + str(scan.num_error_lines) + " lines\n")
         

      
        
      # print(str(scan.num_iloc_ops) + " valid ILOC operations")
    #   print(str(scan.num_parser_errors) + " parser errors.")
    # print(str(scan.num_scanner_errors) + " scanner errors.")
    
    


  def main(self, file, LAB2_FLAG, PRINT_BEFORE):
    """
    - LAB2_FLAG: true if we are wanting to run lab2 flag
    - PRINT_BEFORE: true if we want to print the IR representation before renaming, for debugging
    """

    # call scan function  
    #   make scanner object by calling class with input fileand then my start scanning func in scanner.py
    #   while not the end of the license
    #     the if statements


    # print("LAB1 MAIN")
    
       

    #read()
    # text = f.read(10)
    i = 1
    # print("POO POOO POO")

    arg_len = len(sys.argv)

    # SHOULD AUTOMATICALLY DO -R FLAG FUNCTIONALITY
    self.run(file, '-r')


    # if (LAB2_FLAG):
    #   if (arg_len <= 2):
    #     print("Must specify a file name after the flag.")
    #   else:
    #     __file__ = sys.argv[2]
      
    #   # open file
    #     try:
    #         f = open(__file__, 'r')
    #     except FileNotFoundError:  # FileNotFoundError in Python 3
    #         print(f"ERROR input file not found", file=sys.stderr)
    #         sys.exit()
    #     # Reading a file
    #     # f = open(__file__, 'r')

    #     self.run(f, '-r')
    #     # self.ir_list.print_list()


    #     f.close()
    # else:
    #   if (sys.argv[1] == '-h'):
    #     print("\n")
    #     print("Command Syntax:")
    #     print("     ./412fe [flags] filename")
    #     print("\n")
    #     print("Required arguments:")
    #     print("     filename is the pathname (absolute or relative) to the input file. When the flag is '-h', no filename should be specified and nothing after the flag is processed.")
    #     print("\n")
    #     print("Optional flags:")
    #     print("     -h      prints this message")
    #     print("\n")
    #     print("At most one of the following three flags:")
    #     print("     -s      prints tokens in token stream, only invokes scanner")
    #     print("     -p      invokes parser and resports on success or failure, invokes scanner and parser")
    #     print("     -r      prints the human readable version of parser's IR")
    #     print("If none is specified, the default action is '-p'.")
        
    #   elif (sys.argv[1] == '-r'):
    #     # print("TODO: read the file, parse it, build the intermediate representation (IR), and print out the information in the intermediate representaiton (in an appropriately human readable format)")
    #     if (arg_len <= 2):
    #       print("Must specify a file name after the flag.")
    #     else:
    #       __file__ = sys.argv[2]

    #       # open file
    #       try:
    #           f = open(__file__, 'r')
    #       except FileNotFoundError:  # FileNotFoundError in Python 3
    #           print(f"ERROR input file not found", file=sys.stderr)
    #           sys.exit()
    #       # Reading a file
    #       # f = open(__file__, 'r')

    #       self.run(f, '-r')
    #       self.ir_list.print_list()
    #       f.close()
    #   elif (sys.argv[1] == '-p'):
    #     # print("TODO: read the file, scan it and parse it, build the intermediate representation (IR) and report either success or report all the errors that it finds in the input file.")
    #     if (arg_len <= 2):
    #       print("Must specify a file name after the flag.")
    #     else:
    #       __file__ = sys.argv[2]

    #       # open file
    #       try:
    #           f = open(__file__, 'r')
    #       except FileNotFoundError:  # FileNotFoundError in Python 3
    #           print(f"ERROR input file not found", file=sys.stderr)
    #           sys.exit()

    #       # __file__ = sys.argv[2]
    #       # Reading a file
    #       # f = open(__file__, 'r')
    #       # start(f, '-p')
    #       self.run(f, '-p')
    #       f.close()
    #   elif (sys.argv[1] == '-s'):
    #     # print("TODO: read file and print to stdout a list of tokens that the scanner found. for each, print line number, tokens type (or syntactic category) and its spelling (or lexeme)")
    #     if (arg_len <= 2):
    #       print("Must specify a file name after the flag.")
    #     else:

    #       __file__ = sys.argv[2]

    #       # open file
    #       try:
    #           f = open(__file__, 'r')
    #       except FileNotFoundError:  # FileNotFoundError in Python 3
    #           print(f"ERROR input file not found", file=sys.stderr)
    #           sys.exit()
    #       # __file__ = sys.argv[2]
    #       # # Reading a file
    #       # poo = 0
    #       # f = open(__file__, 'r')
    #       self.run(f, '-s')
    #       # while (token != ["ENDFILE", ""]): # NOTE: should i read the line by line here?
    #       #   scan_func(f)
    #       #   poo += 1
    #       f.close()
    #   elif (int(sys.argv[1]) >= 3 and int(sys.argv[1]) <= 64):
    #     if (arg_len <= 2):
    #       print("Must specify a file name after k.")
    #     else:
    #       __file__ = sys.argv[2]

    #       # open file
    #       try:
    #           f = open(__file__, 'r')
    #       except FileNotFoundError:  # FileNotFoundError in Python 3
    #           print(f"ERROR input file not found", file=sys.stderr)
    #           sys.exit()
    #       # __file__ = sys.argv[2]
    #       # # Reading a file
    #       # poo = 0
    #       # f = open(__file__, 'r')
    #       self.run(f, '-p')
    #       # while (token != ["ENDFILE", ""]): # NOTE: should i read the line by line here?
    #       #   scan_func(f)
    #       #   poo += 1
    #       f.close()
        
    #   else: # p is default if no flag
    #     if (LAB2_FLAG):
    #       if (sys.argv[1] == '-x'):
    #         __file__ = sys.argv[2]
    #         print('//' + str(__file__))
            
    #     else:
    #       __file__ = sys.argv[1]  # no flag, so second arg should be a filename
    #       print('//' + str(__file__))

    #     # open file
    #     try:
    #         __file__ = sys.argv[1]
    #         f = open(__file__, 'r')
    #     except FileNotFoundError:  # FileNotFoundError in Python 3
    #         print(f"ERROR input file not found", file=sys.stderr)
    #         sys.exit()
    #     # __file__ = sys.argv[2]
    #     # Reading a file
    #     # f = open(__file__, 'r')
    #     # start(f, '-p')
    #     self.run(f, '-p')
    #     if (PRINT_BEFORE):
    #         self.ir_list.print_list()
          
    #     f.close()





# if __name__ == "__main__":
#   main()