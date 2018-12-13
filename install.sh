#!/bin/bash

set -eu

AMPY_PORT=$1; shift
PLUGIN_FILE="$*"
DEFAUT_FILE_LIST="logo.jpg main.py settings.json lib/config.py lib/mackerel.py lib/sababox.py"

for DIR in /flash/lib /flash/plugins; do
    echo "mkdir $DIR"
    ampy --port $AMPY_PORT mkdir --exists-okay $DIR
done

for SRC in $DEFAUT_FILE_LIST; do
    DST="/flash/$SRC"
    echo "put $SRC -> $DST"
    ampy --port $AMPY_PORT put $SRC $DST
done

for SRC in $PLUGIN_FILE; do
    DST="/flash/plugins/$(basename $SRC)"
    echo "put $SRC -> $DST"
    ampy --port $AMPY_PORT put $SRC $DST
done
