# COMP 412, Lab3 autograder

import os, time, calendar, datetime, sys
from changeto_testlocation import change_to_test_location, locate_exe
from lab_grade import lab_grade
from get_id import get_id
import operator

## CONFIGURATION SETTINGS
## 
base_name = "/storage-home/r/rew9/comp412/412-lab3/"
#base_name = "/clear/courses/comp412/CodeBase/Lab3/2023-L3AG/l3ag/"

def test_dir():
    return [ base_name + "auto_grade/blocks/" ]

def check_file_type(type):
    for cdir, dirs, files in os.walk('./'):
        for file in files:
            if type in file:
                return True
    return False

def run_test(submission):
    global ref_results

    dirs = test_dir()
    sim = '/clear/courses/comp412/students/lab3/sim'

    print("File\t\tLab\tRef\tDifference")
    print("------------------------------------------")
    result = {}
    for dir in dirs:
        for test in sorted(os.listdir(dir)):
            if not '.i' in test:
                continue

            result[test] = lab_grade(dir+test, sim)
            diff = str(int(result[test]) - int(ref_results[test]))
            if len(test) < 8:
                print(test+"\t\t"+result[test]+"\t"+ref_results[test]+"\t"+diff)
            else:
                print(test+"\t"+result[test]+"\t"+ref_results[test]+"\t"+diff)

    print("")
    return result

def get_input(file):
    f = open(file, 'r')
    input = ""
    while True:
        line = f.readline()
        if line == "":
            break
        if 'SIM INPUT' in line:
            input = line.split(':')[1]
            break
    return input.strip()

def get_ref_cycles():
    lab3_ref = '/clear/courses/comp412/students/lab3/lab3_ref'
    lab3_sim = '/clear/courses/comp412/students/lab3/sim'
    dirs = test_dir()
    results = {}
    for dir in dirs:
        for test in sorted(os.listdir(dir)):
            test_file = dir+test
            input = get_input(test_file)
            cmd = lab3_ref + ' ' + test_file + ' | ' + lab3_sim + ' -s 1 ' + input + ' | grep cycles > out'
            #print(cmd)
            os.system(lab3_ref + ' ' + test_file + ' | ' + lab3_sim + ' -s 1 ' + input + ' | grep cycles > out')
            f = open('out', 'r')
            line = f.readline()
            f.close()
            results[test] = line.rsplit(' ', 2)[1]
    os.system('rm -rf out')
    return results

# This version computes the sum of the reference implementation's cycle counts,
# the sum of the student lab's adjusted cycle counts ( > 2x ref becomes ref ),
# and computes a % distance from 100% of lab3_ref's counts.
def sum_result(result,ref_result):
    dirs = test_dir()
    sum = 0
    ref_sum = 0
    for dir in dirs:
        for test in os.listdir(dir):
            ref_cycles = int(ref_result[test])
            ref_sum = ref_sum + ref_cycles
            upper_bound = 2 * ref_cycles
            student_cycles = int(result[test])
            if student_cycles > upper_bound:
                student_cycles = upper_bound
            if student_cycles == 0:
                student_cycles = upper_bound
            sum = sum + student_cycles

    return 1.0 - float(sum - ref_sum) / float(ref_sum)
    
def check_correctness(result):
    dirs = test_dir()
    total_test = 0
    for dir in dirs:
        for item in os.listdir(dir):
            total_test = total_test + 1

    correct_count = total_test
    for test in result.keys():
        if result[test] == '100000':
            correct_count = correct_count - 1

    return 1.0 * correct_count / total_test

