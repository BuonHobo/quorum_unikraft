import json

from provinew.deployment.Deployment import Deployment
import asyncio
import logging

with open("provinew/deployment.json") as f:
    data = json.load(f)
    dep = Deployment(data)
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dep.quorum.consensus.deploy())
