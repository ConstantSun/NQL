#!/bin/bash
site_package_dir="/usr/local/lib/python3.8/site-packages"
work_dir="/python-docker"
dependencies=("awscli" "awscli-1.27.162.dist-info" "boto3" "boto3-1.26.162.dist-info" "botocore" "botocore-1.29.162.dist-info")

pip install -r requirements.txt

for dependency in "${dependencies[@]}"; do
    cp -r "$work_dir/dependencies/$dependency" $site_package_dir
done
