import wave
import numpy as np
import os

class wave_reader:

    def __init__(self,wav_path):
        f = wave.open(wav_path,"rb")
        self.nchannels, self.sampwidth, self.framerate, self.nframes, self.comptype, self.compname = f.getparams()
        b_data = f.readframes(self.nframes)
        f.close()

        if self.sampwidth == 1:
            self.np_data = np.fromstring(b_data,dtype=np.uint8)
        elif self.sampwidth == 2:
            self.np_data = np.fromstring(b_data,dtype=np.uint16)
        elif self.sampwidth == 4:
            self.np_data = np.fromstring(b_data,dtype=np.uint32)

        if self.nchannels == 2:
            self.np_data = self.np_data.reshape(-1,2).T
        elif self.nchannels == 1:
            self.np_data = self.np_data.expand_dims(0)

    def cut(self,start_time,end_time):
        start = int(start_time*self.framerate)
        end = int(end_time*self.framerate)
        return self.np_data[:,start:end]
