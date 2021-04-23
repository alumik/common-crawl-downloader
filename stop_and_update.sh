#!/bin/bash

for scr in $(screen -ls | awk '{print $1}'); do
  screen -S "$scr" -X stuff '^C'
done

rm -r log

git fetch --all
git reset --hard origin/main
git pull

chmod +x ./*.sh
