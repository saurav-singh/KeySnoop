import sys
import pyaudio
import time
import random
import os
import wave
import threading
import threading
import time
from pydub import AudioSegment
import numpy
from os import listdir
from os.path import isfile, join
from pynput import keyboard
######################################################################################

def on_press(key):
    global keyPressedFlag        
    global keyPressed
    try: k = key.char #single-char keys
    except: k = key.name # other keys
    if key == keyboard.Key.esc: return False # stop listener
    #if k in ['1', '2', 'left', 'right']: # keys interested
        # self.keys.append(k) # store it in global-like variable
    print('Key pressed: ' + k)
    keyPressed = k
    keyPressedFlag = True

    #return False # remove this if want more keys
class recordSurfacePoint (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        global keyPressedFlag        
        global keyPressed
        keyPressedFlag = False
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        RECORD_SECONDS = 1


        while(True):
            p = pyaudio.PyAudio()

            stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            output=True,
                            frames_per_buffer=CHUNK)

            
            print("* Recording in ")
            frames = []

            i = 0  
            while(True):
                i += 1
                data = stream.read(CHUNK)
                frames.append(data)
                if ((i >int((RATE / CHUNK * RECORD_SECONDS)*0.3)) and (keyPressedFlag == False)):
                    frames.remove(frames[0])
                elif(keyPressedFlag == True):
                    for j in range(0, int((RATE / CHUNK * RECORD_SECONDS)*0.7)):
                        data = stream.read(CHUNK)
                        frames.append(data)
                    keyPressedFlag = False
                    break
            
            print("* done recording")

            stream.stop_stream()
            stream.close()
            p.terminate()

            randomFileName = str((random.random() * 100) * (random.random() * 100))
            WAVE_OUTPUT_FILENAME = randomFileName + ".wav"

            wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
           
            surfacePointName = keyPressed

            #if not os.path.exists ("keys/" + surfacePointName):
             #   os.mkdir("keys/" + str(surfacePointName))
            
            if not os.path.exists (surfacePointName):
                os.mkdir(str(surfacePointName))

            #os.rename(WAVE_OUTPUT_FILENAME, "keys/" + surfacePointName + "/" +  WAVE_OUTPUT_FILENAME)
            os.rename(WAVE_OUTPUT_FILENAME, surfacePointName + "/" +  WAVE_OUTPUT_FILENAME)


def recordKey():
    recordSurfacePoint().start()
    lis = keyboard.Listener(on_press=on_press)
    lis.start() # start to listen on a separate thread
    lis.join() # no this if main thread is polling self.keys

