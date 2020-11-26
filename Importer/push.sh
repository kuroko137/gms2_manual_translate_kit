#!/bin/sh

time=$(TZ=UTC-9 date '+%F %R')

rm -rf repo
rm -rf Converted
rm -rf Converted_EX
rm -rf Preview
rm -rf Release
rm -rf tmp
rm -rf ex_tmp

# 生成されたものをコミット&プッシュ
git pull origin master
if [ -e _DISCORD_NOTIFICATION -a ! -e _COMMIT_RUN ]; then
  git add ./logs/discord_latest_notice.log
else
  rm -rf _DISCORD_NOTIFICATION
  rm -rf _COMMIT_RUN
  git add -A
fi

git status
git commit -m "Update from ParaTranz: ${time}"
git push
