import cv2
import numpy as np
import supervision as sv
from threading import Thread
import torch
import torchvision
from flask import Flask, jsonify
from groundingdino.util.inference import Model
from segment_anything import build_sam, SamPredictor
import gradio as gr
from flask_restful import Resource, Api, reqparse
import urllib.parse
import base64
import requests
import json
from robot_connect import robot

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# GroundingDINO config and checkpoint
GROUNDING_DINO_CONFIG_PATH = "C:/Users/MSI/Grounded-Segment-Anything/GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py"
GROUNDING_DINO_CHECKPOINT_PATH = (
    "C:/Users/MSI/Grounded-Segment-Anything/groundingdino_swint_ogc.pth"
)

# Segment-Anything checkpoint
SAM_ENCODER_VERSION = "vit_h"
SAM_CHECKPOINT_PATH = "C:/Users/MSI/Grounded-Segment-Anything/sam_vit_h_4b8939.pth"


# Predict classes and hyper-param for GroundingDINO
# SOURCE_IMAGE_PATH = "./test_data/1_rgb_Color.png"

BOX_THRESHOLD = 0.3
TEXT_THRESHOLD = 0.3
NMS_THRESHOLD = 0.5

app = Flask(__name__)


def calculate_mask_centroid(mask):
    mask_array = np.array(mask)
    indices = np.argwhere(mask_array)
    if len(indices) == 0:
        return -1, -1
    centroid = np.mean(indices, axis=0).astype(float)
    return centroid[1], centroid[0]  # Note the coordinate order


def draw_circle(image, x, y, color=(0, 0, 255)):
    center = (int(x), int(y))
    radius = 20
    thickness = -1
    return cv2.circle(image, center, radius, color, thickness)


# Prompting SAM with detected boxes
def segment(
    sam_predictor: SamPredictor, image: np.ndarray, xyxy: np.ndarray
) -> np.ndarray:
    sam_predictor.set_image(image)
    result_masks = []
    for box in xyxy:
        masks, scores, logits = sam_predictor.predict(box=box, multimask_output=True)
        index = np.argmax(scores)
        result_masks.append(masks[index])
        # result_masks.append(masks)
    # result_masks = np.concatenate(result_masks, 0)
    return np.array(result_masks)


