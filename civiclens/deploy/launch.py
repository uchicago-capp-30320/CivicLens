"""Script to autodeploy CivicLens NLP jobs"""
import pydo

from civiclens.utils.constants import DIGITAL_OCEAN, SSH_ID


do_client = pydo.Client(token=DIGITAL_OCEAN)

with open("civiclens/deploy/droplet_config.yml", "r") as f:
    cloud_config = f.read()

droplet_data = {
    "name": "civiclens-nlp",
    "region": "nyc3",
    "size": "s-4vcpu-8gb",
    "image": "ubuntu-24-04-x64",
    "user_data": cloud_config,
    "ssh_keys": [SSH_ID],
    "monitoring": True,
}

# launch instance
try:
    do_client.droplets.create(body=droplet_data)
    print("Instance launched!")
except Exception as e:
    print(e)
