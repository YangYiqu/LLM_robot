import requests
import cv2
import base64
import numpy as np


class RobotConnect:
    def __init__(self):
        self.address = "http://192.168.0.148:23915/"
        self.use_robot = True

    def img_decode_rgb_image(img_str, flag=cv2.IMREAD_COLOR):
        # flag: specify image type as cv.imread
        # img_str = requests.get(IMG_FET_API).content
        img_str = base64.b64decode(img_str)
        nparr = np.frombuffer(img_str, np.uint8)
        img = cv2.imdecode(nparr, flag)
        img = img[:, :, [2, 1, 0]]
        return img

    def img_decode_depth_image(img_str, flag=cv2.IMREAD_ANYDEPTH):
        img_str = base64.b64decode(img_str)
        nparr = np.frombuffer(img_str, np.uint16)
        img = cv2.imdecode(nparr, flag)
        return img

    def control_gripper(self, data):
        if self.use_robot:
            resp = requests.post(self.address + "control_gripper", data=data).content
            return resp
        else:
            return "Fail to activate gripper"

    def move_arm_position(self, data):
        if self.use_robot:
            resp = requests.post(
                self.address + "move_arm_position", params=data
            ).content
            return resp
        else:
            return "Fail to activate arm to move "

    def get_depthimage(self):
        if self.use_robot:
            return self.img_decode_depth_image(
                requests.get(self.address + "depthimage", timeout=30).content
            )
        else:
            print("Using the default depth data")
            return cv2.imread(r"data//default_depth.png")[:, :, 0]

    def get_rgbimage(self):
        if self.use_robot:
            return self.img_decode_rgb_image(
                requests.get(self.address + "rgbimage", timeout=40).content
            )
        else:
            print("Using the default rgb image")
            return cv2.imread(r"assets//1.jpg")


robot = RobotConnect()
