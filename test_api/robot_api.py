import requests
import json

"""test for the gripper api of the robot"""

# data = {"x": 100, "y": 100, "z": 100}
# response = requests.post(
#     "http://192.168.0.148:23915/move_arm_position", params=data, timeout=30
# ).content
# print(response)

data = {
    "enable": 1,
    "width": 1,
    "depth": 1,
}
response = requests.post(
    "http://192.168.0.148:23915/control_gripper", data=data
).content
print(response)
