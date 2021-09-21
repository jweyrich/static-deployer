from typing import List
from botocore.config import Config
from botocore.exceptions import ClientError
from io import IOBase
import boto3
import os
import mimetypes
import logging
import hashlib
# import base64
from common import log, types


TTL_1YEAR = 31556926
# TTL_1MINUTE = 60


# Original source: https://stackoverflow.com/a/3431838/298054
def hash_file(file: IOBase) -> str:
    hash_impl = hashlib.md5()
    # with open(file_name, "rb") as f:
    for chunk in iter(lambda: file.read(65536), b""):
        hash_impl.update(chunk)
    return hash_impl.hexdigest()


def upload_file(file_name: str, bucket_name: str, object_name: str, dry_run: bool = False) -> bool:
    """Upload a file to an S3 bucket.

    This will use a managed transfer which will perform a multipart upload
    in multiple threads if necessary.

    :param file_name: File to upload
    :param bucket_name: BucketDetails to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :param dry_run: if True, do not actually perform the action.
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Retry configuration
    # See https://boto3.amazonaws.com/v1/documentation/api/latest/guide/retries.html
    config = Config(
        retries = {
            'max_attempts': 3,
            'mode': 'standard',
        }
    )

    # Upload the file
    client = boto3.client('s3', config=config)
    try:
        with open(file_name, "rb") as fileobj:
            # hash_string = hash_file(fileobj)
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/customizations/s3.html#boto3.s3.transfer.S3Transfer.ALLOWED_UPLOAD_ARGS
            cache_seconds = TTL_1YEAR
            content_type, content_encoding = mimetypes.guess_type(file_name)
            extra_opts = {
                # 'ContentMD5': base64.b64encode(hash_string),
                'CacheControl': f'public, max-age={cache_seconds}',
                'ContentType': f'{content_type}{"; {content_encoding}" if content_encoding else ""}',
            }
            log.debug(f'\'{file_name}\' -> \'s3://{bucket_name}/{object_name}\' extra_opts={extra_opts}')
            if not dry_run:
                response = client.upload_fileobj(fileobj, bucket_name, object_name, ExtraArgs=extra_opts)
    except OSError as e:
        logging.error(e)
        return False
    except ClientError as e:
        logging.error(e)
        return False
    return True


def upload_files(root_dir: str, bucket_name: str, file_mappings: List[types.FileMapping], dry_run: bool = False) -> bool:
    for mapping in file_mappings:
        local_path = os.path.join(root_dir, mapping.local_path)
        success = upload_file(local_path, bucket_name, mapping.remote_path, dry_run=dry_run)
        if not success:
            return False
    return True
