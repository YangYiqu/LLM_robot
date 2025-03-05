import requests
import urllib.parse
import cv2
import numpy as np
import base64
import json
import time
import sys
import os
import random

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from robot_connect import robot


def img_resize(image):
    height, width = image.shape[:2]
    crop_width = int((width - 960) / 2)
    cropped_image = image[:, crop_width : width - crop_width]

    new_width = int(960 / 1.5)
    new_height = int(height / 1.5)
    resized_image = cv2.resize(cropped_image, (new_width, new_height))
    return resized_image


def find_max_value_with_mask(mask, depth_image):
    # Converts mask to an indexed array
    indices = np.argwhere(mask)
    if len(indices) == 0:
        return None
    q1 = np.percentile(depth_image, 25)
    q3 = np.percentile(depth_image, 75)
    iqr = q3 - q1
    # 定义异常值上限和下限（假设为0.5倍的IQR）
    upper_bound = q3 + 0.5 * iqr
    lower_bound = q1 - 0.5 * iqr

    # 获取所有非异常值
    values = [
        depth_image[idx[0], idx[1]]
        for idx in np.argwhere(
            (depth_image >= lower_bound) & (depth_image <= upper_bound)
        )
    ]

    # 找到非异常值中的最大值
    max_value = max(values)
    # values = [depthimage[idx[0], idx[1]] for idx in indices]
    # max_value = max(values)
    return max_value


def search_object(robot_info):
    def search_object(object_name):
        loc = {}
        if object_name in robot_info.known_dict.keys():
            loc = {object_name: robot_info.known_dict.get(object_name)}
        else:
            text = urllib.parse.quote_plus(object_name)
            LOCATE_OBJECT_API = robot_info.PRE_LOCATE_OBJECT_API + text
            retry = 0
            max_label = 0
            while retry < 3:
                # try:
                if robot.use_robot:
                    resp = requests.get(LOCATE_OBJECT_API, timeout=60)
                    # print("API", resp.status_code)
                    content = resp.content
                    # except:
                    #     print("Reading API error!")
                    #     content = ""
                    try:
                        img = robot.get_depthimage()
                        print(img)
                        depthimage = img_resize(img)

                    except:
                        depthimage = img_resize(
                            cv2.imread(
                                robot_info.Local_Path + "data\\default_depth.png"
                            )[:, :, 0]
                        )
                        print("Reading depth image from gazebo error!")
                    # if resp.status_code == 201:
                    if (len(content) == 0) or (len(depthimage) == 0):
                        print("Waiting for coordinate data...")
                        time.sleep(1)
                        retry += 1
                        continue
                    else:
                        content = json.loads(content)
                        x = int(float(content.get("x")))
                        y = int(float(content.get("y")))
                        mask = np.array(json.loads(content.get("mask")))
                        z = int(depthimage[y][x])
                        z_max = find_max_value_with_mask(mask, depthimage)

                        obj_width = {object_name: int(float(content.get("obj_width")))}
                        print(
                            f"x: {x},y: {y},z: {z},z_max:{z_max},obj_width: {obj_width}"
                        )
                        max_label = float(content.get("max_label"))
                        loc = {
                            object_name: (x, y, z + 20)
                        }  # z is the depth distance of object. 20 is the offset to the center of the object.
                        break
                else:
                    max_label = robot_info.threshold
                    obj_width = {object_name: random.randint(1, 100)}
                    loc = {
                        object_name: (
                            random.randint(1, 100),
                            random.randint(1, 100),
                            random.randint(1, 100),
                        )
                    }
                    break
            if max_label >= robot_info.threshold:
                robot_info.known_dict.update(loc)
                robot_info.obj_width_dict.update(obj_width)
            else:
                return "Fail. The robot didn't find the target object."

        return str(loc)

    return search_object


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