def grounded_sam(text, zoom=False):
    query = text
    background = []
    CLASSES = [query]
    # CLASSES_show = [text, "fruit cut", "plastic box"]

    if zoom:
        det_cls = background
    else:
        det_cls = CLASSES
    try:
        image = robot.get_rgbimage()
    except:
        image = cv2.imread(r"assets//1.jpg")
        print("Reading rgb image error in the grounded sam!")

    # detect objects
    detections = grounding_dino_model.predict_with_classes(
        # image=cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
        image=image,
        classes=det_cls,
        box_threshold=BOX_THRESHOLD,
        text_threshold=BOX_THRESHOLD,
    )

    # NMS post process
    print(f"Before NMS: {len(detections.xyxy)} boxes")
    nms_idx = (
        torchvision.ops.nms(
            torch.from_numpy(detections.xyxy),
            torch.from_numpy(detections.confidence),
            NMS_THRESHOLD,
        )
        .numpy()
        .tolist()
    )

    detections.xyxy = detections.xyxy[nms_idx]
    detections.confidence = detections.confidence[nms_idx]
    detections.class_id = detections.class_id[nms_idx]
    print(f"After NMS: {len(detections.xyxy)} boxes")

    if zoom:
        # Zoom-in with the fruit cut position
        xyxy = detections.xyxy[detections.class_id == 0, :]

        if len(xyxy) > 0:
            x1, y1 = np.min(xyxy[:, :2], 0).astype(int)
            x2, y2 = np.max(xyxy[:, 2:], 0).astype(int)
        else:
            # No fruit cut is detected
            pass

        image = image[y1:y2, x1:x2, :]
        # print(image, image.shape)
        detections = grounding_dino_model.predict_with_classes(
            image=cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
            classes=CLASSES,
            box_threshold=BOX_THRESHOLD,
            text_threshold=BOX_THRESHOLD,
        )

        # NMS post process
        print(f"Before NMS: {len(detections.xyxy)} boxes")
        nms_idx = (
            torchvision.ops.nms(
                torch.from_numpy(detections.xyxy),
                torch.from_numpy(detections.confidence),
                NMS_THRESHOLD,
            )
            .numpy()
            .tolist()
        )

        detections.xyxy = detections.xyxy[nms_idx]
        detections.confidence = detections.confidence[nms_idx]
        detections.class_id = detections.class_id[nms_idx]
        print(f"After NMS: {len(detections.xyxy)} boxes")

        print(detections.class_id, detections.confidence)

    # idx = detections.confidence == max(detections.confidence[detections.class_id == 0])
    # detections.xyxy = detections.xyxy[idx]
    # detections.confidence = detections.confidence[idx]
    # detections.class_id = detections.class_id[idx]

    # convert detections to masks
    detections.mask = segment(
        sam_predictor=sam_predictor, image=image, xyxy=detections.xyxy
    )

    # annotate image with detections
    box_annotator = sv.BoxAnnotator()
    mask_annotator = sv.MaskAnnotator()
    labels = [f"{confidence:0.2f}" for _, _, confidence, class_id, _ in detections]
    print(labels)

    annotated_image = mask_annotator.annotate(scene=image.copy(), detections=detections)
    annotated_image = box_annotator.annotate(
        scene=annotated_image, detections=detections, labels=labels
    )
    if len(labels) == 0:
        return annotated_image, 0, 0, 0, 0
    for i in range(len(labels)):
        centroid_x, centroid_y = calculate_mask_centroid(detections.mask[i])
        annotated_image = draw_circle(annotated_image, centroid_x, centroid_y)
    centroid_x, centroid_y = calculate_mask_centroid(detections.mask[0])
    obj_width = np.sum(detections.mask[0][int(centroid_y)])
    annotated_image = draw_circle(
        annotated_image, centroid_x, centroid_y, color=(255, 0, 0)
    )
    # save the annotated grounded-sam image
    cv2.imwrite("Output/{}.jpg".format(text), annotated_image)
    return (
        annotated_image,
        centroid_x,
        centroid_y,
        max(labels),
        obj_width,
        detections.mask[0],
    )


@app.route("/<text>", methods=["GET"])
def locate_object(text):
    text = urllib.parse.unquote_plus(text)
    print("object: " + text)
    annotated_image, centroid_x, centroid_y, max_label, obj_widh, mask = grounded_sam(
        text
    )
    response_data = {
        "x": centroid_x,
        "y": centroid_y,
        "max_label": max_label,
        "obj_width": float(obj_widh),
        "mask": json.dumps(mask.tolist()),
    }
    return json.dumps(response_data)


@app.route("/")
def page():
    return "a"


# demo = gr.Interface(
#     fn=grounded_sam,
#     inputs=["image", "text"],
#     outputs=["image", "text", "text"],
# )
# if __name__ == "__main__":
#     demo.launch()

if __name__ == "__main__":
    # Building GroundingDINO inference model
    image = cv2.imread(r"assets//1.jpg")
    print(image.shape)
    grounding_dino_model = Model(
        model_config_path=GROUNDING_DINO_CONFIG_PATH,
        model_checkpoint_path=GROUNDING_DINO_CHECKPOINT_PATH,
    )

    # Building SAM Model and SAM Predictor
    # sam = sam_model_registry[SAM_ENCODER_VERSION](checkpoint=SAM_CHECKPOINT_PATH)
    sam = build_sam(checkpoint=SAM_CHECKPOINT_PATH)
    sam.eval()
    sam.to(device=DEVICE)
    sam_predictor = SamPredictor(sam)

    app.run(host="0.0.0.0", port=9999)
