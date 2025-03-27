import json

from provisioner.deployment.Deployment import Experiment

with open("deployment.json") as f:
    data = json.load(f)
    exp = Experiment(data).run()
