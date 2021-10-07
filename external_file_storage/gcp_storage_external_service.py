import google.cloud.storage
import google.api_core.page_iterator
import google.oauth2.credentials
import typing

from . import base_external_storage_service

"""
GCPStorage is a google-cloud-storage class.
target_bucket_name can be specified in __init__ or to be overwritten in function call.
"""


class GCPStorage(base_external_storage_service.BaseExternalStorageService):
    def __init__(self, target_bucket_name: str = None, credentials_access_key_path: str = None):
        if credentials_access_key_path:
            self.client = google.cloud.storage.client.Client.from_service_account_json(credentials_access_key_path)
        else:
            self.client = google.cloud.storage.client.Client()
        self.bucket = self.client.bucket(target_bucket_name) if target_bucket_name is not None else None

    def __get_bucket(self, target_bucket_name: str = None) -> typing.Union[str, google.cloud.storage.bucket.Bucket]:
        if not target_bucket_name and not self.bucket:
            raise Exception("Missing bucket name")
        return self.client.bucket(target_bucket_name) if target_bucket_name else self.bucket

    def store_file_path(self, origin_file_path: str, target_filepath: str, target_bucket_name: str = None):
        bucket = self.__get_bucket(target_bucket_name)
        blob = bucket.blob(target_filepath)
        blob.upload_from_filename(origin_file_path)

    def store_file_content(self, content: bytes, target_filepath: str, target_bucket_name: str = None):
        bucket = self.__get_bucket(target_bucket_name)
        blob = bucket.blob(target_filepath)
        blob.upload_from_string(content)

    def list_files(
        self, target_directory: str, delimiter: str = None, target_bucket_name: str = None
    ) -> google.api_core.page_iterator.HTTPIterator:
        bucket = self.__get_bucket(target_bucket_name)
        return self.client.list_blobs(bucket, prefix=target_directory, delimiter=delimiter)
