import argparse
import sys
import os
import logging
import random
import time
import datetime
import yaml
import pandas as pd

from furhat import connect_to_iristk

FURHAT_AGENT_NAME = 'system'
FURHAT_IP = '130.237.47.50'

furhat_gestures_list = ['BigSmile', 'Smile',
                         'Blink', 'Wink',
                         'BrowFrown', 'BrowRaise',
                         'CloseEyes', 'OpenEyes', 'GazeAway',
                         'ExpressAnger', 'ExpressDisgust', 'ExpressFear', 'ExpressSad',
                         'Nod', 'Oh', 'Roll', 'Shake',
                         'Surprise', 'Thoughtful']

def furhat_say(utterance):
    with connect_to_iristk(FURHAT_IP,debug=False) as furhat_client:
        furhat_client.say(FURHAT_AGENT_NAME,utterance)

def furhat_attend(direction):
    global attend
    center_location = {'x': 0, 'y': 0, 'z': 2}
    left_location = {'x':0.6,'y':0,'z':2}
    right_location = {'x':-0.6,'y':0,'z':2}

    with connect_to_iristk(FURHAT_IP) as furhat_client:
        if direction == 'center':
            furhat_client.gaze(FURHAT_AGENT_NAME, location=center_location)
            attend = 'center'
        elif direction == 'left':
            furhat_client.gaze(FURHAT_AGENT_NAME,location=left_location)
            attend = 'left'
        elif direction == 'right':
            furhat_client.gaze(FURHAT_AGENT_NAME,location=right_location)
            attend = 'right'

        elif direction == 'return':
            if attend == 'right':
                furhat_attend('left')
            elif attend == 'left':
                furhat_attend('right')
            elif attend == 'center':
                furhat_attend(random.choice(['left', 'right']))

def furhat_gesture(gesture):
    with connect_to_iristk(FURHAT_IP,debug=False) as furhat_client:
        furhat_client.gesture(FURHAT_AGENT_NAME, gesture)

def furhat_face(face):
    print("-------------", face)

    with connect_to_iristk(FURHAT_IP,debug=False) as furhat_client:
        furhat_client.set_face(FURHAT_AGENT_NAME, face)

def play_action(scrip_state):
    if scrip_state['utterance'] != None:
        furhat_say(scrip_state['utterance'])
    if scrip_state['face'] != None:
        furhat_face(scrip_state['face'])
    if scrip_state['expression'] != None:
        furhat_gesture(scrip_state['expression'])

    if scrip_state['attend'] != None:
        if scrip_state['attend'] == 'left-right':
            furhat_attend('left')
            time.sleep(0.8)
            furhat_attend('return')
        elif scrip_state['attend'] == 'right-left':
            furhat_attend('right')
            time.sleep(0.8)
            furhat_attend('return')
        else:
            furhat_attend(scrip_state['attend'])


def process_row(row):

    voice = 'Elin'
    
    utte = row['Utterance']
    utt = utte.split("FH: ")[1]

    if voice == 'Astrid':
        utt = "<speak>{}</speak>".format(utt)
        utt = utt.replace('<es>', '<emphasis level="weak">')
        utt = utt.replace('<ee>', '</emphasis>')
        utt = utt.replace('<vs>', '') #  r'"\"vct=70"\" Då tar vi det från början.', 
        utt = utt.replace('<ve>', '') # r'"\"vct=100"\" I Tvåan väljer man inrikt
    elif voice == "Elin":
        utt = utt.replace('<es>', '')
        utt = utt.replace('<ee>', '')
        # utt = utt.replace('<vs>', '"\"vct=70"\"') #  r'"\"vct=70"\" Då tar vi det från början.', 
        # utt = utt.replace('<ve>', '"\"vct=100"\"') # r'"\"vct=100"\" I Tvåan väljer man inrikt


    att = row['Attention']
    exp = row['Expression']
    fac = row['Face']
    return utt, att, exp, fac


def read_script(scrip_path):
    df = pd.read_csv(scrip_path, header=0)
    script_dict = dict()
    for index, row in df.iterrows():
        utt, att, exp, fac = process_row(row)
        script_dict[index] = {"utterance": utt,
                            "attend": att,
                            "expression": exp,
                            "face": fac}
    return script_dict

def input_text(script, state):
    print("-"*110)
    print("  A: Previous     BLANK: PLAY     D: Skip    -||-    Q: left     W: Center     E: Right    -||-  exit: Quit")
    print("-"*110)
    print("Next State: {}".format(state))

    if script[state]['utterance'] != None:
        print("Utterance:\t{}".format(script[state]['utterance']))
    if script[state]['attend'] != None:
        print("Attention:\t{}".format(script[state]['attend']))
    if script[state]['expression'] != None:
        print("Expression:\t{}".format(script[state]['expression']))
    if script[state]['face'] != None:
        print("Face-change:\t{}".format(script[state]['face']))

    ans = input("Input: ").lower()

    if ans == "a":
        state = state - 1
    elif ans == "d":
        state = state + 1 
    elif ans.isdigit():
        state = int(ans)
    elif ans == "q":
        furhat_attend('left') 
    elif ans == "w":
        furhat_attend('center') 
    elif ans == "e":
        furhat_attend('right') 

    elif ans == "exit":
        pass
    else:
        play_action(script[state])
        state = state + 1 

    if state <= 0: state = 0
    if state >= len(script): state = len(script)-1

    return ans, state

if __name__ == '__main__':

    script = read_script("script_table.csv")
    state = 0
    while True:
        token, state = input_text(script, state)
        if token == "exit":
            break