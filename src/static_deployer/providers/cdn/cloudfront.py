from typing import List
import boto3
import datetime
import logging


def invalidate_paths(distribution_id: str, paths_to_invalidate: List[str], dry_run: bool = False) -> bool:
    client = boto3.client('cloudfront')
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    if not dry_run:
        response = client.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths_to_invalidate),
                    'Items': paths_to_invalidate,
                },
                # A value that you specify to uniquely identify an invalidation request.
                # CloudFront uses the value to prevent you from accidentally resubmitting
                # an identical request.
                'CallerReference': timestamp,
            }
        )

        invalidation_id = response.get('Invalidation', {}).get('Id', '')
    else:
        invalidation_id = 'fake-invalidation-id'

    logging.info(f'Waiting for invalidation ({invalidation_id}) to complete...')
    if not dry_run:
        waiter = client.get_waiter('invalidation_completed')
        # This can take up to `Delay * MaxAttempts` seconds.
        waiter.wait(
            DistributionId=distribution_id,
            Id=invalidation_id,
            # WaiterConfig={
            # 	'Delay': 30, # Wait N seconds between attempts.
            # 	'MaxAttempts': 60 # Try at most N times.
            # },
        )
    logging.info(f'Invalidation ({invalidation_id}) completed')

    return True


def update_distribution(distribution_id: str, origin_name: str, new_origin_path: str, dry_run: bool = False) -> bool:
    client = boto3.client('cloudfront')
    if not dry_run:
        # About the `get_distribution` method:
        # 1. If the distribution was not found, it throws `CloudFront.Client.exceptions.NoSuchDistribution`
        # 2. If the user has no permission to describe the distribution, it throws `CloudFront.Client.exceptions.AccessDenied`
        response = client.get_distribution(Id=distribution_id)
        distribution_etag = response.get('ETag', '')
        distribution_config = response \
            .get('Distribution', {}) \
            .get('DistributionConfig', {})
        all_origins = distribution_config \
            .get('Origins', {}) \
            .get('Items', [])
        filtered_origins = list(filter(lambda origin: origin.get('Id') == origin_name, all_origins))
        if len(filtered_origins) == 0:
            logging.error(f'Could not find origin with origin_name={origin_name} in distribution_id={distribution_id}')
            return False

        new_origin_path = new_origin_path if new_origin_path.startswith('/') else '/' + new_origin_path
        # Update the OriginPath to the new version path
        filtered_origins[0]['OriginPath'] = new_origin_path

        # Update the distribution config
        response = client.update_distribution(
            DistributionConfig=distribution_config,
            Id=distribution_id,
            IfMatch=distribution_etag,
        )

    logging.info(f'Waiting for distribution ({distribution_id}) update to complete...')
    if not dry_run:
        waiter = client.get_waiter('distribution_deployed')
        # This can take up to `Delay * MaxAttempts` seconds.
        waiter.wait(
            Id=distribution_id,
            # WaiterConfig={
            # 	'Delay': 30, # Wait N seconds between attempts.
            # 	'MaxAttempts': 60 # Try at most N times.
            # },
        )
    logging.info(f'Distribution ({distribution_id}) update completed')

    return True


def update(distribution_id: str, origin_name: str, new_origin_path: str, dry_run: bool = False) -> bool:
    success = update_distribution(
        distribution_id,
        origin_name,
        new_origin_path=new_origin_path,
        dry_run=dry_run,
    )
    if not success:
        return False

    success = invalidate_paths(distribution_id, paths_to_invalidate=['/*'], dry_run=dry_run)
    return success
