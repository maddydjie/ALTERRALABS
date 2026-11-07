#!/bin/sh
# Download the public MTSamples notes and confirm they are the exact file this study used.
# Not stored in this repo because the licence is ambiguous. Credit: mtsamples.com
set -e
URL="https://raw.githubusercontent.com/socd06/medical-nlp/master/data/mtsamples.csv"
EXPECTED_MD5="d8547837775283c95b8a70119da806f8"

mkdir -p data/raw
curl -fsSL "$URL" -o data/raw/mtsamples.csv

ACTUAL_MD5=$(python3 -c "import hashlib; print(hashlib.md5(open('data/raw/mtsamples.csv', 'rb').read()).hexdigest())")
if [ "$ACTUAL_MD5" != "$EXPECTED_MD5" ]; then
    echo "md5 mismatch: got $ACTUAL_MD5, expected $EXPECTED_MD5" >&2
    exit 1
fi
echo "data/raw/mtsamples.csv ok"
