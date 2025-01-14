import matplotlib.pyplot as plt
import os
import wave
import pyaudio
from scipy import signal
import numpy as np

STOP_THRESHOLD = 16
#====================================#
# Class for handling audio i/o       #
#====================================#
class AudioHandler:

    def __init__(self, DEBUG=True):
        self.DEBUG = DEBUG
        if DEBUG:
            print("Debug set to True! For production set it to False.")

    # This is for recording ther user input
    # @param: filename -- a path to the audio (WAV) -file that is saved to current folder. 
    # @param: record_seconds -- interger: how many seconds we record for one prompt 
    def record_voice(self, filename, record_seconds):
	# Setup the parameters for recording
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK = 1024
        audio = pyaudio.PyAudio()

	# Open stream for recording input
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print(50*"=") 
        print("Recording...")
    
        if self.DEBUG:
            vals = []
        frames = []    
        avgs = []
        aads = []

        # Amplitude moving average meter
        amp_ma_meter = ma_meter(32000, 0)

        # Amplitude moving average average meter
        aa_ma_meter = ma_meter(32000, 0)

        # Amplitude differential meter
        aad_ma_meter = ma_meter(128000, 0)

        # Extract integer values from bytes
        # LSB is first
        # t[i] + 0x100*t[i+1] 
        def b2i(bytes_data):
            tmp_i_data = []
            for idx in range(0, len(bytes_data), 2):
                N = bytes_data[idx] + 0x100*bytes_data[idx+1]
                if (N & (1 << (16 - 1))) != 0:
                    N = N - (1 << 16)
                tmp_i_data.append(int(N))
            return tmp_i_data 
        
        # Capture audio until speaking stops
        stop = False
        last_aad_avg = 0
        while not stop:
        #for i in range(0, int(RATE / CHUNK * record_seconds)):

            # Read  data from source (microphone/file)
            data = stream.read(CHUNK)
            frames.append(data)

            i_data = b2i(frames[-1]) # convert from bytes to int array/list
            for i in i_data:
                # Raw signal
                if self.DEBUG:
                    vals.append(i)

                # Amplitude moving averange
                amp_ma_meter.put(abs(i))
                
                # Amplitude moving average average
                avg = amp_ma_meter.average()
                aa_ma_meter.put(avg)
                if self.DEBUG:
                    avgs.append(avg)

                # Amplitude differential
                diff = aa_ma_meter.get_history() - aa_ma_meter.get_last()
                aad_ma_meter.put(diff)
                
                # Check amplitude differential moving average
                aad_avg = aad_ma_meter.average()
                if self.DEBUG:
                    aads.append(aad_avg)
                #print(f"| Data point: {i:3f} | Moving avg: {avg:3f} | Differential: {diff:3f} | Differential moving average: {aad_avg:3f} |")

                # Stop if the average derivative is negative 
                if aad_avg < last_aad_avg:
                    print("Stopping...")
                    stop = True
                    break
                last_aad_avg = aad_avg
           
        
        # Debug means plotting
        if self.DEBUG:
            _, ax1 = plt.subplots()
            ax1.plot(vals, color='tab:blue')
            ax1.plot(avgs, color='tab:red')
            ax2 = ax1.twinx()   
            ax2.plot(aads, color='tab:green')
            ax2.plot(np.repeat([STOP_THRESHOLD], len(vals)), color='tab:purple')
            plt.show()
            
        print("Analyzing...")
        # Stop and close the stream and audio
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save the recorded data as a WAV file
        with wave.open(filename, 'wb') as waveFile:
            waveFile.setnchannels(CHANNELS)
            waveFile.setsampwidth(audio.get_sample_size(FORMAT))
            waveFile.setframerate(RATE)
            waveFile.writeframes(b''.join(frames))

    # Play assistant sound using piper and play
    def play(self, assistant_text): 
        print(50*"=") 
        filename = "speak.wav"
        os.system(f'printf "{assistant_text}" | piper -m en_US-amy-medium --output-file {filename}') 
        os.system("play " + filename +" tempo 1.5")
        os.remove(filename)

#====================================================================#
# Class for keeping track of a moving average of a data stream       #
#====================================================================#
class ma_meter:
    def __init__(self, buffer_length: int, initiallisation_val: int = 0):
        self.bl = buffer_length
        self.buf = [initiallisation_val] * buffer_length
        self.i = 0
        self.sum = initiallisation_val

    # Add a value to stream buffer (queue)
    def put(self, val: int):
        if (self.i >= self.bl):
            self.i %= self.bl
        self.buf[self.i], self.sum = val, self.sum + val - self.buf[self.i]
        self.i += 1
        return
    
    # Reutrn the average
    def average(self):
        return self.sum / self.bl
    
    # Return the most recently added item
    def get_last(self):
        if (self.i >= self.bl):
            self.i %= self.bl
        return self.buf[self.i]
    
    # Return the second latest item
    def get_history(self):
        if (self.i >= self.bl):
            self.i %= self.bl
        return self.buf[self.i-1]
