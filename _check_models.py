import httpx, os
from dotenv import load_dotenv
load_dotenv()

r = httpx.get(
    "https://api.groq.com/openai/v1/models",
    headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
)
models = r.json()
for m in models.get("data", []):
    mid = m["id"]
    if any(k in mid.lower() for k in ["llama", "mixtral", "gemma", "tool"]):
        print(mid)
