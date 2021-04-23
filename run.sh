#!/bin/bash

mkdir -p log

for ((i = 1; i <= $1; i++)); do
  screen -dmS common-crawl-"$i" sh -c "source activate;conda activate common-crawl; python src/main.py >> log/log-$i.log 2>&1;"
done
