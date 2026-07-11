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

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# MACHINE LEARNING MODEL INITIALIZATION
# ==========================================
# Initialize a lightweight ResNet-18 network stripped down to its feature layers.
# This runs locally on serverless CPU in milliseconds.
device = torch.device("cpu")
resnet_model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
# Strip away the final 1000-class classification layer to get raw 512-dimension spatial vectors
resnet_model = torch.nn.Sequential(*list(resnet_model.children())[:-1])
resnet_model.eval()

# PyTorch Image Normalization Pipeline
transform_pipeline = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406], # Standard ImageNet distribution scales
        std=[0.229, 0.224, 0.225]
    )
])

def apply_underwater_corrections(img_matrix):
    """ Applies CLAHE and Gray World color balancing (From Story 1) """
    if img_matrix is None or img_matrix.size == 0:
        raise ValueError("Empty image matrix passed to processing engine.")
    
    lab = cv2.cvtColor(img_matrix, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l_channel)
    enhanced_lab = cv2.merge((cl, a_channel, b_channel))
    bgr_enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    b, g, r = cv2.split(bgr_enhanced)
    mean_gray = (np.mean(b) + np.mean(g) + np.mean(r)) / 3.0
    
    b_bal = np.clip((b * (mean_gray / np.mean(b) if np.mean(b) > 0 else 1.0)), 0, 255).astype(np.uint8)
    g_bal = np.clip((g * (mean_gray / np.mean(g) if np.mean(g) > 0 else 1.0)), 0, 255).astype(np.uint8)
    r_bal = np.clip((r * (mean_gray / np.mean(r) if np.mean(r) > 0 else 1.0)), 0, 255).astype(np.uint8)
    
    return cv2.merge((b_bal, g_bal, r_bal))

def generate_vector_embedding(cv2_image):
    """
    Transforms an OpenCV color image matrix into a 512-dimension mathematical array list.
    """
    # Convert image spectrum from BGR (OpenCV) to RGB (PyTorch standard)
    rgb_img = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    
    # Apply standard cropping, tensor conversion, and normalization shapes
    tensor_img = transform_pipeline(rgb_img).unsqueeze(0).to(device)
    
    # Disable tensor tracking gradients to maximize processing speed
    with torch.no_grad():
        embedding_tensor = resnet_model(tensor_img)
        # Flatten array shape down to a simple 1D structure
        embedding_tensor = torch.squeeze(embedding_tensor)
        # Convert floating point arrays straight into a standard Python native list
        vector_list = embedding_tensor.cpu().numpy().tolist()
        
    return vector_list

@functions_framework.http
def process_coral_upload(request):
    """ HTTP Serverless Cloud Function Entry Point """
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
            return {"error": "Failed to safely decode the target image layout."}, 400

        # 1. Standardize visual appearance
        processed_img = apply_underwater_corrections(raw_img)

        # 2. Extract mathematical spatial signatures (The Vector Vault Addition)
        vector_fingerprint = generate_vector_embedding(processed_img)

        # 3. Stream compressed artifact directly to Google Cloud Storage
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

        # 4. Save records to db
        print("saving monitoring session to db...")
        session_payload = {
            "coral_id": coral_id,
            "site_name": site_name,
            "storage_url": public_url
        }
        session_response = supabase_client.table("monitoring_sessions").insert(session_payload).execute()
        
        # Extract the auto-generated primary key UUID of this monitoring visit row
        inserted_session = session_response.data[0]
        session_uuid = inserted_session["id"]

        print("saving vector fingerprint to db...")
        vector_payload = {
            "session_id": session_uuid, # Relational foreign key binding
            "coral_id": coral_id,
            "site_name": site_name,
            "embedding": vector_fingerprint
        }
        supabase_client.table("media_vectors").insert(vector_payload).execute()
        
        return {
            "status": "success",
            "message": "Coral metrics logged and mathematical features cataloged safely.",
            "session_data": inserted_session
        }, 201

    except Exception as e:
        return {"error": f"Vector Vault insertion breakdown: {str(e)}"}, 500
