import boto3
import logging

log = logging.getLogger(__name__)

client = boto3.client('workspaces', region_name="us-east-1")

def appliance_health():
	pass