import os
import functions_framework
from dotenv import load_dotenv
from supabase import create_client, Client
from vision import apply_underwater_corrections
from vision import crop_primary_coral
from embedding import generate_vector_embedding
from storage import decode_image_stream, save_debug_image, upload_image

import logging

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "coral-mvp-media")
GCP_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", BUCKET_NAME)

_supabase_instance = None

logger = logging.getLogger(__name__)

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

    # ----------------------------------------------------
    # ROUTE A: DISCOVER & REGISTER A NEW CORAL (/register-new)
    # ----------------------------------------------------
    if request.path == "/register-new":
        try:
            site_name = request.form.get("site_name")
            coral_id = request.form.get("coral_id")
            uploaded_file = request.files.get("image")

            if not site_name or not coral_id or not uploaded_file:
                return add_cors_headers({"error": "Missing metadata fields."}, 400)

            # Ingest and decode the uploaded image stream
            raw_img = decode_image_stream(uploaded_file)

            # Apply OpenCV adjustments
            processed_img = apply_underwater_corrections(raw_img)
            
            # Crop coral, keeping some margin
            cropped_img = crop_primary_coral(processed_img)["crop"]
            save_debug_image(cropped_img, f"processing/debug_crop_{site_name}_{coral_id}_{uploaded_file.filename}")

            # Extract AI vector descriptor fingerprint
            vector_fingerprint = generate_vector_embedding(cropped_img)

            public_url = upload_image(processed_img, f"processed/{site_name}/{coral_id}_{uploaded_file.filename}")

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

            # Run color adjustments so the vector search matches true features, not water color shifts
            corrected_img = apply_underwater_corrections(raw_img)
            cropped_img = crop_primary_coral(corrected_img)["crop"]
            debug_path = f"processing/debug_crop_{site_name}_{uploaded_file.filename}"
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
