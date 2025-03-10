#!/bin/bash
NUM_NODES=3
export NUM_NODES

./stop.sh
./initialize.sh
./start.sh
