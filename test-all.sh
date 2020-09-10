#!/bin/bash
# An ad-hoc script to run integration tests for some notebooks.
# It assumes that:
# 1. The autograder docker image has been built
# 2. The local Docker instance of autograder is running (via docker/start-local-server.sh)
#    without authentication and serves notebook upload requests at http://localhost:8000/upload
# 3. Student version of the notebooks has been built and unpacked to tmp/student
#    (via ./build-student.sh)

cd "$(dirname "$0")"
if [[ ! -d tmp/student ]]; then
  echo "tmp/student does not exist, did you run build-student.sh?" >&2
  exit 1
fi
if [[ $(python --version 2>&1) =~ Python\ 2.* ]]; then
  echo "Default Python version is 2.x, please change environment to Python 3.x" >&2
  exit 1
fi

set -e
python python/test_integration.py --student_notebook tmp/student/1/1-1-student.ipynb --master_notebook 1/1-1.ipynb --upload_url http://localhost:8000/upload.txt
python python/test_integration.py --student_notebook tmp/student/1/1-2-student.ipynb --master_notebook 1/1-2.ipynb --upload_url http://localhost:8000/upload.txt
python python/test_integration.py --student_notebook tmp/student/1/1-3-student.ipynb --master_notebook 1/1-3.ipynb --upload_url http://localhost:8000/upload.txt
python python/test_integration.py --student_notebook tmp/student/2/2-1-student.ipynb --master_notebook 2/2-1.ipynb --upload_url http://localhost:8000/upload.txt
python python/test_integration.py --student_notebook tmp/student/2/2-2-student.ipynb --master_notebook 2/2-2.ipynb --upload_url http://localhost:8000/upload.txt
echo OK
