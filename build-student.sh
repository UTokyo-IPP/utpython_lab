#!/bin/bash
#
# A convenience script that rebuilds all student notebooks
# and prepares a directory ./tmp/ with student notebooks
# and autograder directories.

cd "$(dirname "$0")"
set -ve

rm -rf tmp/
bazel build ...
mkdir -p tmp/
# Note: tar -i flag is important as these tar files were produced by
# concatenation of multiple tar files.
tar xvfi bazel-bin/autograder_tar.tar -C tmp
mkdir -p tmp/student
tar xvfi bazel-bin/student_tar.tar -C tmp/student

if [ -f student ]; then
  cp -v student/* tmp/student/
fi
if [ -f nbextensions ]; then
  cp -rv nbextensions tmp/student/
  if [ -n "$SERVER_URL" ]; then
    perl -i -pe \
      "s,http://localhost:8000/upload,$SERVER_URL/upload,g" \
      tmp/student/nbextensions/upload_it/main.js
  fi
fi
