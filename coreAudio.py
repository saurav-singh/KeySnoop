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
            data = numpy.fromstring(audiofile._data, numpy.int16)
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

           # print("* HIT!")
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

        # if (Sens != "NOISE"):
        #     print(Sens)
    # time.sleep(1) 
    print(x)

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
                x = aT.fileClassification(f, "svmTaps", "svm")
                
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
# Driver functions
#------------------------------------------------------------

def train():
    audio_data_location = ["audio_data/" + f for f in listdir('audio_data')]
    print(audio_data_location)
    aT.featureAndTrain(audio_data_location, 1.0, 1.0, aT.shortTermWindow, aT.shortTermStep, "svm", "models/svmModel", False)
    
def start(option):
    
    startMode = False
    
    global q 
    q = queue.Queue(0)
         
    if(option == 1):
        audio_data_location = [f for f in listdir('models') if not isfile(join('models', f))]
        print(audio_data_location)
        aT.featureAndTrain(audio_data_location, 1.0, 1.0, aT.shortTermWindow, aT.shortTermStep, "svm", "svmSMTemp", False)
        
    elif(option == 2):
        surfaceName = input("Surface Name: ")
        while(surfaceName != 'x'):
            numberOfInputs = input("Number of Data Points: ")
            for i in range(0,int(numberOfInputs)):
                print ("Input " + str(i+1))
                addSurfacePoint(surfaceName)
            surfaceName = input("Surface Name: ")

    elif(option == 3):
        recordThread().start()
        analyseThread().start()


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

train()
