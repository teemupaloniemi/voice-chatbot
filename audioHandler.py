import wave
import pyaudio
#====================================#
# Class for handling audio i/o       #
#====================================#
class AudioHandler:

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

	# Start recording
        stream = audio.open(format=FORMAT, channels=CHANNELS,
				    rate=RATE, input=True,
				    frames_per_buffer=CHUNK)
        print(50*"=") 
        print("Recording...")
        
        frames = []
        #print(RATE, CHUNK, record_seconds)
        for i in range(0, int(RATE / CHUNK * record_seconds)):
            data = stream.read(CHUNK)
            frames.append(data)
            
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

