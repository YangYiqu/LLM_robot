from http import HTTPStatus
from pprint import pprint
import json
from dashscope import Generation
from dashscope import MultiModalConversation
from dashscope.api_entities.dashscope_response import Role
import sys
import os

"""generate the test data by using llm"""

parent_path = os.path.dirname(sys.path[0])
if parent_path not in sys.path:  # 避免重复加入
    sys.path.append(parent_path)

stop = ["Observation:", "Observation:\n"]
task = """ Please imitate the following examples to generate more data:

Output format:
"task","[Which items will appear together after the robot performs the task]"

Examples:
"put the grape at (1,1), and then move it to (2,2)",[]
"put the grape on the plate, and then bring the plate to the location of table","[['plate', 'table']]"
"move stick to the beach.","[['stick', 'beach']]"

"""

messages = [
    {
        "role": Role.SYSTEM,
        "content": "You are good at annalysing task and  imitating examples",
    },
    {"role": Role.USER, "content": task},
]

response = Generation.call(
    # Generation.Models.qwen_max,
    model="qwen-max-1201",
    messages=messages,
    result_format="message",  # set the result to be "message" format.
    stop_tokens=stop,
    temperature=0.05,
)
print(response.output.choices[0]["message"]["content"])
