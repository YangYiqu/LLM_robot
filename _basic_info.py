from http import HTTPStatus
import dashscope
from dashscope import Generation
from dashscope.api_entities.dashscope_response import Role
import random
import json
import requests
import time
import urllib.parse
import re
import cv2
import numpy as np
import base64
import json
import os

"""store some basic information, function, and prompts"""

dashscope.api_key = "sk-1be100540ecd47a986e38fca4d1d149c"

basic_tools = [
    "search_object",
    "grab_object",
    "move_to_object",
    "move_to_coordinates",
    "release_object",
]
TOOL_DESC = """{name_for_model}: Call this tool API to control the robot. What is the {name_for_human} API useful for? {description_for_model} Parameters: {parameters} Format the arguments as a JSON object."""

REACT_PROMPT = """You are an embodied AI assistant that controls a robot and interacts with the user. You have strong reasoning skills. You have access to the following existing tools (Integrated toola and basic tools):

{tool_descs}

Instruction:

1.If you can find suitable ##integrated tools##, use it preferentially with high priority!
2.If you can't find the suitable ##integrated tools## to streamline tasks quickly and want to move object a to object b, you can use the ##basic tool##:
    - You must search a, move to a, and then must grab a. Then search b, move to b, and then release a. (You don't have to go back to your original position and no further action on a and b.)
3.If you try to find certain object several times and don't find it:
    - You can change your thought or give up

Attention:
When you want to grab_object, you must choose the corresponding suitable tableware.
For ["chair","desk","plate"...], you can use 'hand'.
For ['soup','drinks'...], you can use 'spoon'.
For ['Fruit chunk','steak'...], you can use 'fork'
...

Use the following format:

Status: the current status of the robot
Environment: objects that appear in current surroundings
Task: the input task you must accomplish
Thought: you should always think about what to do based on current environment. ##Integrated tools## are prioritized for use.
Action: the action to take, should be one of {tool_names}.
Action Input: the input to the action. 
Observation: the result of the action
... (this Thought/Action/Action Input/Observation/Status/Environment can be repeated zero or more times)
Thought: The task has accomplished
Final Response: the final response to the user after you finish the task.

Begin!

Status: Robot is grabing nothing.
Environment: {environment}
Task: {query}
"""

SKILL_PROMPT = """You are an embodied AI assistant that controls a robot and interacts with the user. You are a helpful assistant that writes python code and json file. Now You have access to the following existing tools:

{tool_descs}

Given the previous thought procedure:

{response_all}.

Can you gain a new tool from the previous thought procedure by combining the existing tools? The new tool should be represented by a python function. It should be easily generalizable. It should import necessary packages and existing tool api functions.
These tool api functions are in the skills_python. You can use "from skills_python import " to import them. The function parameter should use "Keyword Arguments" format.**Not json format**. We can not assume any return of existing tool api functions.

You should answer with a python function (it should be executable) and the JSON format description for the function (it should be valid when using python `json.dump` and should be clear and unambiguous).

Python function:
def function_name(parameter1,parameter2,...):
    ...
    (No return)

JSON format description:
["name_for_human": "function_name",
"name_for_model": "function_name",
"description_for_model": ,
"parameters": 
            "name": ,
            "type": ,
            "description": ,
            "required": , 

"tool_api": "tool_wrapper_for_qwen(function_name)"]

Note: 1. function_name should be the same with python function name totally. Name your new function in a meaningful way (can infer the aim from the name and don't have ambiguity)
2. We should make sure that "tool_api": "tool_wrapper_for_qwen(function_name)" such as "tool_api": "tool_wrapper_for_qwen(search_object)"
3."description_for_model" should describe each step and results in as much detail as possible.
4. If you need to move to *a*, you must search *a* first to know *a*'s location.
"""

