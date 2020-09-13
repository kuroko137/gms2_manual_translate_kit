#!/bin/sh

time=$(TZ=UTC-9 date '+%F %R')

rm -rf repo
rm -rf Converted
rm -rf Converted_EX
rm -rf Release
rm -rf tmp
rm -rf ex_tmp

# 生成されたものをコミット&プッシュ
git pull origin master
git add -A
git status
git commit -m "Update from ParaTranz: ${time}"
git push
