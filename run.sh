#!/bin/bash

for ((i = 1; i <= $1; i++)); do
  screen -dmS common-crawl-"$i" bash -c "source activate;conda activate common-crawl; python src/main.py;"
done
