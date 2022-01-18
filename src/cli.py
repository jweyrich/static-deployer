#!/usr/bin/env python3

from stat import *
from typing import List, Set, Tuple
import os
import sys
import glob
import argparse
import re
import logging
from static_deployer.common import log, types, configuration
from static_deployer.providers.cdn import cloudfront
from static_deployer.providers.storage import s3bucket


def find_local_files(root_dir: str, glob_patterns: str) -> Set[str]:
    """Find all files existing in root_dir that match the given set of patterns.

    :param root_dir: Absolute path to the root directory where files will be searched.
    :param glob_patterns: Comma separated string containing glob patterns used to filter files.
    :return: The list of file paths matching the patterns. Contains only absolute and normalized paths.
    """
    result = []
    log.debug(f'root_dir={root_dir}')
    patterns = glob_patterns.split(',')
    for pattern in patterns:
        absolute_pattern = os.path.join(root_dir, pattern)
        matching_paths = glob.glob(absolute_pattern, recursive=True)  # recursive=True enables recursive **
        log.debug(f'  pattern=\'{pattern}\', matching_paths={matching_paths}')
        for path in matching_paths:
            # TODO: handle OSError for os.stat
            stat_info = os.stat(path)
            path_is_dir = S_ISDIR(stat_info.st_mode)
            log.debug(f'    {"DIR" if path_is_dir else "FILE"} path=\'{path}\'')
            if not path_is_dir:
                log.debug(f'    MATCH path={path}')
                result.append(path)
        # else:
        # 	for dirpath, dirnames, filenames in os.walk(path):
        # 		# Do we need to normalize the dirpath directory here?
        # 		#dirpath_normalized = os.path.normpath(dirpath)
        # 		#log.debug(f'      WALK dirpath=\'{dirpath}\', dirnames={dirnames}, filenames={filenames}')
        # 		# Skip dirnames as we are only interested in filenames.
        # 		for filename in filenames:
        # 			absolute_filepath = os.path.join(dirpath, filename)
        # 			log.debug(f'    MATCH absolute_filepath={absolute_filepath}')
        # 			result.append(absolute_filepath)

    result_set = set(result)
    len_result, len_result_set = len(result), len(result_set)
    if len(result) > len(result_set):
        logging.warning('Some files are being included more than once! Please, review your patterns!' +
                        ' len(result)=%d > len(result_set)=%d', len_result, len_result_set)
        log.debug(f'RESULT len={len(result)}, {result})')
    log.debug(f'RESULT_SET len={len(result_set)}, {result_set})')
    return result_set


def map_local_to_remote(root_dir: str, remote_prefix: str, local_files: Set[str]) -> List[types.FileMapping]:
    """Convert local file paths to remote object paths.

    :param root_dir: Absolute path to the root directory where files will be searched.
    :param remote_prefix: Prefix where remote objects will reside.
    :param local_files: List of local file paths.
    :return: A list of FileMapping's.
    """
    result = []  # Should we pre-allocate this array?
    for local_file in local_files:
        relative_local_path = os.path.relpath(local_file, root_dir)
        remote_path = os.path.join(remote_prefix, relative_local_path).replace(os.sep, '/')
        file_mapping = types.FileMapping(local_path=relative_local_path, remote_path=remote_path)
        result.append(file_mapping)
        log.debug(str(file_mapping))
    return result


def build_remote_prefix(bucket_prefix: str, version: str) -> str:
    if bucket_prefix:
        return re.sub(r'{{\s*version\s*}}', version, bucket_prefix)
    else:
        return version


def run_deploy(spec: types.DeploySpec, dry_run: bool = False) -> bool:
    logging.info(f'Deploy spec={spec.to_dict()}')
    remote_prefix = build_remote_prefix(spec.storage.prefix, spec.version)

    remote_prefix_exists = s3bucket.directory_exists(spec.storage.name, remote_prefix)
    # Prevent the deploy if the remote path already exists.
    if remote_prefix_exists:
        logging.error(f'The specified version ({spec.version}) already exists in the target storage ({vars(spec.storage)})')
        return False

    local_files = find_local_files(spec.content.root_dir, spec.content.patterns)
    file_mappings = map_local_to_remote(
        spec.content.root_dir,
        remote_prefix,
        local_files,
    )

    success = s3bucket.upload_files(spec.content.root_dir, spec.storage.name, file_mappings, dry_run=dry_run)
    if not success:
        return False

    return cloudfront.update(
        spec.cdn.distribution_id,
        spec.cdn.origin_name,
        remote_prefix,
        dry_run=dry_run,
    )


def run_rollback(spec: types.RollbackSpec, dry_run: bool = False) -> bool:
    logging.info(f'Rollback spec={spec.to_dict()}')
    remote_prefix = build_remote_prefix(spec.storage.prefix, spec.version)

    remote_prefix_exists = s3bucket.directory_exists(spec.storage.name, remote_prefix)
    # Prevent the rollback if the remote path does not exist.
    if not remote_prefix_exists:
        logging.error(f'The specified version ({spec.version}) does not exist in the target storage ({vars(spec.storage)})')
        return False

    return cloudfront.update(
        spec.cdn.distribution_id,
        spec.cdn.origin_name,
        remote_prefix,
        dry_run=dry_run,
    )