CRITIC_PROMPT = """You are an assistant that assesses the progress of manipulation robot and provides useful guidance.
You are required to evaluate if I have met the task requirements. Exceeding the task requirements is also considered a success, while failing to meet them requires you to provide critique to help me improve.
If you find that this is an intermediate step, it is also a failure.
I will give you the following information:
Task: {task}

You should combine the image information (the object showed in the image and their positional relationship) and only respond in JSON format(No additional information) as described below:
{{"description": A concrete description of the image content,
"reasoning": "reasoning",
"success": boolean,
"critique": "critique"}}
Ensure the response in ```json ``` and can be parsed by Python `json.loads`, e.g.: no trailing commas, no single quotes, etc.

Here are some examples:
INPUT:
Task: Open the refrigerator and grab the apple to the table.

RESPONSE:
{{"description": "In the left is an openned refrigerator and in the right there is a table with an apple on it.",
"reasoning": "The image shows the refrigerator is open and the apple is on the table",
"success": true,
"critique": ""}}

INPUT:
Task: Please feed the cherry tomato into the mouth.

RESPONSE:
{{"description": "There is a plate of cherry tomato on the table, and the empty spoon is near the mouth."
"reasoning": "You need to grab the cherry tomato, but The image shows that you failed to grab it by spoon",
"success": false,
"critique": "You can change the table ware to improve the success probabilty, such as fork"}}
"""

DECOMPOSITION_PROMPT = """You are a helpful assistant that generates a curriculum of subgoals to complete task specified by me.

I'll give you a final task and my current tools, you need to decompose the task into a list of subgoals based on my tools.

You must follow the following criteria:
1) Return a Python list of subgoals that can be completed in order to complete the specified task.
2) Each subgoal should be able to be accomplished by single tool.
3) The amount of subgoals should be as small as possible. Such as if you have an integrated tool, you can directly use it to accomplish the subgoal, you don't need to decompose further.

You should only respond in JSON format as described below:
["subgoal1", "subgoal2", "subgoal3", ...]
Ensure the response can be parsed by Python `json.loads`, e.g.: no trailing commas, no single quotes, etc.

Input:
final task: {task}
current tools: {tools}"""

RELATED_SKILL_PROMPT = """You are a helpful assistant that find the useful tool to complete task specified by me.

I'll give you a final task and my current tools, you need to decide which tools we should use to complete the specified task based on my current tools.

You must follow the following criteria:
1) Return a Python list of chosen tools in order to complete the specified task.
2) The chosen tools should not have duplicate values.
3) The amount of chosen tools should be as small as possible. Such as if you have an integrated tool, you can directly use it to accomplish the subgoal, you don't need to decompose further.
4) If you need to move to *a*, you must search *a* first to know *a*'s location.
5) If you need to grab *a*, you must move to *a* first

You should only respond in JSON format as described below:
["tool1", "tool2", "tool3", ...]
Ensure the response can be parsed by Python `json.loads`, e.g.: no trailing commas, no single quotes, etc.

Input:
final task: {task}
current tools: {tools}"""

PARA_GENERATED_PROMPT = """You are a helpful assistant that specializes in helping functions generate relevant parameter values based on function descriptions and target tasks

Input:
The target task: {task}
function description: {func_desc}

Output(it should be json format):
{{parameter_name1: value1,
parameter_name2: value2,
...}}
Ensure the response can be parsed by Python `json.loads`, e.g.: no trailing commas, no single quotes, etc.
"""

QUERY_REWRITE_PROMPT = """You are a helpful assistant that are good at rewriting the query to make the specific task become a general one.

Instruction:
1. Extract specific actions, ignore polite expressions or the content that have nothing to do with robot tasks, and rewrite the questions as declarative sentences.
2. The overwritten query cannot display the specific item name, which should be replaced by pseudonym pronouns, such as object, item, target, desitination, place ...
3. You should distinguish different objects by assigning a different pseudonym pronouns or using serial number such as item1,item2....
4. Verbs should have clear meaning and commonly used. The overwritten verbs should focus on the changing state of the object or the movement of the robot.
5. You are in a state of complete ignorance and that the rewritten query should be complemented with the potentially needed tasks

Example: 
query: Could you please feed the porriage into the mouth and get hold of the tissue?
rewritten query: move the object1 to the object2 and get item.

query: help me to take away the rubbish to the trash can.
rewritten query: move the item to the destination.

Let's begin!

Input: 
query: {query}

Output: 
rewritten query: rewrited query"""

