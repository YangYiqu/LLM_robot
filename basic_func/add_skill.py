import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pprint import pprint
import json
from dashscope import Generation
from dashscope.api_entities.dashscope_response import Role
from _basic_info import (
    SKILL_PROMPT,
    TOOL_DESC,
    construct_tool_descs,
    PARA_GENERATED_PROMPT,
    RECTIFY_PROMPT,
)
from self_verification import self_verification
import requests
import numpy as np
import re
import paramiko
import time
from http import HTTPStatus
from skills_python import robot_info

"""The function primarily serves the following purposes: it adds a new skill to the system through interactive user input.
The process involves constructing tool descriptions, prompting the user for skill information, repeatedly attempting to extract and validate the skill function name from user responses, 
and based on the extracted results, uploading the file, updating initialization configurations, and incorporating the skill into an embedded model. 
If extraction is successful, the skill is added successfully; if extraction fails, it rectifies the input based on error messages and indicates a failed addition attempt."""


def reset():
    """restart the gazebo simulation environment"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh.connect(
        hostname="192.168.0.148", port=22, username="sony", password="sony", timeout=10
    )
    invoke = ssh.invoke_shell()
    invoke.send("rosservice call /gazebo/reset_simulation \n")
    time.sleep(3)
    ssh.close()


def generate_para(task, func_desc):
    para_generated_prompt = PARA_GENERATED_PROMPT.format(task=task, func_desc=func_desc)
    messages_prompt = [
        {
            "role": Role.SYSTEM,
            "content": "You are a helpful assistant that writes json code.",
        },
        {"role": Role.USER, "content": para_generated_prompt},
    ]
    response = Generation.call(
        # Generation.Models.qwen_max,
        model="qwen-max-1201",
        messages=messages_prompt,
        result_format="message",  # set the result to be "message" format.
        temperature=0,
    )

    para_resp = response.output.choices[0]["message"]["content"]
    print(para_resp)
    para_json = re.search(r"```json(.*?)```", para_resp, re.DOTALL)
    para_json = json.loads(para_json.group(1).strip())
    return para_json


def learn_new_skill(prompt, messages):
    if messages == []:
        messages.append(
            {
                "role": Role.SYSTEM,
                "content": "You are a helpful assistant that writes python and json code.",
            }
        )
        messages.append({"role": Role.USER, "content": prompt})
    response = Generation.call(
        # Generation.Models.qwen_max,
        model="qwen-max-1201",
        messages=messages,
        result_format="message",  # set the result to be "message" format.
        temperature=0,
    )
    if response.status_code == HTTPStatus.OK:
        messages.append(
            {
                "role": response.output.choices[0]["message"]["role"],
                "content": response.output.choices[0]["message"]["content"],
            }
        )
    return response.output.choices[0]["message"]["content"]


def extract_json_python(task, response):
    json_match = re.search(r"```json(.*?)```", response, re.DOTALL)
    json_content = json_match.group(1).strip()

    # 提取 Python 代码部分
    python_match = re.search(r"```python(.*?)```", response, re.DOTALL)
    python_code = python_match.group(1).strip()

    print("JSON 内容：")
    print(json_content)
    try:
        func_name = json.loads(json_content)[0].get("name_for_model")
    except:
        func_name = json.loads(json_content).get("name_for_model")
    print("func_name:", func_name)

    print("\nPython 代码：")
    print(python_code)

    try:
        info = json.loads(json_content)[0]
    except:
        info = json.loads(json_content)
    new_skill_desc = TOOL_DESC.format(
        name_for_model=info["name_for_model"],
        name_for_human=info["name_for_human"],
        description_for_model=info["description_for_model"],
        parameters=json.dumps(info["parameters"], ensure_ascii=False),
    )

    flag = True
    try:
        run_error = None
        exec(python_code)
    except Exception as e:
        run_error = str(e)
        print("There are syntax errors in python_code")
        flag = False

    para_json = generate_para(task, new_skill_desc)

    try:
        reset()

        exec("""{func_name}(**{para})""".format(func_name=func_name, para=para_json))

        verification_result = self_verification(task)
        if verification_result.get("success"):
            pass
        else:
            print("There are logic errors in python_code")
            flag = False
    except Exception as e:
        run_error = str(e)
        verification_result = "Due to a running error, the scene change after the program is finished cannot be seen"
        print("There are syntax errors in python_code")
        flag = False

    if flag == True:
        with open(
            "./skills_desc/{func_name}.txt".format(func_name=func_name), "w"
        ) as txt_file:
            txt_file.write(new_skill_desc)

        with open(
            "./skills_python/{func_name}.py".format(func_name=func_name), "w"
        ) as python_file:
            python_file.write(python_code)

    return func_name, flag, run_error, verification_result


def upload_file(func_name):
    test_files = {
        "{func_name}.txt".format(func_name=func_name): robot_info.Local_Path
        + "skills_desc\\{func_name}.txt".format(func_name=func_name)
    }
    files = [("files", (name, open(path, "rb"))) for name, path in test_files.items()]
    data = {"knowledge_base_name": "skill_library", "override": True}
    r = requests.post(
        robot_info.Langchain_chatchat_API + "knowledge_base/upload_docs",
        data=data,
        files=files,
    )
    print(r)


def add_to_init(func_name):
    package_name = "skills_python"
    # 要添加到 __init__.py 文件的代码
    code_to_add = """
    from .{func_name} import {func_name}
    """.format(
        func_name=func_name
    )
    # 指定要编辑的 __init__.py 文件路径
    init_file_path = f"{package_name}/__init__.py"

    # 以追加模式打开 __init__.py 文件，并写入新的代码
    with open(init_file_path, "r") as file:
        file_content = file.read()
        if code_to_add in file_content:
            print("Code already exists in __init__.py. Aborting addition.")
        else:
            # 以追加模式打开 __init__.py 文件，并写入新的代码
            with open(init_file_path, "a") as file:
                file.write(code_to_add)
                file.write("\n")
            print("Code added to __init__.py successfully.")


def add_to_embedding(func_name):
    keywords_path = robot_info.Langchain_chatchat_embedding_Path
    # 读取文件内容并检查是否已经存在 func_name
    with open(keywords_path, "r") as file:
        lines = file.readlines()
        if (func_name + "\n") in lines:
            print(f"{func_name} already exists in the embedding_keywords.txt. Abort.")
        else:
            # 在文件末尾添加 func_name
            with open(keywords_path, "a") as file:
                file.write(func_name + "\n")

            print(f"{func_name} added to the embedding_keywords.txt.")


def rectify_py(messages, run_error, verification_result):
    rectify_prompt = RECTIFY_PROMPT.format(
        run_error=run_error, verification_result=verification_result
    )
    messages.append(
        {
            "role": Role.USER,
            "content": rectify_prompt,
        }
    )


def add_skill(task, response_all):
    messages = []
    used_tools = re.findall(r"Action: (.*)", response_all)
    tool_name, tool_descs = construct_tool_descs(
        withparameter=True, integrated_tools=True, given_tools=used_tools
    )
    skill_prompt = SKILL_PROMPT.format(tool_descs=tool_descs, response_all=response_all)
    for i in range(3):
        response = learn_new_skill(skill_prompt, messages)
        func_name, flag, run_error, verification_result = extract_json_python(
            task, response
        )
        if flag:
            upload_file(func_name)
            add_to_init(func_name)
            add_to_embedding(func_name)
            print("Success to add")
            break
        else:
            print("Fail to add")
            rectify_py(messages, run_error, verification_result)
