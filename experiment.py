import json

from provinew.deployment.Deployment import Deployment
import asyncio

with open("provinew/deployment.json") as f:
    data = json.load(f)
    dep = Deployment(data)
    asyncio.run(dep.quorum.deploy())
