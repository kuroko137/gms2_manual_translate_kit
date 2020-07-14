#!/bin/sh

rm -rf generated
cp Converted/ ./generated -a -r -f
cp generated/docs ./ -a -r -f
rm -rf generated/docs

cp docs_override/docs ./ -a -r -f

mkdir -p GMS2_Japanese-master/
cp docs GMS2_Japanese-master/ -a -r -f
mv GMS2_Japanese-master/docs GMS2_Japanese-master/GMS2_Japanese-master

rm -f GMS2_Japanese-master/GMS2_Japanese-master/.nojekyll
