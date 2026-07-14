import os
import uuid
import cv2
import numpy as np
import functions_framework
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
from typing import Any, Dict, List
from app.vision import apply_underwater_corrections
from app.vision import crop_primary_coral
from app.embedding import generate_vector_embedding
from app.storage import decode_image_stream, save_debug_image, upload_image
from app.segmentation.coralscop_adapter import CoralScopAdapter

import logging
logger = logging.getLogger(__name__)

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

_supabase_instance = None

SEGMENTATION_CACHE: Dict[str, Any] = {}

adapter = CoralScopAdapter()

def store_segmentation_cache(segmentation_id: str, masks: List[Dict[str, Any]], raw_img: np.ndarray) -> None:
    SEGMENTATION_CACHE[segmentation_id] = {
        "masks": masks,
        "image": raw_img,
    }


def get_cached_segmentation(segmentation_id: str) -> Dict[str, Any]:
    cached = SEGMENTATION_CACHE.get(segmentation_id)
    if cached is None:
        raise ValueError("Segmentation ID not found.")
    return cached


def convert_mask_to_polygon(mask: np.ndarray) -> List[List[int]]:
    mask = (mask > 0).astype(np.uint8) * 255

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return []

    contour = max(contours, key=cv2.contourArea)
    return [[int(x), int(y)] for x, y in contour.reshape(-1, 2)]


def build_segment_response(mask_record: Dict[str, Any], segment_id: int) -> Dict[str, Any]:
    segmentation = mask_record.get("segmentation")
    if isinstance(segmentation, np.ndarray):
        mask = segmentation
    elif isinstance(segmentation, list):
        mask = np.asarray(segmentation, dtype=np.uint8)
    else:
        raise ValueError("Unsupported segmentation format for polygon conversion.")

    polygon = convert_mask_to_polygon(mask)
    bbox = mask_record.get("bbox", [0, 0, 0, 0])
    return {
        "id": segment_id,
        "bbox": {
            "x": int(bbox[0]),
            "y": int(bbox[1]),
            "width": int(bbox[2]),
            "height": int(bbox[3]),
        },
        "predictedIoU": float(mask_record.get("predicted_iou", 0.0)),
        "stabilityScore": float(mask_record.get("stability_score", 0.0)),
        "polygon": polygon,
    }


def merge_selected_masks(masks: List[Dict[str, Any]], selected_ids: List[int]) -> np.ndarray:
    if not isinstance(selected_ids, list) or not selected_ids:
        raise ValueError("selectedSegments must be a non-empty list of segment indices.")

    merged_mask = None
    for segment_id in selected_ids:
        if not isinstance(segment_id, int) or segment_id < 0 or segment_id >= len(masks):
            raise ValueError(f"Invalid segment id: {segment_id}")

        segmentation = masks[segment_id].get("segmentation")
        if segmentation is None:
            raise ValueError(f"Missing segmentation for segment {segment_id}.")

        if isinstance(segmentation, list):
            mask = np.asarray(segmentation, dtype=np.uint8)
        elif isinstance(segmentation, np.ndarray):
            mask = segmentation.astype(np.uint8)
        else:
            raise ValueError("Unsupported segmentation format for selected mask.")

        if mask.ndim == 3 and mask.shape[2] == 1:
            mask = mask[:, :, 0]
        if mask.ndim != 2:
            raise ValueError("Selected segmentation masks must be 2D arrays.")

        mask = (mask > 0).astype(np.uint8)
        merged_mask = mask if merged_mask is None else np.logical_or(merged_mask, mask)

    if merged_mask is None:
        raise ValueError("Merged mask could not be created from selected segments.")

    return merged_mask.astype(np.uint8)


def build_mask_crop(raw_img: np.ndarray, merged_mask: np.ndarray) -> Dict[str, Any]:
    ys, xs = np.where(merged_mask > 0)
    if ys.size == 0 or xs.size == 0:
        raise ValueError("Merged mask contains no pixels.")

    x = int(xs.min())
    y = int(ys.min())
    w = int(xs.max() - x + 1)
    h = int(ys.max() - y + 1)

    dummy_mask = [{
        "segmentation": merged_mask,
        "bbox": [x, y, w, h],
        "predicted_iou": 1.0,
        "stability_score": 1.0,
    }]

    return crop_primary_coral(raw_img, dummy_mask)


