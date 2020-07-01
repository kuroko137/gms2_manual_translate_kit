#!/bin/sh

mkdir repo
cp ./source_html ./repo -a -r -f
cp ./source_pot ./repo -a -r -f

cd ./repo
echo repo_dir
ls
cd ../
echo master_dir
ls
