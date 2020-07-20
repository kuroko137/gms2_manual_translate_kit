#!/bin/sh


rm -rf generated
cp Converted/ ./generated -a -r -f
cp generated/docs ./ -a -r -f
rm -rf generated/docs

GENERATE_EX=0

if [ -r ./_VERSION ]; then
  BASE_VER=`cat _VERSION`
  echo BASE_VER=$BASE_VER
  
  if [ -r ./override/_VERSION ]; then

    OVERRIDE_VER=`cat override/_VERSION`
    echo OVERRIDE_VER=$OVERRIDE_VER
  
    if [ $OVERRIDE_VER -ge $BASE_VER ]; then
      cp ./override/docs ./ -a -r -f
    fi
  fi
  
  if [ -r ./override_extra/_VERSION ]; then

    OVERRIDE_VER=`cat override_extra/_VERSION`
    echo OVERRIDE_EX_VER=$OVERRIDE_VER
  
    if [ $OVERRIDE_VER -ge $BASE_VER ]; then
      if [ -e Converted_EX ]; then
        cp ./Converted_EX/docs/ ./ex_tmp -a -r -f
      fi
      cp ./override_extra/docs/* ./ex_tmp/ -a -r -f
      rm -rf ./ex_tmp/.gitkeep
      GENERATE_EX=1
    fi
  fi
fi


mkdir -p ./GMS2_Japanese-master
cp ./docs ./GMS2_Japanese-master -a -r -f
rm -rf ./GMS2_Japanese-master/docs/.nojekyll
mv ./GMS2_Japanese-master/docs ./GMS2_Japanese-master/GMS2_Japanese-master


if [ $GENERATE_EX -eq 1 ]; then
  mkdir -p ./GMS2_Japanese_Alt-master
  cp ./docs ./GMS2_Japanese_Alt-master -a -r -f
  cp ./ex_tmp/* ./GMS2_Japanese_Alt-master/docs -a -r -f
  rm -rf ./GMS2_Japanese_Alt-master/docs/.nojekyll
  mv ./GMS2_Japanese_Alt-master/docs ./GMS2_Japanese_Alt-master/GMS2_Japanese_Alt-master
fi

rm -rf ex_tmp
rm -rf Converted_EX