RECTIFY_PROMPT = """There are errors when verify this newly generated python_function.

Run program error : {run_error}
Task completion failure : Tha analysis of the scenario after running the function is {verification_result}

You should correct and regenerate the python function and json description based on the above error feedback.
"""


def tool_wrapper_for_qwen(tool):
    def tool_(query):
        query = json.loads(query)
        return tool(**query)

    return tool_


def construct_tool_descs(withparameter=True, integrated_tools=True, given_tools=False):
    folder_path = "skills_desc"
    tool_descs = ""
    # 获取文件夹下所有txt文件的文件名
    if given_tools == False:
        txt_files = [file for file in os.listdir(folder_path) if file.endswith(".txt")]
        tool_name = [file[:-4] for file in txt_files]
    else:
        txt_files = [file + ".txt" for file in given_tools]
        tool_name = given_tools

    if integrated_tools == False:
        tool_name = basic_tools
        txt_files = [file + ".txt" for file in basic_tools]
    # 逐个读取txt文件内容并拼接

    for txt_file in txt_files:
        file_path = os.path.join(folder_path, txt_file)
        with open(file_path, "r") as file:
            content = file.read()
            if withparameter:
                tool_descs += content + "\n\n"
            else:
                new_content = content.split("Parameters: ")[0]
                tool_descs += new_content + "\n\n"

    # 输出拼接后的内容
    return tool_name, tool_descs

    # _______________________________________________________________________________________________________________________________________________________________
    # _____________________________The following part is only designed for the implementation of the main function in main.py.__________________________________________________

    # ______________________________________________________________________
    # known_dict = {}
    # obj_width_dict = {}
    # current_loc = [(1, 1, 1)]  # initial location
    # grabbed_objects = []
    # openned_containers = []
    # PRE_LOCATE_OBJECT_API = "http://127.0.0.1:9999/"
    # threshold = 0.4
    # ______________________________________________________________________

    # 1. search a suitable tableware.
    # 2. move to the suitable tableware.
    # 3. grab the suitable tableware by grab_suitable.
    # 3. search a.
    # 4. move to a.
    # 5. must grab a by grab_object.
    # 6. Then search b.
    # 7. move to b.
    # 8. release.
    # ______________________________________________________________________________________________

    # def img_decode(img_str, flag=cv2.IMREAD_ANYDEPTH):
    #     # flag: specify image type as cv.imread
    #     # img_str = requests.get(IMG_FET_API).content
    #     img_str = base64.b64decode(img_str)

    #     nparr = np.frombuffer(img_str, np.uint16)

    #     img = cv2.imdecode(nparr, flag)
    #     return img

    # def img_resize(image):
    #     height, width = image.shape[:2]
    #     crop_width = int((width - 960) / 2)
    #     cropped_image = image[:, crop_width : width - crop_width]

    #     new_width = int(960 / 1.5)
    #     new_height = int(height / 1.5)
    #     resized_image = cv2.resize(cropped_image, (new_width, new_height))
    #     return resized_image

    # def search_object(object_name):
    #     global known_dict, PRE_LOCATE_OBJECT_API, obj_width_dict, threshold
    #     loc = {}
    #     if object_name in known_dict.keys():
    #         loc = {object_name: known_dict.get(object_name)}
    #     else:
    #         text = urllib.parse.quote_plus(object_name)
    #         LOCATE_OBJECT_API = PRE_LOCATE_OBJECT_API + text
    #         retry = 0
    #         max_label = 0
    #         while retry < 3:
    #             # try:
    #             resp = requests.get(LOCATE_OBJECT_API, timeout=60)
    #             # print("API", resp.status_code)
    #             content = resp.content
    #             # except:
    #             #     print("Reading API error!")
    #             #     content = ""
    #             try:
    #                 img = img_decode(
    #                     requests.get(
    #                         "http://192.168.0.148:23915/depthimage", timeout=30
    #                     ).content
    #                 )
    #                 depthimage = img_resize(img)

    #             except:
    #                 depthimage = ""
    #                 print("Reading depth image error!")
    #             # if resp.status_code == 201:
    #             if (len(content) == 0) or (len(depthimage) == 0):
    #                 print("Waiting for coordinate data...")
    #                 time.sleep(1)
    #                 retry += 1
    #                 continue
    #             else:
    #                 # print("-----------" + str(content))
    #                 content = json.loads(content)
    #                 x = int(float(content.get("x")))
    #                 y = int(float(content.get("y")))
    #                 z = int(depthimage[y][x])
    #                 obj_width = {object_name: int(float(content.get("obj_width")))}

    #                 max_label = float(content.get("max_label"))
    #                 loc = {object_name: (x, y, z)}
    #                 break
    #         if max_label >= threshold:
    #             known_dict.update(loc)
    #             obj_width_dict.update(obj_width)
    #         else:
    #             return "The robot didn't find the target object."

    #     return loc

    # def grab_object(object_name, tableware_name="hand"):
    #     global known_dict, current_loc, grabbed_objects, obj_width_dict
    #     if (tableware_name != "hand") and (tableware_name not in grabbed_objects):
    #         return (
    #             "Fail to grab object, beacuse the robot haven't grabbed the corresponding tableware. You should move_to_object("
    #             + tableware_name
    #             + ") first and then grab_object("
    #             + tableware_name
    #             + "), then move back to "
    #             + object_name
    #             + ", grab_object("
    #             + object_name
    #             + ","
    #             + tableware_name
    #             + ")"
    #         )
    #     elif current_loc[0] == known_dict.get(object_name) and random.random() < 0.9:
    #         grabbed_objects.append(object_name)
    #         obj_width = obj_width_dict.get(object_name)
    #         data = {
    #             "enable": 0,
    #             "width": obj_width,
    #             "depth": known_dict.get(object_name)[2],
    #         }
    #         print(data)
    #         response = requests.post(
    #             "http://192.168.0.148:23915/control_gripper", data=data
    #         ).content
    #         print(response)
    #         # rpc('func_name', params: ['type', 'value', ...])
    #         return "Success grab object: " + object_name + " by " + tableware_name
    #     elif current_loc[0] != known_dict.get(object_name):
    #         return (
    #             "Fail to grab object, the robot is in a wrong location, you can choose to 1. move to the "
    #             + object_name
    #             + " by move_to_object tool and then grab_object("
    #             + object_name
    #             + "or 2. you should review the task and change the thought to move to the right location"
    #         )
    #     else:
    #         return (
    #             "Fail to grab object, please try to grab it again by using grab_object("
    #             + object_name
    #             + ")"
    #         )

    # def move_to_object(object_name):
    #     global known_dict, current_loc, grabbed_objects

    #     if object_name in known_dict.keys():
    #         known_object_loc = known_dict.get(object_name)
    #         if len(grabbed_objects) == 0:
    #             pass
    #         else:
    #             for item in grabbed_objects:
    #                 known_dict.update({item: known_object_loc})
    #         data = {
    #             "x": known_object_loc[0],
    #             "y": known_object_loc[1],
    #             "z": known_object_loc[2],
    #         }
    #         response = requests.post(
    #             "http://192.168.0.148:23915/move_arm_position", params=data
    #         ).content
    #         print(response)
    #         current_loc[0] = known_object_loc
    #         return (
    #             "Success move, move to "
    #             + str(known_object_loc)
    #             + ", and is grabbing "
    #             + str(grabbed_objects)
    #         )
    #     else:
    #         return (
    #             "Fail to move because don't know the coordinates of the object. Please find the location by search_object("
    #             + object_name
    #             + ") first "
    #         )

    # def move_to_coordinates(x, y, z):
    #     global current_loc, grabbed_objects, known_dict

    #     if len(grabbed_objects) == 0:
    #         pass
    #     else:
    #         for item in grabbed_objects:
    #             known_dict.update({item: (x, y, z)})
    #     known_object_loc = (x, y, z)
    #     data = {
    #         "x": known_object_loc[0],
    #         "y": known_object_loc[1],
    #         "z": known_object_loc[2],
    #     }
    #     response = requests.post(
    #         "http://192.168.0.148:23915/move_arm_position", params=data
    #     ).content
    #     print(response)
    #     current_loc[0] = known_object_loc
    #     return (
    #         "Success move to ("
    #         + str(x)
    #         + ","
    #         + str(y)
    #         + ","
    #         + str(z)
    #         + ")"
    #         + ", and is grabbing "
    #         + str(grabbed_objects)
    #     )

    # def release_object(param={}):
    #     global grabbed_objects
    #     data = {
    #         "enable": 1,
    #         "width": 0,
    #         "depth": 0,
    #     }
    #     response = requests.post(
    #         "http://192.168.0.148:23915/control_gripper", data=data
    #     ).content
    #     print(response)
    #     grabbed_objects.clear()
    #     return "Success release object."

    # def open_container(container_name):
    #     global known_dict, grabbed_objects, current_loc, openned_containers
    #     if container_name in openned_containers:
    #         return (
    #             "The robot has openned the "
    #             + container_name
    #             + "before, you should try other containers."
    #         )
    #     elif current_loc[0] == known_dict.get(container_name) and random.random() < 0.95:
    #         openned_containers.append(container_name)
    #         return (
    #             "Success open container: "
    #             + container_name
    #             + ", Please search the target object by search_object tool again"
    #         )
    #     elif current_loc[0] != known_dict.get(container_name):
    #         return (
    #             "Fail to open container, the robot is in a wrong location, you can choose to 1. move to the "
    #             + container_name
    #             + " by move_to_object tool or 2. you should review the task and change the thought to move to the right location"
    #         )
    #     else:
    #         return (
    #             "Fail to open container, please try to open it again, using open_container("
    #             + container_name
    #             + ")"
    #         )

    # # ______________________________________________________________________________________________
    # TOOLS = [
    #     {
    #         "name_for_human": "search_object",
    #         "name_for_model": "search_object",
    #         "description_for_model": "Robot will get the location of queried object at the robot's current location. The location is described by x,y and z coordinates.",
    #         "parameters": [
    #             {
    #                 "name": "object_name",
    #                 "type": "string",
    #                 "description": "the name of object to search",
    #                 "required": True,
    #             }
    #         ],
    #         "tool_api": tool_wrapper_for_qwen(search_object),
    #     },
    #     {
    #         "name_for_human": "grab_object",
    #         "name_for_model": "grab_object",
    #         "description_for_model": "Robot will grab the object at the robot's current location in order to take or move the object",
    #         "parameters": [
    #             {
    #                 "name": "object_name",
    #                 "type": "string",
    #                 "description": "the name of object the robot should grab",
    #                 "required": True,
    #             },
    #             {
    #                 "name": "tableware_name",
    #                 "type": "string",
    #                 "description": "the suitable tableware to grab corresponding object. The default is 'hand'. ",
    #                 "required": True,
    #             },
    #         ],
    #         "tool_api": tool_wrapper_for_qwen(grab_object),
    #     },
    #     {
    #         "name_for_human": "move_to_object",
    #         "name_for_model": "move_to_object",
    #         "description_for_model": "Move the robot with the grabbed_item to the object, whose coordinates should be found by 'search_object' first",
    #         "parameters": [
    #             {
    #                 "name": "object_name",
    #                 "type": "string",
    #                 "description": "the name of object to the robot should move to",
    #                 "required": True,
    #             },
    #         ],
    #         "tool_api": tool_wrapper_for_qwen(move_to_object),
    #     },
    #     {
    #         "name_for_human": "move_to_coordinates",
    #         "name_for_model": "move_to_coordinates",
    #         "description_for_model": "Move the robot with the grabbed_item to specified coordinates. Only when the task contains specific coordinates, this action can be called",
    #         "parameters": [
    #             {
    #                 "name": "x",
    #                 "type": "integer",
    #                 "description": "the x-coordinate of the destination.",
    #                 "required": True,
    #             },
    #             {
    #                 "name": "y",
    #                 "type": "integer",
    #                 "description": "the y-coordinate of the destination.",
    #                 "required": True,
    #             },
    #             {
    #                 "name": "z",
    #                 "type": "integer",
    #                 "description": "the z-coordinate of the destination.",
    #                 "required": True,
    #             },
    #         ],
    #         "tool_api": tool_wrapper_for_qwen(move_to_coordinates),
    #     },
    #     {
    #         "name_for_human": "release_object",
    #         "name_for_model": "release_object",
    #         "description_for_model": "Release the grabbed objects at the robot's current location. Only if you make sure the current location is the final location to put the grabbed objects, this action can be called。The Action Input should be: \{\}",
    #         "parameters": [
    #             {
    #                 # "name": "object_name",
    #                 # "type": "string",
    #                 # "description": "the name of object to the robot will release",
    #                 # "required": False,
    #             },
    #         ],
    #         "tool_api": tool_wrapper_for_qwen(release_object),
    #     },
    #     {
    #         "name_for_human": "open_container",
    #         "name_for_model": "open_container",
    #         "description_for_model": "Robot will open the container at the robot's current location in order to 1. find if the target object is in the container,or 2. place the target object inside the container",
    #         "parameters": [
    #             {
    #                 "name": "container_name",
    #                 "type": "string",
    #                 "description": "the name of container the robot should open",
    #                 "required": True,
    #             },
    #         ],
    #         "tool_api": tool_wrapper_for_qwen(open_container),
    #     },
    # ]

    # def build_planning_prompt(TOOLS, query, env):
    tool_descs = []
    tool_names = []
    for info in TOOLS:
        if info["name_for_model"] in basic_tools:
            tool_descs.append(
                "##Basic tool## "
                + TOOL_DESC.format(
                    name_for_model=info["name_for_model"],
                    name_for_human=info["name_for_human"],
                    description_for_model=info["description_for_model"],
                    parameters=json.dumps(info["parameters"], ensure_ascii=False),
                )
            )
        else:
            tool_descs.append(
                "##Intergrated tool## "
                + TOOL_DESC.format(
                    name_for_model=info["name_for_model"],
                    name_for_human=info["name_for_human"],
                    description_for_model=info["description_for_model"],
                    parameters=json.dumps(info["parameters"], ensure_ascii=False),
                )
            )
        tool_names.append(info["name_for_model"])
    # ___________________________________________________________________________
    # 将数据写入文件
    # for i, tool in enumerate(tool_descs):
    #     func_name = tool_names[i]
    #     with open(
    #         "previous_llm_yyq\\skills_desc\\\{func_name}.txt".format(func_name=func_name),
    #         "w",
    #         encoding="utf-8",
    #     ) as file:
    #         file.write(tool)
    #     print("数据已保存到本地文件。")
    # ————————————————————————————————————————————————————————————————————————————
    tool_descs = "\n\n".join(tool_descs)
    # print(tool_descs)
    prompt = REACT_PROMPT.format(
        tool_descs=tool_descs, tool_names=tool_names, query=query, environment=env
    )
    return prompt
