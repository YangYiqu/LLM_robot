import requests
import os
import pprint
import json
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from skills_python import robot_info

"""
test for the chat api of the langchain chatchat with the knowledge base
"""


def dump_input(d, title):
    print("\n")
    print("=" * 30 + title + "  input " + "=" * 30)
    pprint(d)


headers = {
    "accept": "application/json",
    "Content-Type": "application/json",
}
api = "/chat/knowledge_base_chat"
url = robot_info.Langchain_chatchat_API + "chat/knowledge_base_chat"
data = {
    "query": "how many tool api that the robot can use, please list them",
    "knowledge_base_name": "skill_library",
    "temperature": 0.0,
    "history": [
        {"role": "user", "content": "who are you?"},
        {"role": "assistant", "content": "hello,I am qwen"},
    ],
    "stream": True,
}

final_answer = ""
response = requests.post(url, headers=headers, json=data, stream=True)
print("\n")
print("=" * 30 + api + "  output" + "=" * 30)
print(response)
for line in response.iter_content(None, decode_unicode=True):
    data = json.loads(line[6:])
    if "answer" in data:
        print(data["answer"], end="", flush=True)
        final_answer += data["answer"]
# print(final_answer)
assert "docs" in data and len(data["docs"]) > 0
assert response.status_code == 200
