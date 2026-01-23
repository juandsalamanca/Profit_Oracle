from cryptography.fernet import Fernet
import boto3
import os
import tempfile
from dotenv import load_dotenv
load_dotenv()

def get_client_list(client_kwargs, bucket_name):

  client_list = []
  s3_client = boto3.client('s3', **client_kwargs)

  try:

      response = s3_client.list_objects_v2(
          Bucket=bucket_name
      )

      for obj in response.get("Contents", []):
          s3_object_spl = obj["Key"].split("/")
          client = s3_object_spl[1]
          if client not in client_list:
              client_list.append(client)

  except Exception as e:
      print(e)

  return client_list

def fernet_decryption(ciphertext):

  encryption_key = os.environ["ENCRYPTION_KEY"]
  fernet = Fernet(encryption_key.encode())
  decrypted = fernet.decrypt(ciphertext)

  return decrypted.decode()

def get_last_client_snapshot(client_name, snapshot_idx):
    
    bucket_name = os.environ["AWS_S3_BUCKET"]
    client_kwargs = {
            'region_name': os.environ["AWS_REGION"],
            'aws_access_key_id': os.environ["AWS_ACCESS_KEY_ID"],
            'aws_secret_access_key': os.environ["AWS_SECRET_ACCESS_KEY"]
        }

    snapshot_list = []
    try:

        s3_client = boto3.client('s3', **client_kwargs)

        response = s3_client.list_objects_v2(
            Bucket=bucket_name
        )

        for obj in response.get("Contents", []):
            if client_name in obj["Key"] and "snapshots" in obj["Key"]:
                snapshot_list.append(obj["Key"])

    except Exception as e:
        print(e)

    
    snapshot_name = snapshot_list[snapshot_idx]
    snapshot_file_name = snapshot_name.split("/")[-1]
    local_path = f"downloads/{client_name}_{snapshot_file_name}"

    s3_client.download_file(
    Bucket=bucket_name,
    Key=snapshot_name,
    Filename=local_path
    )

    decrypted_snapshot = fernet_decryption(open(local_path, "rb").read())

    return decrypted_snapshot


if __name__ == "__main__":

    x = get_last_client_snapshot('kyle', -1)
    print(x)
