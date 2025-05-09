import openai
from dotenv import dotenv_values

CONFIG = dotenv_values("config/.env")

api_key=CONFIG["OPENAI_API_KEY"]


class ChatGPT4:
    
    def __init__(self):
        """
        Initializes the ChatGPT-4 model with the provided API key.
        
        Parameters:
        api_key (str): The API key for OpenAI's API.
        """
        # self.client = openai.OpenAI(api_key=api_key)
        self.client = openai.OpenAI(api_key=api_key, base_url="https://api.openai-proxy.org/v1")
        # self.model_name = "gpt-3.5-turbo"
        self.model_name = "gpt-4"

    def answer(self, system_prompt, prompt):
        """
        Generates a response from the model based on the provided prompt.

        Parameters:
        system_prompt (str): The system prompt that influences the assistant's behavior.
        prompt (str): The user's query to generate a response for.
        json_output (bool): Whether the response should be formatted as a JSON object.

        Returns:
        str: The response from the model as a string or JSON object.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        # response_format = {"type": "json_object"} if json else None

        try:

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                # response_format=response_format
            )
        except Exception as e:
            print(f"Error during answering: {e}")
            return None


        return response.choices[0].message.content
