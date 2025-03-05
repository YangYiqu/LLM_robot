import cv2
import numpy as np
import supervision as sv
import torch
import torchvision
import requests
from groundingdino.util.inference import Model
from segment_anything import build_sam, SamPredictor
import base64
import gradio as gr
import matplotlib.pyplot as plt

"""test for the grounded sam"""

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# GroundingDINO config and checkpoint
GROUNDING_DINO_CONFIG_PATH = "C:/Users/MSI/Grounded-Segment-Anything/GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py"
GROUNDING_DINO_CHECKPOINT_PATH = (
    "C:/Users/MSI/Grounded-Segment-Anything/groundingdino_swint_ogc.pth"
)

# Segment-Anything checkpoint
SAM_ENCODER_VERSION = "vit_h"
SAM_CHECKPOINT_PATH = "C:/Users/MSI/Grounded-Segment-Anything/sam_vit_h_4b8939.pth"

# Building GroundingDINO inference model
grounding_dino_model = Model(
    model_config_path=GROUNDING_DINO_CONFIG_PATH,
    model_checkpoint_path=GROUNDING_DINO_CHECKPOINT_PATH,
)

# Building SAM Model and SAM Predictor
# sam = sam_model_registry[SAM_ENCODER_VERSION](checkpoint=SAM_CHECKPOINT_PATH)
sam = build_sam(checkpoint=SAM_CHECKPOINT_PATH)
sam.to(device=DEVICE)
sam_predictor = SamPredictor(sam)


# Predict classes and hyper-param for GroundingDINO
# SOURCE_IMAGE_PATH = "./test_data/1_rgb_Color.png"

BOX_THRESHOLD = 0.3
TEXT_THRESHOLD = 0.3
NMS_THRESHOLD = 0.5


def calculate_mask_centroid(mask):
    mask_array = np.array(mask)
    indices = np.argwhere(mask_array)
    if len(indices) == 0:
        return -1, -1
    centroid = np.mean(indices, axis=0).astype(float)
    return centroid[1], centroid[0]  # Note the coordinate order


def draw_circle(image, x, y):
    center = (int(x), int(y))
    radius = 20
    color = (0, 0, 255)
    thickness = -1
    return cv2.circle(image, center, radius, color, thickness)


def img_decode(img_str, flag=cv2.IMREAD_COLOR):
    # flag: specify image type as cv.imread
    # img_str = requests.get(IMG_FET_API).content
    img_str = base64.b64decode(img_str)
    nparr = np.frombuffer(img_str, np.uint8)
    img = cv2.imdecode(nparr, flag)

    img = img[:, :, [2, 1, 0]]
    return img


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
        print(masks[index].shape)
        # result_masks.append(masks)
    # result_masks = np.concatenate(result_masks, 0)
    return np.array(result_masks)


def grounded_sam(text, zoom=False):
    query = text
    # background = ["fruit cut", "table", "black object"]
    CLASSES = [query]
    # CLASSES_show = [text, "fruit cut", "plastic box"]

    # if zoom:
    #     det_cls = background
    # else:
    #     det_cls = CLASSES
    det_cls = CLASSES
    try:
        image = img_decode(
            requests.get("http://192.168.0.148:23915/rgbimage", timeout=20).content
        )
    except:
        print("error")
    # detect objects
    detections = grounding_dino_model.predict_with_classes(
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
    print(detections.mask.shape)
    annotated_image = mask_annotator.annotate(scene=image.copy(), detections=detections)
    annotated_image = box_annotator.annotate(
        scene=annotated_image, detections=detections, labels=labels
    )
    for i in range(len(labels)):
        centroid_x, centroid_y = calculate_mask_centroid(detections.mask[i])
        annotated_image = draw_circle(annotated_image, centroid_x, centroid_y)
    centroid_x, centroid_y = calculate_mask_centroid(detections.mask[0])
    obj_width = np.sum(detections.mask[0][int(centroid_y)])

    cmap = plt.cm.binary

    # 绘制黑白图像
    plt.imshow(detections.mask[0], cmap=cmap)

    # 保存图像到本地
    plt.savefig("black_and_white_image.png")

    # save the annotated grounded-sam image
    # cv2.imwrite("grounded_sam_annotated_image.jpg", annotated_image)
    return annotated_image, centroid_x, centroid_y, obj_width


demo = gr.Interface(
    fn=grounded_sam,
    inputs=["text"],
    outputs=["image", "text", "text", "text"],
)
if __name__ == "__main__":
    demo.launch(share=True)


# from dashscope import MultiModalConversation

# messages = [
#             {'role': Role.USER,
#              'content': [
#                 {'image': 'file:///media/mark/Workspace/works/ChatGLM/test_img/test3.png'},
#                 {
#                     'text': 'Describe the image content and all the objects in image.'
#                     # 'text': 'locate the pineapple in image. Answer in [x0, y0, x1, y1] format'
#                 }
#             ]}]

# response = MultiModalConversation.call(
#         model=MultiModalConversation.Models.qwen_vl_chat_v1,
#         messages=messages,
#     )
