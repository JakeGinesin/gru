import openai
import os

class OpenAIModel:
    def __init__(self, model_name='gpt-4', api_key=None):
        self.model_name = model_name
        # Set the API key from the provided argument or environment variable
        openai.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not provided. Set it via the 'api_key' argument or 'OPENAI_API_KEY' environment variable.")

    def generate_full(self, prompt):
        response = openai.ChatCompletion.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an assistant that writes code."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
            n=1,
            stop=None,
        )

        # Extract the assistant's reply
        completion = response['choices'][0]['message']['content'].strip()
        return completion

# Initialize the model
model = OpenAIModel()
