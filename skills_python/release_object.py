import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from robot_connect import robot


def release_object(robot_info):
    def release_object(*args, **kwargs):
        data = {
            "enable": 1,
            "width": 0,
            "depth": 0,
        }
        # response = requests.post(
        #     "http://192.168.0.148:23915/control_gripper", data=data
        # ).content
        response = robot.control_gripper(data)
        print(response)
        robot_info.grabbed_objects.clear()
        return "Success release object."

    return release_object


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
