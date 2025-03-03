#!/bin/bash
NUM_NODES=2
export NUM_NODES

./stop.sh
./initialize.sh
./start.sh
