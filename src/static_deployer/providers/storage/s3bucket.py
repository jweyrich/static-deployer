from typing import List
from botocore.config import Config
from botocore.exceptions import ClientError
from io import IOBase
import boto3
import os
import mimetypes
import multiprocessing
import logging
import hashlib
# import base64
from ...common import log, types


# Original source: https://stackoverflow.com/a/3431838/298054
def hash_file(file: IOBase) -> str:
    hash_impl = hashlib.md5()
    # with open(file_name, "rb") as f:
    for chunk in iter(lambda: file.read(65536), b""):
        hash_impl.update(chunk)
    return hash_impl.hexdigest()


def upload_file(file_name: str, bucket_name: str, object_name: str, options: types.UploadOptions, dry_run: bool = False) -> bool:
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
            content_type, content_encoding = mimetypes.guess_type(file_name)
            extra_opts = {
                # 'ContentMD5': base64.b64encode(hash_string),
            }
            if options and options.cache_maxage is not None:
                extra_opts = {
                    **extra_opts,
                    'CacheControl': f'public, max-age={options.cache_maxage}',
                }
            if content_type:
                extra_opts = {
                    **extra_opts,
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


def task_upload_file(root_dir: str, bucket_name: str, file_mapping: types.FileMapping, options: types.UploadOptions, dry_run: bool = False) -> bool:
    local_path = os.path.join(root_dir, file_mapping.local_path)
    return upload_file(local_path, bucket_name, file_mapping.remote_path, options, dry_run=dry_run)


def upload_files(root_dir: str, bucket_name: str, file_mappings: List[types.FileMapping], options: types.UploadOptions, dry_run: bool = False) -> bool:
    num_concurrent_tasks = multiprocessing.cpu_count() * 2
    logging.info(f'Will use {num_concurrent_tasks} concurrent tasks')
    pool = multiprocessing.Pool(processes=num_concurrent_tasks)

    all_results = [ pool.apply_async(task_upload_file, (root_dir, bucket_name, mapping, options, dry_run,)) for mapping in file_mappings ]
    logging.info(f'Waiting for {len(all_results)} tasks to finish')
    # Wait for all tasks to complete
    [result.wait() for result in all_results]
    # Return True if all elements of the iterable are true (or if the iterable is empty).
    success = all(all_results)
    logging.info(f'All {len(all_results)} tasks have finished, final result is {"success" if success else "failure"}')
    return success


def file_exists(bucket_name: str, path: str) -> bool:
    try:
        client = boto3.client("s3")
        response = client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=path,
            MaxKeys=1)
        object_list = response.get('Contents', []);
        return len(object_list) > 0
    except ClientError as e:
        logging.error(e)
        return False


def directory_exists(bucket_name: str, path: str) -> bool:
    if not path.endswith('/'):
        path = path + '/'
    return file_exists(bucket_name=bucket_name, path=path)
