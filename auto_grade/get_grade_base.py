#!/usr/bin/python

import time, datetime, os
from get_id import get_id

def change_to_test_location(submission):
    #in case of "frag1 frag2 (frag3) frag4's"
    fixed_submission = submission.replace(" ", "\ ").replace("(", "\(").replace(")", "\)").replace("'", "\\'")
    folder = submission.split('.', 1)[0]
    fixed_folder = fixed_submission.split('.', 1)[0]

    # if folder exists, remove it to restart what we are doing
    if os.path.exists(folder):
        cmd = 'rm ' + fixed_folder + ' -rf'
        os.system(cmd)

    # make dir and cp
    os.makedirs(folder)
    cmd = 'cp ' + fixed_submission + ' ' + fixed_folder
    os.system(cmd)

    # change dir
    os.chdir(folder)

    # unzip or untar
    if '.zip' in fixed_submission:
        cmd = 'unzip ./' + fixed_submission + ' > /dev/null'
    if '.tar' in fixed_submission:
        if 'tar.gz' in fixed_submission:
            cmd = 'tar xfvz ./' + fixed_submission + ' > /dev/null'
        elif 'tar.bz' in fixed_submission:
            cmd = 'tar xfv ./' + fixed_submission + ' > /dev/null'
        else:
            cmd = 'tar xfv ./' + fixed_submission + ' > /dev/null'
    elif './tgz' in fixed_submission:
        
        cmd = 'tar xfv ./' + fixed_submission + ' > /dev/null'
    os.system(cmd)

    # rm the copied tar ball
    cmd = 'rm ' + fixed_submission
    os.system(cmd)
    dirs = os.listdir('./')
    if len(dirs) == 1 and os.path.isdir(dirs[0]):
        os.chdir(dirs[0])

