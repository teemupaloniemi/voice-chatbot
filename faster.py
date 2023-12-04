import os
from gtts import gTTS
import requests
import json
import contextlib
import playsound
import sys
import pyaudio
import wave
import whisper
import subprocess


# ANSI escape codes for some colors
RED = "\033[31m"  # Red text
GREEN = "\033[32m"  # Green text
YELLOW = "\033[33m"  # Yellow text
BLUE = "\033[34m"  # Blue text
MAGENTA = "\033[35m"  # Magenta text
CYAN = "\033[36m"  # Cyan text
RESET = "\033[0m"  # Reset to default color


def get_response_from_llama_server(prompt):
    try: 
        url = 'http://localhost:8080/completion'  # Replace with the correct URL if needed
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({
            'prompt': prompt,
            'n_predict': 100  # Adjust as needed
        })

        response = requests.post(url, headers=headers, data=data)
        #print(RED + str(response.json()) + RESET)
        if response.status_code == 200:
            return response.json()['content']
        else:
            return "Error: " + response.text
    except: 
        print(RED + "ERROR: " + RESET + "Start up the llama.cpp server with \"" + GREEN + "./server -m models/YOUR_MODEL -ngl 100" + RESET + "\" in the llama.cpp folder!")

def record_voice(filename, record_seconds=5):
    # Setup the parameters for recording
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024

    audio = pyaudio.PyAudio()

    # Start recording
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)

    print("Recording...")
    frames = []

    for i in range(0, int(RATE / CHUNK * record_seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Stopped recording, analyzing...")
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

def transcribe_voice(filename):
    model = whisper.load_model("tiny")
    result = model.transcribe(filename, language='english')
    return result["text"]

def play(assistant_text): 
    language = 'en'
    sound = gTTS(text=assistant_text, lang=language, slow=False)
    
    filename = "speak.mp3"
    sound.save(filename)
    os.system("play " + "speak.mp3"+" tempo 1.5")
    os.remove(filename)

def main():
    while 1:
        # Record the user's voice
        voice_filename = "user_voice.wav"
        record_voice(voice_filename)

        # Transcribe the recorded voice
        transcription = transcribe_voice(voice_filename)
        preprompt = "Help answer my questions. Give a short answer, please.  My question is: "
        prompt = preprompt + transcription
        
        if len(transcription) == 0: 
            continue

        print(BLUE + "\nUser: " + RESET, transcription)


        if "exit" in transcription.lower() or "stop" in transcription.lower():
            break

        response = get_response_from_llama_server(transcription)
        print(CYAN + "Assistant: " + RESET + response.strip())
        play(response.strip())

if __name__ == "__main__": 
    main()

