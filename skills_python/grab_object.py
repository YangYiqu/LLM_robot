import random
import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from robot_connect import robot


def grab_object(robot_info):
    def grab_object(object_name, tableware_name="hand"):

        if (tableware_name != "hand") and (
            tableware_name not in robot_info.grabbed_objects
        ):
            return (
                "Fail to grab object, beacuse the robot haven't grabbed the corresponding tableware. You should move_to_object("
                + tableware_name
                + ") first and then grab_object("
                + tableware_name
                + "), then move back to "
                + object_name
                + ", grab_object("
                + object_name
                + ","
                + tableware_name
                + ")"
            )
        elif (
            robot_info.current_loc[0] == robot_info.known_dict.get(object_name)
            and random.random() < 0.9
        ):
            robot_info.grabbed_objects.append(object_name)
            obj_width = robot_info.obj_width_dict.get(object_name)
            data = {
                "enable": 0,
                "width": obj_width,
                "depth": robot_info.known_dict.get(object_name)[2],
            }
            print(data)
            response = robot.control_gripper(data)
            print(response)
            return "Success grab object: " + object_name + " by " + tableware_name
        elif robot_info.current_loc[0] != robot_info.known_dict.get(object_name):
            return (
                "Fail to grab object, the robot is in a wrong location, you can choose to 1. move to the "
                + object_name
                + " by move_to_object tool and then grab_object("
                + object_name
                + "or 2. you should review the task and change the thought to move to the right location"
            )
        else:
            return (
                "Fail to grab object, please try to grab it again by using grab_object("
                + object_name
                + ")"
            )

    return grab_object


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
