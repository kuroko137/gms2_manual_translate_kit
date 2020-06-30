#!/bin/sh

time=$(TZ=UTC-9 date '+%F %R')

git pull origin master
cp ./Converted/docs ./ -a -r -f
cp ./Converted/po ./po -a -r -f
rm -rf ./Converted
rm -rf ./repo
# rm -rf ./utf8
rm -rf ./tmp
git add -A
git status
git commit -m "Update from ParaTranz: ${time}"
git push