def identify_coral(segmentation_id: str, selected_ids: List[int]) -> Dict[str, Any]:
    if not segmentation_id or not isinstance(segmentation_id, str):
        raise ValueError("Missing or invalid segmentationId.")
    if not isinstance(selected_ids, list) or not selected_ids:
        raise ValueError("selectedSegments must be a non-empty list of segment indices.")

    cached = get_cached_segmentation(segmentation_id)
    masks = cached["masks"]
    raw_img = cached["image"]

    merged_mask = merge_selected_masks(masks, selected_ids)

    crop_result = build_mask_crop(raw_img, merged_mask)
    square_crop = crop_result.get("square_crop")
    if square_crop is None:
        raise ValueError("Failed to generate padded crop.")

    return {
        "cropWidth": int(square_crop.shape[1]),
        "cropHeight": int(square_crop.shape[0]),
        "selectedSegments": selected_ids,
    }


def segment_uploaded_image(uploaded_file) -> Dict[str, Any]:
    if not uploaded_file:
        raise ValueError("Missing image file.")

    raw_img = decode_image_stream(uploaded_file)
    masks = adapter.segment(raw_img)
    if not masks:
        raise ValueError("No coral segments detected.")

    segmentation_id = str(uuid.uuid4())
    store_segmentation_cache(segmentation_id, masks, raw_img)

    height, width = raw_img.shape[:2]
    segment_responses = [build_segment_response(mask, idx) for idx, mask in enumerate(masks)]

    return {
        "segmentationId": segmentation_id,
        "image": {
            "width": width,
            "height": height,
        },
        "segments": segment_responses,
    }


def get_supabase_client() -> Client:
    """
    Implements Lazy Initialization to bypass container-loading order bugs.
    Ensures environment variables are fully present before generating clients.
    """
    global _supabase_instance
    if _supabase_instance is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Runtime configuration failure: Database credentials missing from host container environment.")
        _supabase_instance = create_client(url, key)
    return _supabase_instance

def add_cors_headers(response_data, status_code=200):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
        "Access-Control-Max-Age": "3600"
    }
    return (response_data, status_code, headers)

