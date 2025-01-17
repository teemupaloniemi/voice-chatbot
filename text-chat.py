import os
import requests
import json
import contextlib
import io
import sys
import wave


# ANSI escape codes for some colors
RED = "\033[31m"  # Red text
GREEN = "\033[32m"  # Green text
YELLOW = "\033[33m"  # Yellow text
BLUE = "\033[34m"  # Blue text
MAGENTA = "\033[35m"  # Magenta text
CYAN = "\033[36m"  # Cyan text
RESET = "\033[0m"  # Reset to default color


def generate(prompt):
    try: 
        url = 'http://localhost:8081/completion'  # Replace with the correct URL if needed
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({
            'prompt': prompt,
            'n_predict': 8192  # Adjust as needed
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
def tokenize(transcription, past_interaction): 
        system = "<|im_start|>system\nYou are an assistant called Lexie. You are a superintelligent system developed to help users and answer their questions. Give a short answer, please. You, Lexie, are really smart and answers in clear fashion but accurately<|im_end|>"
        for item in past_interaction: 
            system += item['user'] + item['assistant']
        user = "<|im_start|>user\n" + transcription + "<|im_end|>"
        assistant = "<|im_start|>assistant\n"
        prompt = system + user + assistant
        return prompt, user, assistant


# Llama-3
def tokenize_llama(transcription, past_interaction): 
        system = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\nYou are an assistant called Lexie. You are a superintelligent system developed to help users and answer their questions. Give a short answer, please. You, Lexie, are really smart and answers in clear fashion but accurately<|eot_id|>"
        for item in past_interaction: 
            system += item['user'] + item['assistant']
        user = "<|start_header_id|>user<|end_header_id|>\n" + transcription + "<|eot_id|>"
        assistant = "<|start_header_id|>assistant<|end_header_id|>\n"
        prompt = system + user + assistant
        return prompt, user, assistant

"""
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{{ system_prompt }}<|eot_id|><|start_header_id|>user<|end_header_id|>

{{ user_message }}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

def main():
    PRINT_CACHE = False
    past_interaction = []
    while 1:
        past_user = ''
        past_assistant = ''

        # Transcribe the recorded voice
        transcription = input("\nUser: ") # <--- here is the input point

        # Exit calls
        if "exit" in transcription.lower() or "stop" in transcription.lower():
            break

        # Tokenize the prompt
        prompt, user, assistant = tokenize_llama(transcription, past_interaction)
	
        # Generate response to prompt
        response = generate(prompt)
        if "<|im_end|>" in response: 
            response.replace('<|im_end|>', '')

        # Handle past interaction. This works as a short term memory for the model.
        past_user = user
        past_assistant = assistant + response.strip() + "<|im_end|>"
	
        # How many of the past interactions we want to keep in memory
        # Be awere of the context length! 
        cache_length = 4
        if len(past_interaction) > cache_length: 
            past_interaction.pop(0)
 
        # Print answer
        print(YELLOW + "Assistant: " + RESET + response.strip()) # <--- here is the output point

        if '```python' in response:
            print(f"{RED} Python detected! Do you want to run it (y/n)? {RESET}")
            ans = input("(y/n)")  # apparently some sort of AI-safety thing :)
            if 'y' in ans:
                code = response.split('```python')[1].split('```')[0]
                print(RED + "Running: " + RESET + code)

                # Redirect stdout to capture prints
                old_stdout = sys.stdout  # Save the current stdout
                sys.stdout = buffer = io.StringIO()
                err = ""
                try: 
                    # Execute the code
                    exec(code)
                except Exception as e:
                    print(RED + f"ERROR in running code {e}" + RESET)
                    err = str(e) 

                # Restore stdout and get the captured output
                sys.stdout = old_stdout
                captured_output = buffer.getvalue()
                print(YELLOW + "Captured Output:\n" + captured_output + " \nPossible errors: " + err + RESET)
                past_assistant = past_assistant.replace('<|im_end|>', ' ') + captured_output + err + '<|im_end|>'

        past_interaction.append({'user': past_user, 'assistant': past_assistant})
        # Print cache
        if PRINT_CACHE:
            print(MAGENTA + '-'*16 + "MEMORY WINDOW START" + '-'*16 + RESET) 
            for i, line in enumerate(past_interaction): 
                print(f"Q:{i}")
                print(MAGENTA + "Cache user: " + RESET + line['user'])
                print(MAGENTA + "Cache assistant: " + RESET + line['assistant'])
            print(MAGENTA + '-'*16 + "MEMORY WINDOW END" + '-'*16 + RESET)
if __name__ == "__main__": 
    main()

