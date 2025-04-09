#!/bin/sh

cd ./webui
npm run build
cd ./dist
FILES_TO_COPY=`find . | grep "gz$\|ico$\|png$"`
TARGET_PATH="../../insighioNode/www"

echo "cleaning up old files"
rm -rf $TARGET_PATH/*

echo "Preparing target folder"
mkdir -p $TARGET_PATH/assets

for FILE in $FILES_TO_COPY
do
    if [ -f $FILE ]; then
        echo "Copying $FILE"
        cp $FILE $TARGET_PATH/$FILE
    fi
done

cd ..
echo "Done"