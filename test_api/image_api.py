import requests
import cv2
import numpy as np
import base64

"""
test the depthimage api
"""

def img_decode(img_str, flag=cv2.IMREAD_ANYDEPTH):
    # flag: specify image type as cv.imread
    # img_str = requests.get(IMG_FET_API).content
    img_str = base64.b64decode(img_str)

    nparr = np.frombuffer(img_str, np.uint16)

    img = cv2.imdecode(nparr, flag)
    print(img.shape)
    # img = img[:, :, [2, 1, 0]]
    # print(img[:, :, 0].max())
    return img


def img_resize(image):
    height, width = image.shape[:2]
    crop_width = int((width - 960) / 2)
    cropped_image = image[:, crop_width : width - crop_width]

    new_width = int(960 / 1.5)
    new_height = int(height / 1.5)
    resized_image = cv2.resize(cropped_image, (new_width, new_height))
    depth_image = resized_image**0.3
    print(depth_image.shape)
    print(depth_image)
    depth_image = (65535 * depth_image / depth_image.max()).astype(np.uint16)
    cv2.imwrite("depth.tif", depth_image)


while True:
    img_str = requests.get("http://192.168.0.148:23915/depthimage", timeout=15)

    # print(img_str.status_code)
    # img = img_decode(img_str=img_str)
    # img_resize(img)
