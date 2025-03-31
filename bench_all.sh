#!/bin/bash

for d in $(find deployments -type f); do python experiment.py $d; done
