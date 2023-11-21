#!/usr/bin/python

import os, time, calendar, datetime, sys
from datetime import datetime

from changeto_testlocation import change_to_test_location, locate_exe, get_language
from get_id import get_id
import operator

#
# Code to take timing measurements on the lab submission, using the 
# SLOCs test set
#
# Runs each submission three times.
#
#


#
# Configuration parameters
#

# base_name contains the path to the directory where this file tree is installed
# It should be one level above the directory that holds this code.

base_name = "/storage-home/r/rew9/comp412/412-lab3/"
#base_name = "/clear/courses/comp412/CodeBase/Lab3/2023-L3AG/l3ag/"

# Locations for test blocks (blocks) and timing blocks (timing)
# These are relative to the directory in base_name

timing_dir = "auto_time/timing_blocks/"

timeout_val = 60.0 # Maximum number of seconds that any run should be allowed
repetitions = 5    # trials at each size

def check_file_type(type):
    for cdir, dirs, files in os.walk('./'):
        for file in files:
            if type in file:
                return True
    return False

def run_timing_block(block_name):
    global kill_switch

    path = base_name + timing_dir

    command_line = "timeout "+str(timeout_val)+"s ./schedule "+path+block_name+" >&/dev/null"
    #print("command line: ", command_line)
    
    start_tic = datetime.now()
    os.system(command_line)
    stop_tic  = datetime.now()
    elapsed = stop_tic - start_tic
    ms = (elapsed.days * 86400 + elapsed.seconds) * 1000 + elapsed.microseconds / 1000.0

    if (ms/1000) >= timeout_val:
        kill_switch = 1
    return ms
        
def run_test(submission):
    global scaling
    global t_names
    global t_sizes
    global kill_switch

    scaling = ""

    # have already found and built the executable
    #record name and netid in result file
    result_file.write(current_id + '\t' + current_name)

    # Scalability testing
    scales = 0
    print("Testing Scalability:\n")

    t_times =  [1000000, 1000000, 1000000, 1000000,  1000000,  1000000,  1000000,  1000000]

    kill_switch = 0

    for i in range(0,repetitions):
        n = 7
        if kill_switch > 0:
            print("\n--> Scheduler exceeded timeout value\n")
            break # stop running the iterative trials that improve accuracy
        while n > -1:
            ms = run_timing_block(t_names[n])
            if ms < t_times[n]:
                t_times[n] = ms
            n = n -1

    for i in range(0,8):
        print("\t"+t_names[i]+":  \t"+str(t_times[i]/1000)[0:6]+" seconds")
        result_file.write("\t"+str(t_times[i]/1000)[0:6])

    # analyze scaling
    linear_ct = 0
    noninc_ct = 0
    quad_ct   = 0
    for i in range(0,7):
        ratio = t_times[i+1]/t_times[i]
        if ratio < 1:
            noninc_ct +=1
        if ratio < 2.3:
            linear_ct += 1
        elif ratio > 3.6:
            quad_ct += 1
        else:
           noninc_ct += 1

    if noninc_ct == 0:
        scaling += " linear"
        scale_points = 100
    elif noninc_ct == 1:
        scaling += " linear (1 jump)"
        scale_points = 100
    elif quad_ct > 2:
        scaling = " quadratic"
        scale_points = 0
    else:
        scaling = " unusual"
        scale_points = 0

    # analyze efficiency
    time = t_times[7] / 1000
    language = get_language()

    if language.find("python") > -1:
        if time <= 10.0:
            eff_points = 100
        elif time > 20.0:
            eff_points = 0
        else:
            eff_points = 100 - (time - 10.0) / 0.1   # 0.1 is (20 - 10) /100

    elif language.find("java") > -1:
        if time <= 2.75:
            eff_points = 100
        elif time > 10.0:
            eff_points = 0
        else:
            eff_points = 100 - (time - 2.75) / 0.0725  # 0.0725 is (10 - 2.75) / 100

    elif language.find("c++") > -1:
        if time <= 2.0:
            eff_points = 100
        elif time > 4.0:
            eff_points = 0
        else:
            eff_points = 100 - (time - 2.0) / 0.02  # 0.02 is (4 - 2) / 100

    elif language.find("c") > -1:
        if time <= 1.5:
            eff_points = 100
        elif time > 3.0:
            eff_points = 0
        else:
            eff_points = 100 - (time - 1.5) / 0.015  # 0.015 is (3 - 1.5) / 100

    else:  # others are all 1 sec and 2 sec
        eff_points = -1  # will require manual intervention
  
    print("\nScaling score is "+str(scale_points))
    print("Efficiency score is "+str(eff_points)+"\t("+language+", "+str(time)+")")

    # record scaling and efficiency points in results file
    if noninc_ct > 0:
        scaling += " (?)"
        print("\n\tAnomalous behavior: "+str(noninc_ct)+" inputs showed no growth")
        result_file.write("\t"+language+"\t"+scaling+"\t"+str(scale_points)+"\t"+str(eff_points)+"\t*\n")
    else:
        result_file.write("\t"+language+"\t"+scaling+"\t"+str(scale_points)+"\t"+str(eff_points)+"\n")
    
    return 0


