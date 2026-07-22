import logging
import sys
import functions_framework
from flask import Request

import numpy as np
from functools import reduce

from app.orchestration.coral_service import CoralService
from app.persistence.storage import decode_image_stream
from app.api.serialization import parse_identify_request, serialize_observation_candidates, serialize_image_upload_response, parse_confirm_request


logger = logging.getLogger(__name__)

logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )

service = CoralService()

def add_cors_headers(body, status=200):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }
    return body, status, headers

def extract_file_from_request(request: Request, parameter_name: str):
    uploaded_file = request.files.get(parameter_name)
    if uploaded_file is None:
        raise ValueError("[API] Missing image.")
    return uploaded_file

@functions_framework.http
def process_coral_upload(request: Request):
    logger.info("%s %s", request.method, request.path)

    if request.method == "OPTIONS":
        return add_cors_headers("", 204)

    try:
        if request.path == "/api/upload-coral-image":
            uploaded_file = extract_file_from_request(request, "image")
            image: np.ndarray = decode_image_stream(uploaded_file)
            segmentation = service.segment_image(
                image=image,
                filename=uploaded_file.filename or "uploaded.jpg"
            )
            segment = reduce(
                lambda segment, other: segment if segment.score() > other.score() else other,
                segmentation.segments
            )
            candidates = service.find_similar_observations(image, [segment])
            response = serialize_image_upload_response(segmentation, candidates)
            return add_cors_headers(response)

        if request.path == "/api/identify-by-segments":
            identify_request = parse_identify_request(request)
            observationCandidates = service.find_similar_observations(identify_request.image, identify_request.selected_segments)
            response = serialize_observation_candidates(observationCandidates)
            return add_cors_headers(response)
        
        if request.path == "/api/confirm-coral":
            confirm_request = parse_confirm_request(request)
            observation = service.confirm_observation(confirm_request.image,
                confirm_request.selected_segments,
                confirm_request.dive_site,
                confirm_request.coral_name
            ).observation
            return add_cors_headers({"observationId": observation.id})

        return add_cors_headers({"error": "Unknown endpoint."}, 404)

    except ValueError as ex:
        logger.exception(f"[API] An error has occurred: {str(ex)}", ex)
        return add_cors_headers({"error": str(ex)}, 400)

    except Exception as ex:
        logger.exception(ex)
        return add_cors_headers({"error": "Internal server error."}, 500)

    