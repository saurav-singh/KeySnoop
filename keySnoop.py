#------------------------------------------------------------
# Imports
#------------------------------------------------------------
import sys
import pyaudio
import time
import random
import os
import wave
import threading
import time
from pydub import AudioSegment
import numpy
import queue
from pynput import keyboard
from os import listdir
from os.path import isfile, join
from pyAudioAnalysis3 import audioTrainTest as aT

#------------------------------------------------------------
# Thread Control
#------------------------------------------------------------
lo = threading.Lock()
onlyfiles = []

#------------------------------------------------------------
# Class to play audio segment
#------------------------------------------------------------
class playThread (threading.Thread):
    def __init__(self, file):
        threading.Thread.__init__(self)
        self.file = file

    def run(self):
        CHUNK = 1024

        wf = wave.open(self.file, 'rb')

        p = pyaudio.PyAudio()

        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        data = wf.readframes(CHUNK)

        while data != '':
            stream.write(data)
            data = wf.readframes(CHUNK)

        stream.stop_stream()
        stream.close()

        p.terminate()


#------------------------------------------------------------
# Class to Queue record stream 
#------------------------------------------------------------
class recordQThread (threading.Thread):
    def __init__(self, frames = []):
        threading.Thread.__init__(self)
        self.frames = frames
    def run(self):
           
            global q
            RATE = 44100           
            audiofile = AudioSegment(data=b''.join(self.frames),sample_width=2,frame_rate=RATE,channels=2)
            # data = numpy.fromstring(audiofile._data, numpy.int16)
            data = numpy.frombuffer(audiofile._data, numpy.int16)

            x = []
            for chn in range(audiofile.channels):
                x.append(data[chn::audiofile.channels])
            x = numpy.array(x).T
           # print "X: " + str(len(x))
            lo.acquire()
            #print "Q: " + str(q.qsize())
            q.put(x)
            lo.release()


#------------------------------------------------------------
# Class to record audio segment
#------------------------------------------------------------
class recordThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        global q
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 2
        RATE = 44100
        RECORD_SECONDS = 0.3
        WAVE_OUTPUT_FILENAME = "output.wav"

        p = pyaudio.PyAudio()


        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        output=True,
                        frames_per_buffer=CHUNK)

        frames = []
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)  
            frames.append(data) 
   
        #recordQThread(frames).start()

        while True:
                frames.remove(frames[0])
                data = stream.read(CHUNK)  
                frames.append(data)
                recordQThread(frames).start()

def find(x):
    l = x[1].tolist()
    maX = max(l)
    if (maX > 0.65 and maX < 0.99):
        match_index = l.index(max(l))
        Sens = x[2][match_index]

        if (Sens != "NOISE"):
            print(Sens)
    

#------------------------------------------------------------
# Class to analyze audio segment
#------------------------------------------------------------
class analyseThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global q

        while True:
            lo.acquire()

            while not q.empty():
                f = q.get()
                x = aT.fileClassification(f, "models/svmModel", "svm")
                
                q.task_done()
                flagStart = True
                if flagStart:
                    flagStart = False 
                    onlyObj = [f for f in listdir('.') if not isfile(join('.', f))]
                    onlyObj.remove("pyAudioAnalysis3")
                    counter = 2

                    find(x)
            
                        
            lo.release()


#------------------------------------------------------------
# Class to record Audio Surface
#------------------------------------------------------------
def addSurfacePoint(surfacePointName):
    print ("Starting Record")
    recordSurfacePoint(surfacePointName)

def recordSurfacePoint(surfacePointName):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    RECORD_SECONDS = 0.9
    randomFileName = str((random.random() * 100) * (random.random() * 100))
    WAVE_OUTPUT_FILENAME = randomFileName + ".wav"

    p = pyaudio.PyAudio()   

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK)

    print("* Recording in ")
    print (".. 2")
    time.sleep(0.2)
    print (".. 1")
    time.sleep(0.2  )
    print ("Tap!")
    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    
    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    if not os.path.exists (surfacePointName):
        os.mkdir(str(surfacePointName))

    os.rename(WAVE_OUTPUT_FILENAME, surfacePointName + "/" + WAVE_OUTPUT_FILENAME)

#------------------------------------------------------------
# Class to record key stroke audio segments
#------------------------------------------------------------
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
            
            if not os.path.exists (surfacePointName):
                os.mkdir(str(surfacePointName))

            os.rename(WAVE_OUTPUT_FILENAME, surfacePointName + "/" +  WAVE_OUTPUT_FILENAME)

#------------------------------------------------------------
# Driver functions
#------------------------------------------------------------

def train():
    audio_data_location = ["audio_data/" + f for f in listdir('audio_data')]
    aT.featureAndTrain(audio_data_location, 1.0, 1.0, aT.shortTermWindow, aT.shortTermStep, "svm", "models/svmModel", False)

def start():
    global q
    q = queue.Queue()
    recordThread().start()
    analyseThread().start()

def recordKey():
    recordSurfacePoint().start()
    lis = keyboard.Listener(on_press=on_press)
    lis.start() # start to listen on a separate thread
    lis.join() # no this if main thread is polling self.keys

def recordSurface():
    surfaceName = input("Surface Name: ")
    numberOfInputs = input("Number of Data Points: ")
    for i in range(0,int(numberOfInputs)):
        print ("Input " + str(i+1))
        addSurfacePoint(surfaceName)
      