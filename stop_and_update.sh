#!/bin/bash

for scr in $(screen -ls common-crawl- | awk '{print $1}'); do
  screen -S "$scr" -X stuff '^C'
done

git fetch --all
git reset --hard origin/main
git pull
