# static-deployer

## How to install?

    pip3 install static-deployer

## How to deploy a static website?

    static-deployer deploy \
        --root-dir ROOT_DIR \
        --patterns PATTERNS \
        --bucket-name BUCKET_NAME \
        --distribution-id DISTRIBUTION_ID \
        --origin-name ORIGIN_NAME \
        --version VERSION

The deploy does the following:

1. Finds all files from `ROOT_DIR`, including only those that match the patterns specified in `PATTERNS` (comma separated);
2. Unside the bucket specified by `BUCKET_NAME`, creates a new folder/directory with the name specified in `VERSION`;
3. Uploads all files to the folder/directory created in step 2;
4. Changes the CloudFront distribution `DISTRIBUTION_ID` origin named `ORIGIN_NAME` to point the folder/directory created in step 2;
4. Invalidates the CloudFront distribution `DISTRIBUTION_ID` cache using the pattern `/*`;
5. Waits for the distribution changes to complete.

## How to rollback to a previous deployed version?

    static-deployer rollback \
        --bucket-name BUCKET_NAME \
        --distribution-id DISTRIBUTION_ID \
        --origin-name ORIGIN_NAME \
        --version VERSION

The rollback does the following:
1. Changes the CloudFront origin `ORIGIN_NAME` to point to a previously deployed version specified by `VERSION`.
2. Waits for the distribution changes to complete.

## Example of config file `config.toml`

```toml
dry_run = "false"

[content]
root_dir = "public"
patterns = "**"

[storage]
name = "your-website-domain.com"
prefix = "{{version}}"

[cdn]
distribution_id = "your-cloudfront-distribution-id"
origin_name = "your-cloudfront-origin-name"
```

## How to use the config file?

    static-deployer -c config.toml deploy --version VERSION

Once you have settings in a config file, you can tell static-deployer to use the config file by using the arguments `-c yourfile.toml`.
By specifying a config file, you eliminate the need of informing all parameters at every invocation. You're then required to inform only the missing parameters.
The command-line arguments override any settings you have in the config file.
