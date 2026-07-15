import numpy as np
from flask import Request
import json
import base64
import cv2

from app.storage import decode_image_stream
from app.segmentation.models import SegmentationResult, Segment, BoundingBox, Point
from app.orchestration.coral_service import IdentifyRequest, IdentifyResult



def serialize_segmentation_response(result: SegmentationResult) -> dict:
    """
    Convert a SegmentationResult into a JSON-compatible API response.
    """
    return {
        "image": {
            "height": result.image_height,
            "width": result.image_width,
        },
        "segments": [
            {
                "id": segment.id,
                "bbox": {
                    "x": segment.bbox.x,
                    "y": segment.bbox.y,
                    "width": segment.bbox.width,
                    "height": segment.bbox.height,
                },
                "polygon": [
                    [point.x, point.y]
                    for point in segment.polygon
                ],
                "predictedIoU": segment.predictedIoU,
                "stabilityScore": segment.stabilityScore,
            }
            for segment in result.segments
        ],
    }
    
def _extract_file_from_request(request: Request, parameter_name: str):
    uploaded_file = request.files[parameter_name]
    if uploaded_file is None:
        raise ValueError("[API] Missing image.")
    return uploaded_file

def parse_identify_request(request) -> IdentifyRequest:
    """
    Convert the http request into a IdentifyRequest for processing
    """
    uploaded_file = _extract_file_from_request(request, "image")
    image = decode_image_stream(uploaded_file)
    payload = json.loads(request.form["segments"])
    
    segments = [
        Segment(
            id=segment["id"],
            bbox=BoundingBox(
                x=segment["bbox"]["x"],
                y=segment["bbox"]["y"],
                width=segment["bbox"]["width"],
                height=segment["bbox"]["height"],
            ),
            polygon=[
                Point(
                    x=point[0],
                    y=point[1],
                )
                for point in segment["polygon"]
            ],
            predictedIoU=segment["predictedIoU"],
            stabilityScore=segment["stabilityScore"],
        )
        for segment in payload["selectedSegments"]
    ]
    return IdentifyRequest(image=image, selected_segments=segments)
    
def serialize_identify_response(result: IdentifyResult) -> dict:
    success, encoded = cv2.imencode(".jpg", result.crop)

    if not success:
        raise ValueError("Failed to encode cropped image.")

    return {
        "image": {
            "width": result.crop.shape[1],
            "height": result.crop.shape[0],
        },
        "imageData": base64.b64encode(encoded).decode("ascii")
    }