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

#=================================

def generate(prompt):
    try: 
        url = 'http://localhost:8081/completion'  # Replace with the correct URL if needed
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({
            'prompt': prompt,
            'n_predict': 128  # Adjust as needed
        })

        response = requests.post(url, headers=headers, data=data)
        #print(RED + str(response.json()) + RESET)
        if response.status_code == 200:
            return response.json()['content']
        else:
            return "Error: " + response.text
    except: 
        print(RED + "ERROR: " + RESET + "Start up the llama.cpp server with \"" + GREEN + "./server -m models/YOUR_MODEL -ngl 100" + RESET + "\" in the llama.cpp folder!")

#=================================

def record_voice(filename, record_seconds=3):
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

    print("Recording...")
    frames = []

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

#=================================

def transcribe_voice(filename):
    url = 'http://127.0.0.1:8080/inference'
    file_path = filename
    temperature = '0.0'
    temperature_inc = '0.2'
    response_format = 'json'

    try:
        files = {'file': ('file', open(file_path, 'rb'))}
        data = {
            'temperature': temperature,
            'temperature_inc': temperature_inc,
            'response_format': response_format
        }

        response = requests.post(url, files=files, data=data)

        if response.status_code == 200:
            #print("Response: ", response)
            return response.json()['text']
        else:
            print(f"Error: {response.status_code}\n{response.text}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
#=================================

def play(assistant_text): 
    language = 'en'
    sound = gTTS(text=assistant_text, lang=language, slow=False)
    
    filename = "speak.mp3"
    sound.save(filename)
    os.system("play " + "speak.mp3"+" tempo 1.5")
    os.remove(filename)

#=================================

def tokenize(transcription, past_interaction): 
        system = "<|im_start|>system\nYou are an assistant called Lexie. Help answer my questions. Give a short answer, please.  Lexie is really smart and answers in clear fashion but accurately<|im_end|>"
        for item in past_interaction: 
            system += item['user'] + item['assistant']
        user = "<|im_start|>user\n" + transcription + "<|im_end|>"
        assistant = "<|im_start|>assistant\n"
        prompt = system + user + assistant
        return prompt, user, assistant

#=================================

def main():
    PRINT_CACHE = False
    past_interaction = []
    while 1:
        past_user = ''
        past_assistant = ''
        # Record the user's voice
        voice_filename = "user_voice.wav"
        record_voice(voice_filename)

        # Transcribe the recorded voice
        transcription = transcribe_voice(voice_filename)        
        if len(transcription) == 0: 
            continue
        print(BLUE + "\nUser: " + RESET, transcription)

        # Exit calls
        if "exit" in transcription.lower() or "stop" in transcription.lower():
            break

        # Tokenize the prompt
        prompt, user, assistant = tokenize(transcription, past_interaction)

        # Generate response to prompt
        response = generate(prompt)
        if "<|im_end|>" in response: 
            response.replace('<|im_end|>', '')

        # Handle past interaction. This works as a short term memory for the model.
        past_user = user
        past_assistant = assistant + response.strip() + "<|im_end|>"
        
        # How many of the past interactions we want to keep in memory
        # Be awere of the context length! 
        cache_length = 10
        if len(past_interaction) > cache_length: 
            past_interaction.pop(0)
        past_interaction.append({'user': past_user, 'assistant': past_assistant})
 
        # Print answer
        print(YELLOW + "Assistant: " + RESET + response.strip())

        # Check if there is runnable code (inspired by George Hotz)
        if '```python' in response: 
            print(f"{RED} Python detected! Do you want to run it (y/n)? {RESET}")
            ans = input("(y/n)") # apparently some sort of AI-safety thing :)
            if 'y' in ans:
                code = response.split('```python')[1].split('```')[0]
                print(RED + "Running: " + RESET + code)
                exec(code)
        else: 
            play(response.strip())
        
        # Print cache
        if PRINT_CACHE:
            print(MAGENTA + '-'*16 + "MEMORY WINDOW START" + '-'*16 + RESET) 
            for i, line in enumerate(past_interaction): 
                print(f"Q:{i}")
                print(MAGENTA + "Cache user: " + RESET + line['user'])
                print(MAGENTA + "Cache assistant: " + RESET + line['assistant'])
            print(MAGENTA + '-'*16 + "MEMORY WINDOW END" + '-'*16 + RESET) 

#=================================

if __name__ == "__main__": 
    main()

