import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from _basic_info import CRITIC_PROMPT
from pprint import pprint
import json
import re
from dashscope import Generation
from dashscope import MultiModalConversation
from dashscope.api_entities.dashscope_response import Role
import base64
import cv2
import numpy as np
import requests
from robot_connect import robot


def self_verification(task):
    """
    A self-validation function that takes an image from a given task and verifies it using a multimodal dialogue model.

    Parameters:
    - task: str, a task description, which is used to generate authentication prompts.

    Back:
    - verification_result: dict: dictionary containing verification results.
    """
    critic_prompt = CRITIC_PROMPT.format(task=task)
    try:
        image = robot.get_rgbimage()
        cv2.imwrite("../assets/2.jpg", image)

    except:
        print("Reading image error!")
    messages = [
        {
            "role": Role.USER,
            "content": [
                {"image": "file://C:/Users/MSI/Grounded-Segment-Anything/assets/2.jpg"},
                {"text": critic_prompt},
            ],
        }
    ]

    response = MultiModalConversation.call(
        model="qwen-vl-max",
        messages=messages,
        temperature=0,
    )

    resp = (
        response.output.choices[0]["message"]["content"][0]
        .get("text")
        .replace("\n", " ")
    )

    json_match = re.search(r"```json(.*?)```", resp, re.DOTALL)
    if json_match == None:
        json_content = resp
    else:
        json_content = json_match.group(1).strip()
    verification_result = json.loads(json_content)
    return verification_result