# ========================================================
# UNIFIED ROUTER GATEWAY
# ========================================================
@functions_framework.http
def process_coral_upload(request):
    if request.method == "OPTIONS":
        return add_cors_headers("", 204)
    
    if request.path == "/api/segment-image":
        try:
            uploaded_file = request.files.get("image")
            response_body = segment_uploaded_image(uploaded_file)
            return add_cors_headers(response_body, 200)
        except ValueError as e:
            logger.exception(f"Segmentation request validation failure: {str(e)}")
            return add_cors_headers({"error": str(e)}, 400)
        except Exception as e:
            logger.exception(f"Segmentation execution failure: {str(e)}")
            return add_cors_headers({"error": f"Segmentation execution failure: {str(e)}"}, 500)

    if request.path == "/api/identify-coral":
        try:
            payload = request.get_json(silent=True)
            if payload is None:
                raise ValueError("Request body must be valid JSON.")

            segmentation_id = payload.get("segmentationId")
            selected_ids = payload.get("selectedSegments")
            response_body = identify_coral(segmentation_id, selected_ids)
            return add_cors_headers(response_body, 200)
        except ValueError as e:
            logger.exception(f"Identify request validation failure: {str(e)}")
            return add_cors_headers({"error": str(e)}, 400)
        except Exception as e:
            logger.exception(f"Identify execution failure: {str(e)}")
            return add_cors_headers({"error": f"Identify execution failure: {str(e)}"}, 500)


    # ----------------------------------------------------
    # ROUTE A: DISCOVER & REGISTER A NEW CORAL (/register-new)
    # ----------------------------------------------------
    elif request.path == "/register-new":
        try:
            site_name = request.form.get("site_name")
            coral_id = request.form.get("coral_id")
            uploaded_file = request.files.get("image")

            if not site_name or not coral_id or not uploaded_file:
                return add_cors_headers({"error": "Missing metadata fields."}, 400)

            # Ingest and decode the uploaded image stream
            raw_img = decode_image_stream(uploaded_file)

            masks = adapter.segment(raw_img)
            segmentation = crop_primary_coral(raw_img, masks)
            if segmentation is None:
                return add_cors_headers({"error": "Segmentation not possible. Has image been uploaded?"})
            cropped_img = segmentation["crop"]
            save_debug_image(cropped_img, f"processing/debug_crop_{site_name}_{coral_id}_{uploaded_file.filename}")

            # Extract AI vector descriptor fingerprint
            vector_fingerprint = generate_vector_embedding(cropped_img)

            public_url = upload_image(cropped_img, f"processed/{site_name}/{coral_id}_{uploaded_file.filename}")

            # Save record to monitoring_sessions
            session_payload = {"coral_id": coral_id, "site_name": site_name, "storage_url": public_url}
            session_res = get_supabase_client().table("monitoring_sessions").insert(session_payload).execute()
            session_uuid = session_res.data[0]["id"]

            # Link fingerprint database row
            vector_payload = {
                "session_id": session_uuid,
                "coral_id": coral_id,
                "site_name": site_name,
                "embedding": vector_fingerprint
            }
            get_supabase_client().table("media_vectors").insert(vector_payload).execute()

            return add_cors_headers({
                "status": "success",
                "message": "New baseline individual logged successfully.",
                "data": session_res.data[0]
            }, 201)

        except Exception as e:
            logger.exception(f"Registration exception: {str(e)}")
            return add_cors_headers({"error": f"Registration exception: {str(e)}"}, 500)

    # ----------------------------------------------------
    # ROUTE B: SEARCH PATTERN SIMILARITIES (/match-coral)
    # ----------------------------------------------------
    elif request.path == "/match-coral":
        try:
            site_name = request.form.get("site_name")
            uploaded_file = request.files.get("image")

            if not site_name or not uploaded_file:
                return add_cors_headers({"error": "Missing parameters."}, 400)

            raw_img = decode_image_stream(uploaded_file)

            masks = adapter.segment(raw_img)
            segmentation = crop_primary_coral(raw_img, masks)
            if segmentation is None:
                return add_cors_headers({"error": "Segmentation not possible. Has image been uploaded?"})
            cropped_img = segmentation["crop"]
            debug_path = f"processing/{datetime.now().strftime('%Y%m%d_%H%M')}_debug_crop_{site_name}_{uploaded_file.filename}"
            save_debug_image(cropped_img, debug_path)
            
            query_vector = generate_vector_embedding(cropped_img)

            db_call = get_supabase_client().rpc("match_coral_vectors", {
                "query_embedding": query_vector,
                "filter_site": site_name,
                "match_threshold": 0.85,
                "match_count": 3
            }).execute()

            return add_cors_headers({"matches": db_call.data}, 200)
        except Exception as e:
            logger.exception(f"Search execution fail: {str(e)}")
            return add_cors_headers({"error": f"Search execution fail: {str(e)}"}, 500)

    # ----------------------------------------------------
    # ROUTE C: COMMIT A CONFIRMED MATCHED SESSION (/commit-session)
    # ----------------------------------------------------
    elif request.path == "/commit-session":
        try:
            coral_id = request.form.get("coral_id")
            site_name = request.form.get("site_name")
            public_url = request.form.get("storage_url")

            if not coral_id or not site_name or not public_url:
                return add_cors_headers({"error": "Missing core identifier records."}, 400)

            session_payload = {"coral_id": coral_id, "site_name": site_name, "storage_url": public_url}
            db_response = get_supabase_client().table("monitoring_sessions").insert(session_payload).execute()

            return add_cors_headers({
                "status": "success",
                "message": "Monitoring session logged successfully.",
                "data": db_response.data[0]
            }, 201)
        except Exception as e:
            logger.exception(f"Commit verification failure: {str(e)}")
            return add_cors_headers({"error": f"Commit verification failure: {str(e)}"}, 500)

    return add_cors_headers({"error": "Endpoint path not resolved."}, 404)
