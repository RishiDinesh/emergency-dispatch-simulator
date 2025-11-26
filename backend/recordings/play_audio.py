import json
import base64
import sys
import os
import subprocess
import tempfile

def play_audio(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from '{file_path}'.")
        return

    if not isinstance(data, list):
        print("Error: JSON content is not a list.")
        return

    for i, message in enumerate(data):
        role = message.get('role')
        transcription = message.get('transcription', '(No transcription)')
        print(f"\nMessage {i+1} ({role}): {transcription}")

        if role == 'assistant' and 'audio' in message:
            if not (audio_b64 := message['audio']):
                print("  (No audio data)")
                continue
            try:
                audio_data = base64.b64decode(audio_b64)
            except Exception as e:
                print(f"  Error processing audio: {e}")
                continue
                
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav') as temp_audio:
                temp_audio.write(audio_data)
                temp_audio_path = temp_audio.name
            
                print("  Playing audio...")
                # Play audio using afplay on macOS
                try:
                    subprocess.run(['afplay', temp_audio_path], check=True)
                except FileNotFoundError:
                    print("  Error: 'afplay' command not found...")
                except subprocess.CalledProcessError as e:
                    print(f"  Error playing audio: {e}")
                
                

def play_conversation(folder_path):
    
    file_paths = [os.path.join(folder_path, f) 
                  for f in os.listdir(folder_path) 
                  if os.path.isfile(os.path.join(folder_path, f))]
    file_paths.sort()
    
    for file_path in file_paths:
        print("=" * 50)
        print(f"** {file_path} **")
        play_audio(file_path)
    

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python play_audio.py <path_to_log_file | path_to_log_files_folder>")
        sys.exit(1)
    
    path = sys.argv[1]

    if os.path.isdir(path):
        print(f"Playing conversation in folder {path}")
        play_conversation(path)
    else:
        play_audio(path)
