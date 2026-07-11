# Getting Started
## Prerequisites
* Running Supabase instance with url and key (```SUPABASE_URL``` and ```SUPABASE_KEY```) in .env file or environment variables
* Running Google Cloud Storage Bucket with name (```BUCKET_NAME```) defined in .env file or environment variables

## Run Locally
```
$ pip install -r requirements.txt

# Only necessary once
$ python -m venv venv

# Run in virtual environment
$ source venv/bin/activate

# Run app
$ functions-framework --target=process_coral_upload --debug

# Example image upload
$ curl --location 'http://127.0.0.1:8080/' \
--form 'image=@"/C:/Users/kenis/Downloads/Corals Daniek/CR_IslaLarga_T08_c001_A.JPG"' \
--form 'coral_id="1"' \
--form 'site_name="Isla Larga"'
```
