import json
import sys
from pathlib import Path

from provisioner.deployment.Deployment import Experiment

with Path(sys.argv[1]).open() as f:
    data = json.load(f)
    exp = Experiment(data).run()
