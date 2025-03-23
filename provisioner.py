import json

from provisioner.deployment.Deployment import Deployment
import asyncio

with open("provisioner/deployment.json") as f:
    data = json.load(f)
    dep = Deployment(data)
    asyncio.run(dep.quorum.consensus.deploy())
