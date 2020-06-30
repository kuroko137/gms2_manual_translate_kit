#!/bin/sh

time=$(TZ=UTC-9 date '+%F %R')

rm -rf ./Converted
rm -rf ./repo
rm -rf ./tmp
rm -rf ./GMS2_Japanese-master/
git pull origin master
git add -A
git status
git commit -m "Update from ParaTranz: ${time}"
git push
