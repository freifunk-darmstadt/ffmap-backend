#!/bin/bash

set -e

DEST=$1


[ "$DEST" ] || exit 1

cd "$(dirname "$0")"/

# update aliases
# ...

./bat2nodes.py -A -a aliases.json -d $DEST
