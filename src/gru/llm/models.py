import os
import re
import requests 

class OpenAIModel:

    def __init__(self, system: str, temperature=0.3):
        """Sets up the model with a system prompt and a temperature"""
        
        self.model = 'gpt-3.5-turbo'
        self.apikey = os.getenv('OPENAI_KEY')
        self.baseurl = "https://api.openai.com/v1/chat/completions"
        self.system = system
        self.temperature = temperature
        self.abstract_base = "You are an AI assistant that writes Python code. "
        self.messages = [{"role": "system", "content": self.system}]

    def reset(self):
        self.messages = [{"role": "system", "content": self.system}]

    def generate_full(self, query: str) -> str:
        
        headers = {
            'Authorization': f'Bearer {self.apikey}',
            'Content-Type': 'application/json'
        }
        
        base = self.abstract_base 
        data = {
            'model': self.model, 
            'messages': [
                {'role': 'user', 'content': base + "\n" + query}
            ]
        }            
        
        tries = 0
        while tries < 5:
            try:
                response = requests.post(self.baseurl, headers=headers, json=data)
                res = response.json()['choices'][0]['message']['content']
                return res
            except:
                tries += 1
        raise Exception(f"Failed to get response after {tries} tries.")

# Initialize the model
model = OpenAIModel(system="", temperature=0.2)

if __name__ == "__main__":
    model = ChatModel(system="", temperature=0.2)
    res1 = model.generate_full("""Find survey papers on Julia.""")
    print(res1)
    breakpoint()
