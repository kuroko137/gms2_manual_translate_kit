#!/bin/sh

mkdir repo
cp ./tr_sources ./repo -a -r -f

cd ./repo
echo repo_dir
ls
cd ../
echo master_dir
ls
