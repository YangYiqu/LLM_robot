import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from robot_connect import robot


# current_loc, grabbed_objects, known_dict
def move_to_coordinates(robot_info):
    def move_to_coordinates(x, y, z):

        if len(robot_info.grabbed_objects) == 0:
            pass
        else:
            for item in robot_info.grabbed_objects:
                robot_info.known_dict.update({item: (x, y, z)})
        known_object_loc = (x, y, z)
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
            "Success move to ("
            + str(x)
            + ","
            + str(y)
            + ","
            + str(z)
            + ")"
            + ", and is grabbing "
            + str(robot_info.grabbed_objects)
        )

    return move_to_coordinates


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
