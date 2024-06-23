from openai import OpenAI

client = OpenAI(api_key="YourAPIKeyHere")

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a bitrix24 salesman helpful assistant."},
        {"role": "user", "content": "What is the best CMS for business?"}
    ]
)
# Access text content from "message" within the first "Choice"
ai_response = response.choices[0].message.content
print(ai_response.strip())
