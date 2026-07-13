# Getting Started
## Prerequisites
* Running Supabase instance with url and key (```SUPABASE_URL``` and ```SUPABASE_KEY```) in .env file or environment variables
* Running Google Cloud Storage Bucket with name (```BUCKET_NAME```) defined in .env file or environment variables

## Run Locally
```

# Install dependencies - this takes a while
$ cd backend
$ conda env create -f environment.yaml
$ pip install -r requirements.txt
$ conda activate coral-matcher

# Run tests
$ pytest -s test_vision.py

# Run app
$ functions-framework --target=process_coral_upload --debug

# Example image upload
$ curl --location 'http://127.0.0.1:8080/' \
--form 'image=@"/C:/Users/kenis/Downloads/Corals Daniek/CR_IslaLarga_T08_c001_A.JPG"' \
--form 'coral_id="1"' \
--form 'site_name="Isla Larga"'
```
