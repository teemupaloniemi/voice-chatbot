import requests
import json
from audioHandler import AudioHandler

# ANSI escape codes for some colors
RED = "\033[31m"  # Red text
GREEN = "\033[32m"  # Green text
YELLOW = "\033[33m"  # Yellow text
BLUE = "\033[34m"  # Blue text
MAGENTA = "\033[35m"  # Magenta text
CYAN = "\033[36m"  # Cyan text
RESET = "\033[0m"  # Reset to default color

#====================================#
# Class for creating an AI assistant #
#====================================#
class Assistant:
    
	# This is for generating text based on user text prompt
    # @param: prompt --  a string that is passed to the api 
    def generate(self, prompt):
        try: 
            url = 'http://localhost:8081/completion'  # Replace with the correct URL if needed
            headers = {'Content-Type': 'application/json'}
            data = json.dumps({
				'prompt': prompt,
				'n_predict': 1024  # Adjust as needed
			})

            response = requests.post(url, headers=headers, data=data)
			#print(RED + str(response.json()) + RESET)
            if response.status_code == 200:
                return response.json()['content']
            else:
                return "Error: " + response.text
        except: 
            print(RED + "ERROR: " + RESET + "Start up the llama.cpp server with \"" + GREEN + "./server -m models/YOUR_MODEL -ngl 100" + RESET + "\" in the llama.cpp folder!")

    # Mistral
    def tokenize(self, transcription, past_interaction): 
        system = "<|im_start|>system\nYou are an AI assistant known for your exceptional empathy and emotional intelligence. Your primary objective is to create a safe, supportive environment where users feel understood and valued. You achieve this by actively listening, asking meaningful and relevant questions, and responding with genuine concern and insight. At the same time, you are intellectually sharp and capable of challenging users' ideas and perspectives to promote growth and deeper understanding.<|im_end|>"
        for item in past_interaction: 
            system += item['user'] + item['assistant']
        user = "<|im_start|>user\n" + transcription + "<|im_end|>"
        assistant = "<|im_start|>assistant\n"
        prompt = system + user + assistant
        return prompt, user, assistant

    # Llama-3
    def tokenize_llama(self, transcription, past_interaction): 
        system = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\nYou are an assistant called Lexie. You are a superintelligent system developed to help users and answer their questions. Give a short answer, please. You, Lexie, are really smart and answers in clear fashion but accurately<|eot_id|>"
        for item in past_interaction: 
            system += item['user'] + item['assistant']
        user = "<|start_header_id|>user<|end_header_id|>\n" + transcription + "<|eot_id|>"
        assistant = "<|start_header_id|>assistant<|end_header_id|>\n"
        prompt = system + user + assistant
        return prompt, user, assistant

    # This is for transcribing speech to text
    # @param: filename -- a path to the audio (WAV) -file for the api
    def transcribe_voice(self, filename):
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
                return response.json()['text']
            else:
                print(f"Error: {response.status_code}\n{response.text}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
	    

#=====================================#
# Class for handling user interaction #
#=====================================#
class UI:
    
	# For init
    # @param: ai -- An Assistant object that handles the AI api communication
    # @param: audioHandler -- AudioHandler object that handles the audio i/o
    # @param: PRINT_CACHE -- A boolean flag for debugging past_interaction
    def __init__(self, ai, audioHandler, PRINT_CACHE=False):
        self.PRINT_CACHE = PRINT_CACHE
        self.ai = ai 
        self.audioHandler = audioHandler
        
    # This starts the interaction between user and ai
    def start(self):
        past_interaction = []
        while 1:
            past_user = ''
            past_assistant = ''
            # Record the user's voice
            voice_filename = "user_voice.wav"
            self.audioHandler.record_voice(voice_filename, 8)

            # Transcribe the recorded voice
            transcription = self.ai.transcribe_voice(voice_filename)        
            if len(transcription) == 0:
                continue
               
            # Wrap in model specific format
            prompt, user, assistant = self.ai.tokenize(transcription, past_interaction)

            # Not an activating command
            if '<enter assistant name here>' not in transcription.lower(): 
                cache_length = 10
                if len(past_interaction) > cache_length: 
                    past_interaction.pop(0)
                past_interaction.append({'user': transcription, 'assistant': ''}) 
                print(50*"=") 
                print(BLUE + "User: " + RESET, transcription)
                continue

            print(50*"=") 
            print(BLUE + "User: " + RESET, transcription)

	    # Exit calls
            if "exit" in transcription.lower() or "stop" in transcription.lower():
                break

            response = self.ai.generate(prompt)
            if "<|im_end|>" in response: 
                response.replace('<|im_end|>', '')

            past_user = user
            past_assistant = assistant + response.strip() + "<|im_end|>"
            cache_length = 10
            if len(past_interaction) > cache_length: 
                past_interaction.pop(0)
            past_interaction.append({'user': past_user, 'assistant': past_assistant})
	
            # Print answer
            self.outputHandler(response.strip(), self.audioHandler)

            # Print cache
            if self.PRINT_CACHE:
                print(MAGENTA + '-'*16 + "MEMORY WINDOW START" + '-'*16 + RESET) 
                for i, line in enumerate(past_interaction): 
                    print(f"Q:{i}")
                    print(MAGENTA + "Cache user: " + RESET + line['user'])
                    print(MAGENTA + "Cache assistant: " + RESET + line['assistant'])
                print(MAGENTA + '-'*16 + "MEMORY WINDOW END" + '-'*16 + RESET) 
	

	# Here to modify the way we handle output
    def outputHandler(self, output, ah):
        print(50*"=") 
        print(YELLOW + "Assistant: " + RESET + output.replace('<|im_end|>',''))
        if '```python' in output: 
            print(f"{RED} Python detected! Do you want to run it (y/n)? {RESET}")
            ans = input("(y/n)") # apparently some sort of AI-safety thing :)
            if 'y' in ans:
                code = output.split('```python')[1].split('```')[0]
                print(RED + "Running: " + RESET + code)
                exec(code)
        else: 
            ah.play(output.strip())
        print(50*"=") 
#=================================
    
def main():
    ai = Assistant()
    audioHandler = AudioHandler()
    ui = UI(ai, audioHandler)
    ui.start()
    
if __name__ == "__main__": 
    main()

