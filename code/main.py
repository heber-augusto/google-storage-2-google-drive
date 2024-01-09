from google.cloud import storage
import os

google_storage_json_filename = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
google_drive_json_filename = os.getenv('GD_JSON_FILE', '')

# Cliente do Google Cloud Storage
storage_client = storage.Client.from_service_account_json(json_filename)
bucket_id = os.getenv('GCP_BUCKET', '')

gs_prefix = os.getenv('GCP_PREFIX', '')


bucket_id = 'observatorio-oncologia'

# Acesse o bucket desejado
blobs = storage_client.list_blobs(
        bucket_or_name = bucket_id,
        prefix = gs_prefix)
gs_files = [blob for blob in blobs]

gs_files_list = [\
  {
      'current_path': gs_file.name.replace(f"{gs_prefix}/", ''),
      'size': int(gs_file.size)
  } \
  for gs_file in gs_files if gs_file.size > 0]

print(f"{gs_prefix} : {sum([file['size'] for file in gs_files_list])} bytes")
