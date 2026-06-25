import sys

with open('core/ai/llm_clients.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace bare excepts
content = content.replace('except:', 'except Exception:')

# Fix httpx delete parameter issue
content = content.replace(
    "self.client.delete('/api/delete', json={'name': model})",
    "self.client.request('DELETE', '/api/delete', json={'name': model})"
)

with open('core/ai/llm_clients.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix applied successfully.")
