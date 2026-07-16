# Coral Matcher Backend

Development and build instructions for the Coral Matcher backend.

## Prerequisites

### For Local Development
* Currently no local database setup provided. Running Supabase instance with url and key (```SUPABASE_URL``` and ```SUPABASE_KEY```) in .env file or environment variables. Also ```DATABASE_URL``` so that albemic and sqlmodel can communicate with db (classic style: postgresql://[username]:[password]@host.com:5432/postgres)
* Currently no local storage bucket setup provided. Running Google Cloud Storage Bucket with name (```BUCKET_NAME``` for bucket name and ```GOOGLE_CLOUD_PROJECT``` for google cloud project name) defined in .env file or environment variables


### For Cloud Run Deployment
* Github Actions Secrets and Variables:
    * secret ```GCP_SA_KEY```: google cloud service account key of service account deploying the application
    * secret ```SUPABASE_SERVICE_ROLE_KEY```: key of supabase service role which will be injected into cloud run container so that it can access database
    * secret ```DATABASE_URL``` so that albemic and sqlmodel can communicate with db (classic style: postgresql://[username]:[password]@host.com:5432/postgres)
    * variable ```GCP_BUCKET_NAME``` the name of the google cloud storage bucket where the coral colony images are going to be stored
    * variable ```GCP_PROJECT_ID``` the id of the google cloud project
    * variable ```GCP_STATIC_WEB_BUCKET_NAME``` the name of the google cloud storage bucket where the frontend is going to be deployed 
    * variable ```SUPABASE_URL``` the url to the supabase database


## Run Locally
### Python Environment Setup
```
# Install dependencies - this takes a while
$ conda env create -f environment.yaml
$ pip install -r requirements.txt
$ conda activate coral-matcher
```

### DB Setup
```
# only for the very intitial setup
$ alembic init migrations
# then edit alembic.ini for connection to your supabase

# to create the initial schema
$ alembic revision --autogenerate -m "Initial schema"

# actually create the database and run the migration path
$ alembic upgrade head

```
# Example to run tests
$ pytest -s test_vision.py

# Run app (from backend/)
$ cd backend 
$ functions-framework --target process_coral_upload --debug
``` 
