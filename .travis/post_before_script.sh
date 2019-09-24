#!/usr/bin/env bash

# Tests require additional modules, but users do not need them at runtime.
# So install test requirements here, rather than in the image Dockerfile.
cat test_requirements.txt | $CMD_STDIN_PREFIX bash -c "cat > /tmp/test_requirements.txt"
$CMD_PREFIX pip3 install -r /tmp/test_requirements.txt
