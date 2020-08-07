#!/bin/sh

time=$(TZ=UTC-9 date '+%F %R')

ZIP_PATH='Converted/GMS2_Japanese-master.zip'
ZIP_EX_PATH='Converted/GMS2_Japanese_Alt-master.zip'
IDE_PATH='Converted/ide/japanese_alt.csv'
FOUND_CHANGES=0

if [ -e $ZIP_PATH ]; then
  cp $ZIP_PATH ./ -a -f
  FOUND_CHANGES=1
fi
if [ -e $ZIP_EX_PATH ]; then
  cp $ZIP_EX_PATH ./ -a -f
  FOUND_CHANGES=1
fi
if [ -e $IDE_PATH ]; then
  cp $IDE_PATH ./generated/ide -a -f
  FOUND_CHANGES=1
fi

rm -rf Converted
rm -rf repo
rm -rf tmp
rm -rf GMS2_Japanese-master
rm -rf GMS2_Japanese_Alt-master

if [ $FOUND_CHANGES -eq 1 ]; then
  # 生成されたものをコミット&プッシュ
  git pull origin master
  git add -A
  git status
  git commit -m "Update from ParaTranz: ${time}"
  git push
  echo '::set-env name=action_state::green'
else
  # 変更が見つからず、生成されたアーカイブが削除されたため何もコミットしない
  echo 'No changes were detected. Processing is complete.'
  echo '::set-env name=action_state::yellow'
fi
