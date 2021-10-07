import datetime
import os
import pathlib

from . import gcp_storage_external_service
from . import base_external_storage_service

GOOGLE_STORAGE_DEVICE_LOGS = os.environ.get('GOOGLE_STORAGE_CREDENTIALS_PATH', '{APPLIANCE_CUSTOMER_HOSTNAME}/{MSP_ID}/{DEVICE_ID}/{TIME}.blob')
GOOGLE_STORAGE_CREDENTIALS_PATH = os.environ.get('GOOGLE_STORAGE_CREDENTIALS_PATH', '/storage/secret/GCP_SA.json')


class ExternalStorageFactory:
    @staticmethod
    def get_instance(gcp_bucket_name: str) -> base_external_storage_service.BaseExternalStorageService:
        load_credentials = os.environ.get("GCP_USE_SERVICE_ACCOUNT_CREDENTIALS") == 'True'
        credentials_access_key_path = None
        if load_credentials:
            credentials_access_key_path = str((pathlib.Path(os.getcwd()).parent / GOOGLE_STORAGE_CREDENTIALS_PATH).resolve())
        return gcp_storage_external_service.GCPStorage(
            target_bucket_name=gcp_bucket_name, credentials_access_key_path=credentials_access_key_path
        )


class ExternalFileStorage():
    def __init__(self, *args, **kwargs):
        super(ExternalFileStorage, self).__init__(*args, **kwargs)
        gcp_bucket_name = os.environ.get("GCP_STORAGE_DEVICE_LOGS_BUCKET_NAME")
        self.external_storage = ExternalStorageFactory.get_instance(gcp_bucket_name)

    def store_device_blob(self, blob: bytes, msp_id: int, device_id: int):
        self.external_storage.store_file_content(
            content=blob,
            target_filepath=GOOGLE_STORAGE_DEVICE_LOGS.format(
                APPLIANCE_CUSTOMER_HOSTNAME=self.app.global_config.general.appliance_external_hostname,
                MSP_ID=msp_id,
                DEVICE_ID=device_id,
                TIME=datetime.datetime.now().isoformat(),
            ),
        )


class InternalFileStorage():
    def __init__(self, *args, **kwargs):
        super(ExternalFileStorage, self).__init__(*args, **kwargs)
        gcp_bucket_name = os.environ.get("GCP_STORAGE_DEVICE_LOGS_BUCKET_NAME")
        self.external_storage = ExternalStorageFactory.get_instance(gcp_bucket_name)

    def store_device_blob(self, blob: bytes, msp_id: int, device_id: int):
        self.external_storage.store_file_content(
            content=blob,
            target_filepath=GOOGLE_STORAGE_DEVICE_LOGS.format(
                APPLIANCE_CUSTOMER_HOSTNAME=self.app.global_config.general.appliance_external_hostname,
                MSP_ID=msp_id,
                DEVICE_ID=device_id,
                TIME=datetime.datetime.now().isoformat(),
            ),
        )