#!/bin/bash

if [ ! -e _COMMIT_RUN ]; then
  # 変更が見つからないため処理を中断
  echo "action_state=yellow" > _ENV_ACTION_STATE
  echo 'NO CHANGES FOUND. The process was aborted.'
  exit
fi

rm -rf _COMMIT_RUN

if [ ! -e _VERSION ]; then
  echo "action_state=yellow" > _ENV_ACTION_STATE
  echo '_VERSION cannot be found. The process was aborted.'
  exit
fi

BASE_VER=`cat _VERSION`
RELEASE_VAR=`echo ${BASE_VER} | sed -e "s/^\([0-9]\+\)\([0-9]\)\([0-9]\)/\1.\2.\3/"`
FOUND_TAG=0

echo "BASE_VER = ${BASE_VER}"

LIST=`git ls-remote --tags`

for LINE in $LIST
do
    if expr "${LINE}" : "refs/tags/${BASE_VER}" > /dev/null; then
      echo "var_matched! = ${BASE_VER} : ${LINE}"
      FOUND_TAG=1
      break
    fi
done

if [ $FOUND_TAG -eq 0 ]; then
  git tag $BASE_VER
  git push origin --tags
  echo "TAG PUSH!"
fi

echo "release_tag=${BASE_VER}" > _ENV_TAG
echo "release_ver=${RELEASE_VAR}" > _ENV_VER


if [ ! -e ./generated ]; then
  mkdir -p ./generated
fi

cp ./Converted/* ./generated -arf
cp generated/manual/docs ./ -arf
rm -rf generated/manual/docs
rm -rf generated/manual/cnv_csv
rm -rf generated/manual/cnv_po

GENERATE_EX=0

if [ -r ./_VERSION ]; then
  BASE_VER=`cat _VERSION`
  echo BASE_VER=$BASE_VER
  
  if [ -r ./override/_VERSION ]; then

    OVERRIDE_VER=`cat override/_VERSION`
    echo OVERRIDE_VER=$OVERRIDE_VER
  
    if [ $OVERRIDE_VER -ge $BASE_VER ]; then
      cp ./override/docs ./ -arf
      find ./docs -name 'git_noadd_*' | xargs rm
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
      find ./ex_tmp -name 'git_noadd_*' | xargs rm
      rm -rf ./ex_tmp/docs/gitkeep
      GENERATE_EX=1
    else
      echo OVERRIDE_EXTRA is OUTDATED. No override is done.
    fi
  fi
fi


cp ./docs ./Release -arf
rm -rf ./Release/docs/.nojekyll
mv ./Release/docs ./Release/YoYoStudioRoboHelp
cd Release/YoYoStudioRoboHelp
zip -r ../YoYoStudioRoboHelp.zip ./
cd ../../
rm -rf ./Release/YoYoStudioRoboHelp

echo "action_state=green" > _ENV_ACTION_STATE


if [ $GENERATE_EX -eq 1 ]; then
  cp ./docs ./Release -arf
  cp ./ex_tmp/docs ./Release -arf
  rm -rf ./Release/docs/.nojekyll
  mv ./Release/docs ./Release/YoYoStudioRoboHelp
  cd Release/YoYoStudioRoboHelp
  zip -r ../YoYoStudioRoboHelp_Alt.zip ./
  cd ../../
  rm -rf ./Release/YoYoStudioRoboHelp
fi


if [ -e ./Preview ]; then
  cp ./Preview/* ./docs -arf
  rm -rf ./docs/whxdata/search_db.js
  rm -rf ./docs/whxdata/search_auto_map_0.js
  rm -rf ./docs/whxdata/search_auto_model_0.js
  rm -rf ./docs/whxdata/search_topics.js
  rm -rf ./docs/whxdata/text
fi


STATS=`sed -n 2p ./logs/update_stats.csv`
IFS="$(echo -e '\t')"
set -- $STATS

if [ $5 ]; then
  echo "discord_message=${1} - オンラインヘルプに翻訳を反映: ${4}% (+${6}%, ${5} 行, ${7} 語)" > _ENV_DISCORD_MESSAGE
else
  echo "discord_message=${1} - オンラインヘルプに翻訳を反映: ${4}%" > _ENV_DISCORD_MESSAGE
fi
