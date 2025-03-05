from http import HTTPStatus
from pprint import pprint
import json
from dashscope import Generation
from dashscope import MultiModalConversation
from dashscope.api_entities.dashscope_response import Role

# from _basic_info import TOOLS, TOOL_DESC,REACT_PROMPT, build_planning_prompt, known_dict,openned_containers,grabbed_objects,tool_wrapper_for_qwen,construct_tool_descs,basic_tools
from _basic_info import (
    REACT_PROMPT,
    tool_wrapper_for_qwen,
    construct_tool_descs,
    basic_tools,
)

# from _basic_info import build_planning_prompt, build_planning_prompt2,tool_wrapper_for_qwen,REACT_PROMPT
from basic_func.related_skill import related_skill
from basic_func.query_rewrite import query_rewrite
from skills_python import robot_info
import requests
import ast
import cv2
import base64
import numpy as np
import time
from typing import Dict, Tuple
import re
import os
from robot_connect import robot
from threading import Thread
from queue import Queue
from collections import defaultdict

os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

"""
1.`main` is the original one which uses only the tools defined in test react.py
2.`main2` uses the tool in the self-defined module skills_python, text similarity matching in the vector database is used when filtering task-related tools
3.`main3` uses the tool in the self-defined module skills_python, llm is used to filter the tools that a task might use
"""


def parse_latest_plugin_call(text: str) -> Tuple[str, str]:
    i = text.rfind("\nAction:")
    j = text.rfind("\nAction Input:")
    k = text.rfind("\nObservation:")
    if 0 <= i < j:  # If the text has `Action` and `Action input`,
        if k < j:  # but does not contain `Observation`,
            # then it is likely that `Observation` is ommited by the LLM,
            # because the output text may have discarded the stop word.
            text = text.rstrip() + "\nObservation:"  # Add it back.
            k = text.rfind("\nObservation:")
    if 0 <= i < j < k:
        plugin_name = text[i + len("\nAction:") : j].strip()
        plugin_args = text[j + len("\nAction Input:") : k].strip()
        return plugin_name, plugin_args
    return "", ""


def use_api_from_skills_python(tool_names, response):
    use_toolname, action_input = parse_latest_plugin_call(response)
    if use_toolname == "":
        return f"No such action founds, The action should be changed to one of the {tool_names}"
    if use_toolname not in tool_names:
        return f"No such action founds, The action should be changed to one of the {tool_names}"
    try:
        eval("tool_wrapper_for_qwen({use_toolname})".format(use_toolname=use_toolname))
    except NameError as e:
        exec(f"from skills_python import {use_toolname}")
    if use_toolname in basic_tools:
        api_output = tool_wrapper_for_qwen(eval(use_toolname))(action_input)
        return api_output
    else:
        tool_wrapper_for_qwen(eval(use_toolname))(action_input)
        return "Success accomplish " + use_toolname + " with " + action_input


def search_relevent_api(query):
    tool_descs = []
    tool_names = []
    api_base_url = robot_info.Langchain_chatchat_API
    api = "knowledge_base/search_docs"
    url = api_base_url + api
    r = requests.post(
        url,
        json={
            "knowledge_base_name": "skill_library",
            "query": query,
            "top_k": 3,
            "score_threshold": 0.6,
        },
    )
    data = r.json()
    for tool in data:
        if tool["metadata"]["source"][:-4] in basic_tools:
            tool_descs.append("##Basic tool## " + tool["page_content"])
        else:
            tool_descs.append("##Integrated tool## " + tool["page_content"])
        tool_names.append(tool["metadata"]["source"][:-4])
    tool_descs = "\n\n".join(tool_descs)
    return tool_names, tool_descs


def generate_env():
    global environment, finish_flag
    while finish_flag != True:
        try:
            image = robot.get_rgbimage()

            cv2.imwrite("../assets/1.jpg", image)

        except:
            print("Reading image error!")
        messages = [
            {
                "role": Role.USER,
                "content": [
                    {
                        "image": "file://C:/Users/MSI/Grounded-Segment-Anything/assets/1.jpg"
                    },
                    {
                        "text": """
                            Tasks: 
                            Describe the all the objects that appear in the image
                
                            Using the following Output format:
                            The image shows ...
                            
                            Begin!"""
                    },
                ],
            }
        ]

        response = MultiModalConversation.call(
            model="qwen-vl-plus",
            messages=messages,
            temperature=0,
        )
        envi = (
            response.output.choices[0]["message"]["content"][0]
            .get("text")
            .replace("\n", " ")
        )
        i = envi.rfind("The image shows")
        environment = envi[i + len("The image shows") :].strip()
        if finish_flag == True:
            pass
        else:
            time.sleep(30)


