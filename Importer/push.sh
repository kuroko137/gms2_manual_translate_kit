#!/bin/sh

time=$(TZ=UTC-9 date '+%F %R')

ZIP_PATH='Converted/GMS2_Japanese-master.zip'
NO_CHANGES=0

if [ -e $ZIP_PATH ]; then
  cp Converted/GMS2_Japanese-master.zip ./ -a -f
else
  NO_CHANGES=1
fi

rm -rf Converted
rm -rf repo
rm -rf tmp
rm -rf GMS2_Japanese-master

if [ $NO_CHANGES -eq 0 ]; then
  git pull origin master
  git add -A
  git status
  git commit -m "Update from ParaTranz: ${time}"
  git push
else
  echo 'No changes were detected. Processing is complete.'
fi