def main():
    global root
    global tests
    global ref_results

    root = os.getcwd()

    #for each submission:
    #1. make a tmp dir
    #2. cp the tar ball to the dir
    #3. extract and the tar ball
    #4. locate the makefile or the executable
    #5. ready to run with the executable

    result = {}

    names = {}
    failed = []

    print("COMP 412, Lab3, Autograder")
    print("--------------------------")
    print("\nThe Lab 3 autograder no longer measures running time.")
    print("Use the autotimer instead. It provides more accurate results.\n")
    print("Correcness and Effectiveness results are printed at the")
    print("bottom of the log. Effectiveness of > 0.90 is full credit.\n")

    if not os.path.isdir(base_name):
        print('\nNeed to set "base_name" in auto_grade/auto_grade.py\n\n')
        exit(-1)

    print('... Gathering cycle counts from lab3_ref ...')
    ref_results = get_ref_cycles()
    print(" ")

    for submission in os.listdir('./'):
        result_temp = {}
        if os.path.isdir(submission):
            continue

        change_to_test_location(submission)
        print('========', 'testing', submission, '========')
        name, id = get_id()
        if id == "":
            id = submission.split('.', 1)[0]
            name = id
        names[id] = name

        print("Name: "+name+"\tNetID: "+id)

        if not locate_exe(submission) == -1:
            result[id] = run_test(submission)
        else:
            failed.append(id)
            print('\nSubmission failed <---\n')

        print('=======', 'finished', submission, '=======\n')


        #clean up everything that was created during testing
        os.chdir(root)
        fixed_submission = submission.replace(" ", "\ ").replace("(", "\(").replace(")", "\)").replace("'", "\\'")
        folder = submission.split('.', 1)[0]
        fixed_folder = fixed_submission.split('.', 1)[0]
        os.system('rm ' + fixed_folder + ' -rf')

    #print out the result
    sorted_id = sorted(result.keys(), key=lambda s: s.lower())
    dirs = test_dir()
    result_dir = base_name + "results/"
    result_file = open(result_dir + 'cycles.txt', 'w')

    result_file.write('Shows cycle counts for student lab by each test file\n')
    result_file.write('Need a wide window ...\n\n')
    result_file.write('Name\tNetID')

    for dir in dirs:
        for test in sorted(os.listdir(dir)):
           result_file.write('\t' + test) 
    result_file.write('\n')

    for id in sorted_id:
        if id in names.keys():
            result_file.write(names[id] + '\t' + id)
        for dir in dirs:
            for test in sorted(os.listdir(dir)):
                result_file.write('\t' + result[id][test])
        result_file.write('\n')
    result_file.close()

    points = {}

    print('\nCorrectness results:\t(sorted NetID order)')

    correctness = open(result_dir+'correct.txt', 'w')
    correctness.write('Shows % of correctness points\n\n')
    correctness.write('Name\tNetID\tCorrectness Score\n')
    for id in sorted_id:
        points[id] = sum_result(result[id],ref_results)
        correct_int = check_correctness(result[id])
        if correct_int == 0:
            failed.append(id)
        correctness.write(names[id] + '\t' + id + '\t' + str(correct_int) + '\n')
        print('\t',names[id],'\t',id,'\t',correct_int)
    correctness.close()

    print('\nEffectiveness Results:\t(sorted point order)')

    point_file = open(result_dir+'points.txt', 'w')
    point_file.write('Shows % of efficiencty points\n')
    point_file.write('Calculated from 110% of lab3_ref\n\n')
    point_file.write('name\tnetid\tpoints\n')
    sort_points = sorted(points.items(), key=operator.itemgetter(1))
    for p in sort_points:
        # cap effectiveness points at 1.0 
        val = min(p[1],1.0)
        point_file.write(names[p[0]] + '\t' + p[0] + '\t' + str(val) + '\n')
        print('\t',names[p[0]], '\t', p[0], '\t', str(val)[0:5])
    point_file.close()

    print(" ")

    failed_file = open(result_dir+'failed'+ '.txt', 'w')
    failed_file.write('Shows NetIDs of labs that failed to get any correctness points\n\n')
    for id in failed:
        failed_file.write(id+ '\n')
    failed_file.close()
            

if __name__ == "__main__":
    main()
