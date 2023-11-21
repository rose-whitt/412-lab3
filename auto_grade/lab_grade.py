#!/usr/bin/python

import os

def check_output(alloc_output, correct_output):
    fa = open(alloc_output, 'r')
    fc = open(correct_output, 'r')
    line_a = ""
    line_c = ""
    is_bad = False
    while True:
        line_c = fc.readline()
        line_a = fa.readline()
	#print(line_c)
	#print(line_a)
        if 'cycle' in line_c:
            break
        if line_a == "":
            is_bad = True
            break
        if not line_a == line_c:
            is_bad = True
            break

    fa.close()
    fc.close()
    big_number = '100000'
    if is_bad == True:
        return big_number

    if not 'cycle' in line_a:
        return big_number

    return line_a.rsplit(' ', 1)[0].rsplit(' ', 1)[1]

#return number of cycles after allocation and checking the outputs
def lab_grade(test_file, sim):
    #get input for simulator
    os.system('cp ' + test_file + ' ./')
    file = test_file.rsplit('/', 1)[1]
    f = open(file, 'r')
    input = ""
    output = []

    while True:
        line = f.readline().strip()
        if line == "":
            break
        if '//SIM INPUT:' in line:
            input = line.split(':')[1]
            break

    f.close()

    # get result without scheduling
    correct_output = 'correct_output'
    os.system(sim + ' -s 3 ' + input + ' < ' + file + ' > ' + correct_output)

    # compare output with scheduling to result without scheduling
    # if same outputs, return number of cycles
    # if not same, return -1
    alloc_output = 'output'
    os.system('chmod +x schedule')
    #print('checking ' + file)
    test_string = 'timeout 120s ./schedule ' + file + ' | ' + sim + ' -s 1 ' + input + ' > ' + alloc_output
    #print(test_string)
    os.system(test_string)
    cycles = check_output(alloc_output, correct_output) # outup comparison
    #os.system('rm ' + alloc_output)

    #os.system('rm ' + correct_output)
    return cycles
