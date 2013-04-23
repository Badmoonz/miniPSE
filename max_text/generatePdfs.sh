#!/bin/bash

if [ $# -eq 1 ]; then
  cd $1
elif [ $# -gt 1 ]; then
  echo "Usage generatePdfs [path]"
fi

DOTS=`ls *.dot`
for I in $DOTS
do
  FILENAME="${I%.*}"
  dot -Teps $I > "$FILENAME.eps"
  epstopdf "$FILENAME.eps"
  rm "$FILENAME.eps"
done
