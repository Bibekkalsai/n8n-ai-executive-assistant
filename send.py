import requests

# Paste your exact copied n8n Webhook URL here (no < > brackets)
url = "n8n Webhook URL"

query = input("Enter your query: ")

response = requests.post(
    url,
    json={"query": query, "sessionId": "test-session-1"},
    timeout=60,
)

print("Status:", response.status_code)
print("Response:", response.text)