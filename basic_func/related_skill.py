import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from _basic_info import (
    DECOMPOSITION_PROMPT,
    construct_tool_descs,
    RELATED_SKILL_PROMPT,
    basic_tools,
)
from dashscope import Generation
from dashscope.api_entities.dashscope_response import Role
import json
import os


def related_skill(task):
    """
    This function aims to generate a list of related skills and concatenated descriptions based on the given task.
    It iterates through the skill list, reads and concatenates each skill's description content, marking basic tools and integrated tools as "Basic tool" and "Integrated tool", respectively. Finally, the function returns the list of skills and the combined content.
    """
    tool_name, tool_descs = construct_tool_descs(
        withparameter=False, integrated_tools=True
    )
    related_skill_prompt = RELATED_SKILL_PROMPT.format(task=task, tools=tool_descs)
    messages = [
        {
            "role": Role.SYSTEM,
            "content": "You are a helpful assistant that writes python code.",
        },
        {"role": Role.USER, "content": related_skill_prompt},
    ]
    response = Generation.call(
        # Generation.Models.qwen_max,
        model="qwen-max-1201",
        messages=messages,
        result_format="message",  # set the result to be "message" format.
        temperature=0,
    )
    resp = response.output.choices[0]["message"]["content"]
    skills = json.loads(resp)
    skills = list(set(skills))
    folder_path = "skills_desc"

    # 存储拼接的内容
    combined_content = ""

    # 遍历列表
    for skill in skills:
        # 构建文件路径
        file_path = os.path.join(folder_path, skill + ".txt")

        # 打开文件并读取内容
        with open(file_path, "r") as file:
            content = file.read()
        if skill in basic_tools:
            # 拼接内容
            combined_content += "##Basic tool## " + content + "\n\n"
        else:
            combined_content += "##Integrated tool## " + content + "\n\n"

    # 输出结果
    return skills, combined_content