def deploy(config: configuration.ConfigOptions) -> bool:
    root_dir = os.path.abspath(config.content.root_dir)
    patterns = config.content.patterns
    bucket_name = config.storage.name
    bucket_prefix = config.storage.prefix
    distribution_id = config.cdn.distribution_id
    origin_name = config.cdn.origin_name
    version = config.version
    dry_run = config.dry_run

    content = types.ContentDetails(root_dir=root_dir, patterns=patterns)
    bucket = types.StorageDetails(name=bucket_name, prefix=bucket_prefix)
    cloudfront_dist = types.CdnDetails(distribution_id=distribution_id, origin_name=origin_name)
    spec = types.DeploySpec(content=content, storage=bucket, cdn=cloudfront_dist, version=version)
    return run_deploy(spec, dry_run=dry_run)


def rollback(config: configuration.ConfigOptions) -> bool:
    bucket_name = config.storage.name
    bucket_prefix = config.storage.prefix
    distribution_id = config.cdn.distribution_id
    origin_name = config.cdn.origin_name
    version = config.version
    dry_run = config.dry_run

    bucket = types.StorageDetails(name=bucket_name, prefix=bucket_prefix)
    cloudfront_dist = types.CdnDetails(distribution_id=distribution_id, origin_name=origin_name)
    spec = types.RollbackSpec(storage=bucket, cdn=cloudfront_dist, version=version)
    return run_rollback(spec, dry_run=dry_run)


def parse_args() -> Tuple[str, configuration.ConfigOptions]:
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',
                        help='load configuration from a specific file',
                        required=False,
                        dest='config_file',
                        type=argparse.FileType('r', encoding='UTF-8'))
    args, remaining_argv = parser.parse_known_args()

    is_config_loaded = False
    config = configuration.ConfigOptions()
    config_adapter = configuration.ConfigOptionsAdapter(config)
    if args.config_file:
        is_config_loaded = True
        config.load_from_io(args.config_file)

    subparsers = parser.add_subparsers(dest='subcommand', required=True, help='sub-command')

    cmd_deploy = subparsers.add_parser('deploy')
    cmd_deploy.add_argument('--dry-run',
                            help='do not actually perform the deploy',
                            required=False,
                            action='store_true')
    cmd_deploy.add_argument('--root-dir',
                            help='local directory holding files to deploy',
                            required=True)
    cmd_deploy.add_argument('--patterns',
                            help='comma separated glob patterns, used to filter files contained by root-dir',
                            required=True)
    cmd_deploy.add_argument('--bucket-name',
                            help='bucket name where the contents should be placed',
                            required=True)
    cmd_deploy.add_argument('--bucket-prefix',
                            help='the prefix inside the bucket where the contents should be placed',
                            required=False)
    cmd_deploy.add_argument('--distribution-id',
                            help='the cloudfront distribution id',
                            required=True)
    cmd_deploy.add_argument('--origin-name',
                            help='the cloudfront origin name',
                            required=True)
    cmd_deploy.add_argument('--version',
                            help='version to be deployed',
                            required=True)

    cmd_rollback = subparsers.add_parser('rollback')
    cmd_rollback.add_argument('--dry-run',
                              help='do not actually perform the rollback',
                              required=False,
                              action='store_true')
    cmd_rollback.add_argument('--bucket-name',
                              help='bucket name where the contents reside',
                              required=True)
    cmd_rollback.add_argument('--bucket-prefix',
                              help='the prefix inside the bucket where the contents reside',
                              required=False)
    cmd_rollback.add_argument('--distribution-id',
                              help='the cloudfront distribution id',
                              required=True)
    cmd_rollback.add_argument('--origin-name',
                              help='the cloudfront origin name',
                              required=True)
    cmd_rollback.add_argument('--version',
                              help='version to rollback to',
                              required=True)

    # If a configuration file was loaded
    if is_config_loaded:
        loaded_args = config_adapter.to_args()
        log.debug(f'loaded_args={loaded_args}')
        # For each sub-parser
        for sub_name, sub_parser in (('deploy', cmd_deploy), ('rollback', cmd_rollback)):
            # Use values from configuration file by default
            sub_parser.set_defaults(**loaded_args)

            # Reset `required` attribute when provided from config file
            # Suggested in https://stackoverflow.com/a/47904804/298054
            for action in sub_parser._actions:
                # We check if the argument was loaded from config,
                # but we also need to check whether its value is not None
                if action.dest in loaded_args and loaded_args[action.dest] is not None:
                    action.required = False

    extra_args = parser.parse_args()
    log.debug(f'extra_args={extra_args}')
    config_adapter.merge_args(vars(extra_args))
    return extra_args.subcommand, config


def main():
    subcommand, config_options = parse_args()
    success = True

    if subcommand == 'deploy':
        success = deploy(config_options)
    elif subcommand == 'rollback':
        success = rollback(config_options)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
