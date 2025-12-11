import os
from dotenv import load_dotenv
from openai import OpenAI

# Load .env variables
load_dotenv()

client = OpenAI(
  api_key=os.getenv("OPENAI_API_KEY")
)

response = client.responses.create(
  model="gpt-5-nano",
  input="write a haiku about ai",
  store=True,
)

print(response.output_text)