def logical_reasoning(prompt_1, response_all, result_queue, tool_names):
    global finish_flag
    stop = ["Observation:", "Observation:\n"]

    messages = [
        {
            "role": Role.SYSTEM,
            "content": "You are an embodied AI assistant that controls a robot and interacts with the user.",
        },
        {"role": Role.USER, "content": prompt_1},
    ]
    grab = False
    grabbed_name = []

    while True:
        response = Generation.call(
            # Generation.Models.qwen_max,
            model="qwen-max-1201",
            messages=messages,
            result_format="message",  # set the result to be "message" format.
            stop_tokens=stop,
            temperature=0,
        )

        if response.status_code == HTTPStatus.OK:
            resp = response.output.choices[0]["message"]["content"]
            messages.append(
                {
                    "role": response.output.choices[0]["message"]["role"],
                    "content": response.output.choices[0]["message"]["content"],
                }
            )
            print(resp)
            response_all.append(resp)
        else:
            print(
                "Request id: %s, Status code: %s, error code: %s, error message: %s"
                % (
                    response.request_id,
                    response.status_code,
                    response.code,
                    response.message,
                )
            )
            break

        if response.output.choices[0].finish_reason != "stop":
            break
        if "Final Response" in resp:
            break
        if "Final response" in resp:  # unstable
            break
        # all_tool_names,all_tools_decs=construct_tool_descs()
        api_output = use_api_from_skills_python(tool_names, resp)
        response_all.append("API output: " + api_output)
        print("API output:", api_output)
        print("________________________________________________________________")
        response_all.append(
            "________________________________________________________________"
        )

        try:
            if api_output.startswith("Success grab tableware"):
                grab = True
                grabbed_name.append(api_output.split(":")[1].strip())
            if api_output.startswith("Success grab object"):
                grab = True
                grabbed_name.append(api_output.split(":")[1].strip())
        except:
            pass

        try:
            if api_output.startswith("Success release object"):
                grab = False
                grabbed_name.clear()
        except:
            pass

        if not grab:
            status = "Status: Robot is grabing nothing."
        else:
            status = "Status: Robot is grabing " + str(grabbed_name)
        print(status)
        print("Environment: " + environment)
        response_all.append("Environment: " + environment)
        messages.append(
            {
                "role": Role.USER,
                "content": "Observation: {obs}\n{status}\nEnvironment: {environment}\nAnswer further according to the environment and state".format(
                    status=status, environment=environment, obs=json.dumps(api_output)
                ),
            }
        )

    print("Final Response:", resp)
    finish_flag = True
    result_queue.put(robot_info.known_dict)


def main(task, result_queue, response_all):
    """
    Using basic tools.
    """
    global environment, finish_flag
    print("Task:", task)
    response_all.append("Task:" + task)
    print("Initial env:", environment)
    tool_names, tool_descs = construct_tool_descs(
        withparameter=True, integrated_tools=False
    )
    prompt_1 = REACT_PROMPT.format(
        tool_descs=tool_descs,
        tool_names=tool_names,
        query=task,
        environment=environment,
    )
    logical_reasoning(prompt_1, response_all, result_queue, tool_names)


def main2(task, result_queue, response_all):
    """
    Using tools that defined in skills_python
    choose related tools by langchain_chatchat vector library
    """
    global environment, finish_flag
    print("Task:", task)
    response_all.append("Task:" + task)
    print("Initial env:", environment)
    query = query_rewrite(task)
    tool_names, tool_descs = search_relevent_api(query)
    # tool_names = read_embedding_keywords(robot_info.Langchain_chatchat_embedding_Path)
    prompt_1 = REACT_PROMPT.format(
        tool_descs=tool_descs,
        tool_names=tool_names,
        query=task,
        environment=environment,
    )
    logical_reasoning(prompt_1, response_all, result_queue, tool_names)


def main3(task, result_queue, response_all):
    """
    Using tools that defined in skills_python
    choose related tools by llm (related_skill.py)
    """
    global environment, finish_flag
    print("Task:", task)
    response_all.append("Task:" + task)
    print("Initial env:", environment)
    tool_names, tool_descs = related_skill(task)
    prompt_1 = REACT_PROMPT.format(
        tool_descs=tool_descs,
        tool_names=tool_names,
        query=task,
        environment=environment,
    )
    logical_reasoning(prompt_1, response_all, result_queue, tool_names)


if __name__ == "__main__":
    try:
        image = robot.get_rgbimage()

        cv2.imwrite("../assets/1.jpg", image)

    except:
        print("Reading image error!")
    messages = [
        {
            "role": Role.USER,
            "content": [
                {"image": "file://C:/Users/MSI/Grounded-Segment-Anything/assets/1.jpg"},
                {
                    "text": """
                        Tasks: 
                        Describe the all the objects that appear in the image
            
                        Using the following Output format:
                        The image shows 
                        
                        Begin!"""
                },
            ],
        }
    ]
    response = MultiModalConversation.call(
        model="qwen-vl-plus",
        messages=messages,
        temperature=0,
    )

    envi = (
        response.output.choices[0]["message"]["content"][0]
        .get("text")
        .replace("\n", " ")
    )
    i = envi.rfind("The image shows")
    environment = envi[i + len("The image shows") :].strip()

    finish_flag = False
    result_queue = Queue()
    response_all = []

    task = "move cola can to the plate"  # self-defined task for robot to accomplish
    t1 = Thread(
        target=main, args=(task, result_queue, response_all)
    )  # choose main/main2/main3
    t2 = Thread(target=generate_env)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    known_dict = result_queue.get()

    print(known_dict)
    reversed_dict = defaultdict(list)
    for key, value in known_dict.items():
        reversed_dict[value].append(key)

    # Find the set of keys with the same value
    result = [keys for keys in reversed_dict.values() if len(keys) > 1]
    print(result)

    response_all = "\n".join(response_all)
    print(response_all)
