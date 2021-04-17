#!/bin/bash

mkdir -p log
for (( i=1; i<=$1; i++ ))
do
    screen -dmS comcrawl-$i sh -c "conda activate comcrawl; python src/main.py > log/log-$i.log 2>&1;"
done
