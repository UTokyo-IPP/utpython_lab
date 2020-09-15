#!/bin/bash

set -e

bazel build ...
docker/build-docker-image.sh
./build-student.sh
