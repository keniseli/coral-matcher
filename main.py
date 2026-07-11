import os
import cv2
import numpy as np
import functions_framework
from google.cloud import storage
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
# Initialize clients using safe environment lookups
# For local testing, fallback mock defaults are provided
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "mock-anon-key")
BUCKET_NAME = os.getenv("BUCKET_NAME", "coral-matcher-media")

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def apply_underwater_corrections(img_matrix):
    """
    Applies local contrast enhancement (CLAHE) and basic 
    Gray World color balancing to recover suppressed red channels.
    """
    if img_matrix is None or img_matrix.size == 0:
        raise ValueError("Empty image matrix passed to processing engine.")

    # 1. CLAHE Contrast Adjustment via LAB Space
    lab = cv2.cvtColor(img_matrix, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l_channel)
    enhanced_lab = cv2.merge((cl, a_channel, b_channel))
    bgr_enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    # 2. Gray World Channel Balancing
    b, g, r = cv2.split(bgr_enhanced)
    mean_b, mean_g, mean_r = np.mean(b), np.mean(g), np.mean(r)
    mean_gray = (mean_b + mean_g + mean_r) / 3.0

    # Avoid zero division bugs if image is completely pitch black
    scale_b = mean_gray / mean_b if mean_b > 0 else 1.0
    scale_g = mean_gray / mean_g if mean_g > 0 else 1.0
    scale_r = mean_gray / mean_r if mean_r > 0 else 1.0

    b_bal = np.clip((b * scale_b), 0, 255).astype(np.uint8)
    g_bal = np.clip((g * scale_g), 0, 255).astype(np.uint8)
    r_bal = np.clip((r * scale_r), 0, 255).astype(np.uint8)

    return cv2.merge((b_bal, g_bal, r_bal))

@functions_framework.http
def process_coral_upload(request):
    """
    HTTP Cloud Function handling multi-part form payloads
    """
    # Guard against incorrect method calls
    if request.method != "POST":
        return {"error": "Only HTTP POST requests are accepted."}, 405

    try:
        
        print("extracting form data...")
        # Extract fields from multi-part form metadata boundary
        site_name = request.form.get("site_name")
        coral_id = request.form.get("coral_id")
        uploaded_file = request.files.get("image")

        if not site_name or not coral_id or not uploaded_file:
            return {"error": "Missing required fields: site_name, coral_id, or image.",
                    "site": site_name, "coral": coral_id, "file": uploaded_file}, 400

        print("reading file...")
        # Read input buffer directly into memory via NumPy array
        file_bytes = np.frombuffer(uploaded_file.read(), np.uint8)
        raw_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if raw_img is None:
            return {"error": "Failed to decode target image asset. File may be corrupt."}, 400

        # Process the image matrix arrays
        print("applying underwater corrections...")
        processed_img = apply_underwater_corrections(raw_img)

        print("encoding normalized image...")
        # Encode normalized image matrix directly to an extension format byte string
        _, encoded_buffer = cv2.imencode(".jpg", processed_img)
        processed_bytes = encoded_buffer.tobytes()

        print("uploading normalized image to bucket...")
        # Upload binary stream directly to Google Cloud Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_filename = f"processed/{site_name}/{coral_id}_{uploaded_file.filename}"
        blob = bucket.blob(blob_filename)
        
        blob.upload_from_string(processed_bytes, content_type="image/jpeg")
        public_url = f"https://googleapis.com{BUCKET_NAME}/{blob_filename}"

        # Write metadata logs into Supabase
        db_payload = {
            "coral_id": coral_id,
            "site_name": site_name,
            "storage_url": public_url
        }
        print("saving record to db...")
        db_response = supabase_client.table("monitoring_sessions").insert(db_payload).execute()
        
        return {
            "status": "success",
            "message": "Coral metrics ingested successfully.",
            "data": db_response.data[0]
        }, 201

    except Exception as e:
        return {"error": f"Internal pipeline execution error: {str(e)}"}, 500
