import openai
import base64
import os

from call_data import CallData

current_dir = os.getcwd()
print(current_dir)

BOSON_API_KEY = os.getenv("BOSON_API_KEY")

def encode_audio_to_base64(file_path: str) -> str:
    """Encode audio file to base64 format."""
    with open(file_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode("utf-8")
    


def evaluate_message(prev_call_data: list[CallData], 
                     api_key=BOSON_API_KEY, 
                     model="higgs-audio-understanding-Hackathon", 
                     file_format='wav',
                     base_url='https://hackathon.boson.ai/v1') -> str:
    
    client = openai.Client(
        api_key=api_key,
        base_url=base_url)
    
    system_content = "You are a 911 call trainer evaluating operator performance."
    output_questions = current_dir + "/backend/data/individual_summary_prompt.txt"

    messages = [{"role": "system", "content": system_content}]
    for call_data in prev_call_data:
        messages.append(
            {
                "role": "user", 
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": call_data.audio,
                            "format": file_format,
                        },
                    }
                ]
            }
        )
    
    messages.append({"role": "user", "content": output_questions})
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        # max_completion_tokens=512,
        temperature=0.1
    )

    return response.choices[0].message.content




def evaluate_call(call_data: list[CallData], 
                  api_key=BOSON_API_KEY, 
                  model="higgs-audio-understanding-Hackathon", 
                  file_format='wav',
                  base_url='https://hackathon.boson.ai/v1') -> str:
    
    client = openai.Client(
        api_key=api_key,
        base_url=base_url)
    
    eval_path = current_dir + "/operator_evaluation_guidelines.txt"
    system_content = "You are a 911 call trainer evaluating operator performance."
    output_questions = current_dir + "/backend/data/summary_prompt.txt"

    # audio_base64 = encode_audio_to_base64(audio_path)
    # file_format = audio_path.split(".")[-1]

    messages = [{"role": "system", "content": system_content}]
    for data in call_data:
        messages.append(
            {
                "role": "user", 
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": call_data.audio,
                            "format": file_format,
                        },
                    }
                ]
            }
        )
    
    messages.append({"role": "user", "content": output_questions})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        # max_completion_tokens=512,
        temperature=0.1
    )

    return response.choices[0].message.content



# The transcript provided is a recording of a 911 call in which the operator answers the call and asks the caller for their location and the nature of the emergency. The caller is a male who speaks in a somewhat agitated tone, stating that he has three hostages in an RV and is requesting a nuclear bomb. The operator asks for the address of the RV, and the caller provides it. The operator then dispatches the appropriate emergency services.

# Overall, the operator handled the call appropriately by asking for the necessary information and dispatching the correct service. The tone used by the operator was professional and calm, which is essential in emergency situations. The only area for improvement is to ensure that the caller is taken seriously and that the situation is handled with urgency. Despite this minor concern, the operator's performance can be rated as an 8/10.