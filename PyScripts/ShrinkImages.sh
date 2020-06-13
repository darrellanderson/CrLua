#!/bin/bash

while read -r line
do
    filename=$( printf "%s" "$line" | tr -cs 'a-zA-Z0-9' '_' )
    src="/Users/darrell/t.images/$filename"
    dst="/Users/darrell/t.images2/$filename"
    sips -s format jpeg -s formatOptions 80 "$src" --out "$dst"
done
