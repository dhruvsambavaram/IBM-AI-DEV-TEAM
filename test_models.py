import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from groq import Groq
api_key = os.environ.get('GROQ_API_KEY', '')
client = Groq(api_key=api_key, timeout=30)

for model in ['openai/gpt-oss-20b', 'openai/gpt-oss-120b']:
    for tokens in [200, 500, 900]:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{'role': 'user', 'content': 'Write a python function that adds two numbers. Return only the code.'}],
                max_tokens=tokens
            )
            content = resp.choices[0].message.content
            chars = len(content or '')
            preview = (content or '')[:80].replace('\n', ' ')
            print(f'OK  {model} @{tokens}t: {chars} chars | {preview}')
        except Exception as e:
            print(f'ERR {model} @{tokens}t: {str(e)[:120]}')
