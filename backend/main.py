import os
import cv2
import numpy as np
import functions_framework
from dotenv import load_dotenv
from google.cloud import storage
from supabase import create_client, Client

import torch
import torchvision.models as models
import torchvision.transforms as transforms

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "coral-mvp-media")
GCP_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", BUCKET_NAME)

_supabase_instance = None

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

# ========================================================
# MACHINE LEARNING ENGINE INITIALIZATION (UPDATED)
# ========================================================
device = torch.device("cpu")

# Re-direct the framework to point inside our local packaged directory path
local_weights_dir = os.path.join(os.getcwd(), "weights")
os.environ["TORCH_HOME"] = local_weights_dir

resnet_model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
resnet_model = torch.nn.Sequential(*list(resnet_model.children())[:-1])
resnet_model.eval()

transform_pipeline = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# ========================================================
# OPENCV UNDERWATER COLOR EXTENSION FUNCTIONS (RESTORED)
# ========================================================
def apply_underwater_corrections(img_matrix):
    """
    Applies CLAHE local contrast enhancement and Gray World color balancing
    to recover lost red channel data signatures underwater.
    """
    if img_matrix is None or img_matrix.size == 0:
        raise ValueError("Empty image matrix passed to processing engine.")
    
    # 1. CLAHE Contrast Equalization
    lab = cv2.cvtColor(img_matrix, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l_channel)
    enhanced_lab = cv2.merge((cl, a_channel, b_channel))
    bgr_enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    # 2. Gray World Channel Normalization (Red Recovery)
    b, g, r = cv2.split(bgr_enhanced)
    mean_b, mean_g, mean_r = np.mean(b), np.mean(g), np.mean(r)
    mean_gray = (mean_b + mean_g + mean_r) / 3.0
    
    scale_b = mean_gray / mean_b if mean_b > 0 else 1.0
    scale_g = mean_gray / mean_g if mean_g > 0 else 1.0
    scale_r = mean_gray / mean_r if mean_r > 0 else 1.0
    
    b_bal = np.clip((b * scale_b), 0, 255).astype(np.uint8)
    g_bal = np.clip((g * scale_g), 0, 255).astype(np.uint8)
    r_bal = np.clip((r * scale_r), 0, 255).astype(np.uint8)
    
    return cv2.merge((b_bal, g_bal, r_bal))

def generate_vector_embedding(cv2_image):
    """ Transforms an OpenCV image matrix into a 512-dimension spatial vector array. """
    rgb_img = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    tensor_img = transform_pipeline(rgb_img).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding_tensor = torch.squeeze(resnet_model(tensor_img))
        return embedding_tensor.cpu().numpy().tolist()

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

            # Ingest image array byte matrices
            file_bytes = np.frombuffer(uploaded_file.read(), np.uint8)
            raw_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if raw_img is None:
                return add_cors_headers({"error": "Corrupt or invalid image."}, 400)

            # 1. Apply OpenCV adjustments
            processed_img = apply_underwater_corrections(raw_img)
            # 2. Extract AI vector descriptor fingerprint
            vector_fingerprint = generate_vector_embedding(processed_img)

            # 3. Stream normalized JPEG file stream directly to GCS bucket
            _, encoded_buffer = cv2.imencode(".jpg", processed_img)
            processed_bytes = encoded_buffer.tobytes()

            storage_client = storage.Client(project=GCP_PROJECT)
            bucket = storage_client.bucket(BUCKET_NAME)
            blob_filename = f"processed/{site_name}/{coral_id}_{uploaded_file.filename}"
            blob = bucket.blob(blob_filename)
            blob.upload_from_string(processed_bytes, content_type="image/jpeg")
            public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_filename}"

            # 4. Save record to monitoring_sessions
            session_payload = {"coral_id": coral_id, "site_name": site_name, "storage_url": public_url}
            session_res = get_supabase_client().table("monitoring_sessions").insert(session_payload).execute()
            session_uuid = session_res.data[0]["id"]

            # 5. Link fingerprint database row
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

            file_bytes = np.frombuffer(uploaded_file.read(), np.uint8)
            raw_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if raw_img is None:
                return add_cors_headers({"error": "Failed to decode matrix."}, 400)

            # Run color adjustments so the vector search matches true features, not water color shifts
            corrected_img = apply_underwater_corrections(raw_img)
            query_vector = generate_vector_embedding(corrected_img)

            db_call = get_supabase_client().rpc("match_coral_vectors", {
                "query_embedding": query_vector,
                "filter_site": site_name,
                "match_threshold": 0.85,
                "match_count": 3
            }).execute()

            return add_cors_headers({"matches": db_call.data}, 200)
        except Exception as e:
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
            return add_cors_headers({"error": f"Commit verification failure: {str(e)}"}, 500)

    return add_cors_headers({"error": "Endpoint path not resolved."}, 404)
