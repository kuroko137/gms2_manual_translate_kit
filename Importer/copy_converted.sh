#!/bin/sh

if [ ! -e ./generated ]; then
  mkdir -p ./generated
fi

cp ./Converted/* ./generated -arf
cp generated/manual/docs ./ -arf
rm -rf generated/manual/docs

GENERATE_EX=0

if [ -r ./_VERSION ]; then
  BASE_VER=`cat _VERSION`
  echo BASE_VER=$BASE_VER
  
  if [ -r ./override/_VERSION ]; then

    OVERRIDE_VER=`cat override/_VERSION`
    echo OVERRIDE_VER=$OVERRIDE_VER
  
    if [ $OVERRIDE_VER -ge $BASE_VER ]; then
      cp ./override/docs ./ -arf
    else
      echo OVERRIDE is OUTDATED. No override is done.
    fi
  fi
  
  if [ -r ./override_extra/_VERSION ]; then

    OVERRIDE_VER=`cat override_extra/_VERSION`
    echo OVERRIDE_EX_VER=$OVERRIDE_VER
  
    if [ $OVERRIDE_VER -ge $BASE_VER ]; then
      mkdir -p ./ex_tmp
      cp ./Converted_EX/manual/docs ./ex_tmp/docs -arf
      cp ./override_extra/docs ./ex_tmp -arf # 連続で同じ場所にコピーするとコピー先が変化するため直下にコピー
      rm -rf ./ex_tmp/docs/gitkeep
      cp ./Converted_EX/ide ./Converted -arf
      GENERATE_EX=1
    else
      echo OVERRIDE_EXTRA is OUTDATED. No override is done.
    fi
  fi
fi


mkdir -p ./GMS2_Japanese-master
cp ./docs ./GMS2_Japanese-master -arf
rm -rf ./GMS2_Japanese-master/docs/.nojekyll
mv ./GMS2_Japanese-master/docs ./GMS2_Japanese-master/GMS2_Japanese-master


if [ $GENERATE_EX -eq 1 ]; then
  mkdir -p ./GMS2_Japanese_Alt-master
  cp ./docs/ ./GMS2_Japanese_Alt-master -arf
  cp ./ex_tmp/docs ./GMS2_Japanese_Alt-master -arf
  rm -rf ./GMS2_Japanese_Alt-master/docs/.nojekyll
  mv ./GMS2_Japanese_Alt-master/docs ./GMS2_Japanese_Alt-master/GMS2_Japanese_Alt-master
fi

rm -rf ex_tmp
rm -rf Converted_EX