def main():
    global root
    global tests
    global base_name
    global current_name
    global current_id
    global result_file
    global failed_file
    global scaling
    global t_names, t_times
    

    root = os.getcwd()

    #for each submission:
    #1. make a tmp dir
    #2. cp the tar ball to the dir
    #3. extract and the tar ball
    #4. locate the makefile or the executable
    #5. ready to run with the executable

    print('Autotimer: using Scalability SLOCs blocks')
    print(str(repetitions)+" trials at each block size")

    # set up the output files
    if not os.path.isdir(base_name):
        print('\nNeed to set "base_name" in auto_time/auto_time.py\n\n')
        exit(-1)

    result_path = base_name + 'results/'

    result_file = open(result_path + 'timer-results.txt','w')
    failed_file = open(result_path + 'timer-failed.txt','w')

    # write file headers
    result_file.write('NetId\tName\tT1k\tT2k\tT4k\tT8k\tT16k\tT32k\tT64k\tT128k\tLang.\tScaling Pts\tEff Pts %\n')
    failed_file.write('Name\tNetId\n')

    print('=======================================================================')

    t_names =  ["T001k.i","T002k.i","T004k.i","T008k.i","T016k.i","T032k.i","T064k.i","T128k.i"]
    t_sizes =  [1, 2, 4, 8, 16, 32, 64, 128]

    for submission in sorted(os.listdir('./')):
        if os.path.isdir(submission):
            continue

        print('Testing submission: ' + submission)
        submission_date = change_to_test_location(submission)
                
        current_name, current_id = get_id()
        if current_id == "":
            current_id   = submission.split('.', 1)[0]
            current_name = current_id

        print('NetId: ' + current_id + '\tName: ' + current_name)
        
        if not locate_exe(submission) == -1:
            dummy = run_test(submission)
        else:
            print('submission failed to build correctly')
            print('likely a problem with tar file, make file, or script')
            failed_file.write(current_name + '\t' + current_id+"\n")

        print('\nfinished timing run on submission ' + submission)
        print('=======================================================================')

        #clean up everything that was created during testing
        os.chdir(root)
        fixed_submission = submission.replace(" ", "\ ").replace("(", "\(").replace(")", "\)").replace("'", "\\'")
        folder = submission.split('.', 1)[0]
        fixed_folder = fixed_submission.split('.', 1)[0]
        os.system('rm -rf ' + fixed_folder)


    # close the grading files
    result_file.close()
    failed_file.close()

    print('\nTiming run complete.')
    exit(0)
    
if __name__ == "__main__":
    main()
