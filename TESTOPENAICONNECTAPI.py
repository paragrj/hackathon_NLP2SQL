import os
from openai import AzureOpenAI

# endpoint = "https://nlptosqlaz.openai.azure.com/"
# model_name = "gpt-35-turbo"
# deployment = "gpt-35-turbo"
from dotenv import load_dotenv
load_dotenv()
DeploymentName = os.environ["DeploymentName"]
EndPoint_URL = os.environ["EndPoint_URL"]
EndPoint_KEY = os.environ["EndPoint_KEY"]

# subscription_key = "1dcEfwBJAhfc8rNAS19JXw9ytX4EXi1zEDdNBRrCci0fg1sgDxFKJQQJ99BEAC77bzfXJ3w3AAABACOGMuiw"
# api_version = "2024-12-01-preview"

# client = AzureOpenAI(
#     api_version=api_version,
#     azure_endpoint=endpoint,
#     api_key=subscription_key,
# )

client = AzureOpenAI(
    azure_endpoint=EndPoint_URL,
    api_key=EndPoint_KEY,
    api_version='2024-12-01-preview',)

response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        },
        {
            "role": "user",
            "content": "I am going to Paris, what should I see?",
        }
    ],
    max_tokens=4096,
    temperature=1.0,
    top_p=1.0,
    model=DeploymentName
)

print(response.choices[0].message.content)