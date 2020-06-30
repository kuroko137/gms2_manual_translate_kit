#!/bin/sh

cp Converted/docs ./ -a -r -f
cp Converted/po ./ -a -r -f
cp Converted/csv ./ -a -r -f

mkdir -p GMS2_Japanese-master/
cp docs GMS2_Japanese-master/ -a -r -f
mv GMS2_Japanese-master/docs GMS2_Japanese-master/GMS2_Japanese-master

rm -f GMS2_Japanese-master/GMS2_Japanese-master/.nojekyll
