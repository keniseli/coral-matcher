from app.domain.models import BoundingBox, Point, Segment
from app.orchestration.models import IdentifyResult
import numpy as np
from flask import Request
import json
import base64
import cv2

from app.persistence.storage import decode_image_stream
from app.segmentation.models import SegmentationResult
from app.orchestration.models import IdentifyRequest, ConfirmRequest
from app.domain.observation import Observation


def serialize_image_upload_response(result: SegmentationResult, observation_candidates: list[Observation]) -> dict:
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
        "observationCandidates": [
            {
                "id": observation.id,
                "coralId": observation.id,
                "coralName": observation.coral_name,
                "monitoringSessionDate": observation.created_at,
                #TODO: find a way to show visual similarity. is this distance between the vectors? or the confidence of the segment? 
                "visualSimilarity": 0.83,
                "diveSite": observation.dive_site,
                # intentionally return a smaller image
                "imageUrl": observation.cropped_image_path,
            }
            for observation in observation_candidates
        ]
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
    segments_form_field = request.form["segments"]
    segments_form_payload = json.loads(segments_form_field)
    segments_payload_field_key = "selectedSegments"
    segments_json_array = segments_form_payload[segments_payload_field_key]
    segments = parse_segments(segments_json_array)

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
    
def parse_confirm_request(request) -> ConfirmRequest:
    """
    Convert the http request into a ConfirmRequest for processing
    """
    uploaded_file = _extract_file_from_request(request, "image")
    image = decode_image_stream(uploaded_file)

    segments_form_field = request.form["segments"]
    segments_form_payload = json.loads(segments_form_field)
    segments_payload_field_key = "selectedSegments"
    segments_json_array = segments_form_payload[segments_payload_field_key]
    segments = parse_segments(segments_json_array)

    dive_site = request.form["diveSite"]
    coral_name = request.form["coralName"]
    selected_candidate_id = request.form["selectedCandidateId"]
    
    return ConfirmRequest(image, segments, selected_candidate_id, dive_site, coral_name)

def parse_segments(segments_json_array):
    return [
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
        for segment in segments_json_array
    ]
    