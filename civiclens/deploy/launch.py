"""Script to autodeploy CivicLens NLP jobs"""
from pydo import Client

from civiclens.utils.constants import DIGITAL_OCEAN, SSH_ID


do_client = Client(token=DIGITAL_OCEAN)

with open("droplet_config.yml", "r") as f:
    cloud_config = f.read()

droplet_data = {
    "name": "civiclens-nlp-test",
    "region": "nyc3",
    "size": "s-4vcpu-8gb",
    "image": "ubuntu-24-04-x64",
    "user_data": cloud_config,
    "ssh_keys": [SSH_ID],
    "monitoring": True,
}

# launch instance
resp = do_client.droplets.create(body=droplet_data)
print(resp)
