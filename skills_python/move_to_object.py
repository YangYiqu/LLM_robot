import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from robot_connect import robot

# class Variable: known_dict, current_loc, grabbed_objects


def move_to_object(robot_info):
    def move_to_object(object_name):
        if object_name in robot_info.known_dict.keys():
            known_object_loc = robot_info.known_dict.get(object_name)
            if len(robot_info.grabbed_objects) == 0:
                pass
            else:
                for item in robot_info.grabbed_objects:
                    robot_info.known_dict.update({item: known_object_loc})
            data = {
                "x": known_object_loc[0],
                "y": known_object_loc[1],
                "z": known_object_loc[2],
            }
            # response = requests.post(
            #     "http://192.168.0.148:23915/move_arm_position", params=data
            # ).content
            response = robot.move_arm_position(data)
            print(response)
            robot_info.current_loc[0] = known_object_loc
            return (
                "Success move, move to "
                + str(known_object_loc)
                + ", and is grabbing "
                + str(robot_info.grabbed_objects)
            )
        else:
            return (
                "Fail to move because don't know the coordinates of the object. Please find the location by search_object("
                + object_name
                + ") first "
            )

    return move_to_object


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
