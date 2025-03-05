import requests
import pprint
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from skills_python import robot_info

"""test for search_docs api of the knowledge base"""


TOOLS = []
pp = pprint.PrettyPrinter()

api_base_url = robot_info.Langchain_chatchat_API
api = "knowledge_base/search_docs"

url = api_base_url + api
query = """
move object1 to object2 and move object2 to object3
"""
print("\n检索知识库：")
print(query)
r = requests.post(url, json={"knowledge_base_name": "skill_library", "query": query})
data = r.json()
for i, tool in enumerate(data):
    print(tool["metadata"]["source"][:-4])
    print(tool["score"])
    print()
    TOOLS.append(tool["page_content"])
tool_descs = "\n\n".join(TOOLS)
# pp.pprint(data)
print(tool_descs)
