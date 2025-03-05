import requests
import pprint
import json
import re
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from skills_python import robot_info

"""test for upload_docs api of the langchain chatchat database"""

test_files = {"tool_descs.txt": robot_info.Local_Path + "data\\tool_descs.txt"}
files = [("files", (name, open(path, "rb"))) for name, path in test_files.items()]
print(files)
data = {"knowledge_base_name": "skill_library", "override": True}
r = requests.post(
    robot_info.Langchain_chatchat_API + "knowledge_base/upload_docs",
    data=data,
    files=files,
)
print(r)
data = r.json()
# pprint(data)
