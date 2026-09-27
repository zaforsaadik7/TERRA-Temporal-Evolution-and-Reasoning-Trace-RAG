import os
import sys
import time
from dotenv import load_dotenv
import openai

# Load environment variables from .env
load_dotenv()

print("=" * 60)
print("=== AWS BEDROCK MANTLE API CHECK ===")
print("=" * 60)

# Check Bearer Token
token = os.environ.get("AWS_BEARER_TOKEN_BEDROCK")
if not token:
    print("❌ FAIL: AWS_BEARER_TOKEN_BEDROCK is missing from environment / .env")
    sys.exit(1)

print(f"✓ AWS_BEARER_TOKEN_BEDROCK present (Length: {len(token)} chars)")

base_url = "https://bedrock-mantle.us-east-1.api.aws/v1"
print(f"✓ Target Base URL: {base_url}")

client = openai.OpenAI(
    api_key=token,
    base_url=base_url
)

# Active models used in TERRA project
models_to_test = [
    ("deepseek.v3.2", "Generation Strong Tier"),
    ("mistral.ministral-3-8b-instruct", "Generation Fast Tier"),
    ("qwen.qwen3-235b-a22b-2507", "Judge Model")
]

all_passed = True

print("\n--- Testing Model Completion Endpoints ---")
for model_id, role in models_to_test:
    print(f"\n[Test] Model: {model_id} ({role})...")
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "user", "content": "Respond with the single word 'OK' if you can read this."}
            ],
            max_tokens=20,
            temperature=0.0
        )
        elapsed = (time.time() - start_time) * 1000
        content = response.choices[0].message.content.strip()
        print(f"  Status: SUCCESS ({elapsed:.1f} ms)")
        print(f"  Response: {repr(content)}")
    except Exception as e:
        all_passed = False
        print(f"  Status: FAILED")
        print(f"  Error: {e}")

print("\n" + "=" * 60)
if all_passed:
    print("✅ RESULT: AWS Bedrock API is WORKING perfectly across all models.")
else:
    print("❌ RESULT: AWS Bedrock API check failed for one or more models.")
print("=" * 60)
