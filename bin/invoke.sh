#!/bin/bash

if [ -z "$umcRoot" ]; then
  umcRoot="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
fi

. $umcRoot/bin/umc


