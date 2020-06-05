#!/bin/bash
#
# Builds and deploys the autograder image to Google Cloud Run.
# Note: before using this script, you need to
#   (1) Install Google Cloud SDK and log in using 'gcloud init' command
#   (2) Configure deployment-specific environment by copying and editing
#
#       cp docker/cloud-run.env.template docker/cloud-run.env
#       edit docker/cloud-run.env
#
# Usage:
#
#   docker/deploy-cloud-run.sh
#

function @execute() { echo "$@" >&2; "$@"; }

DIR="$(dirname "$0")"
set -e

if [ ! -f "$DIR/cloud-run.env" ]; then
  echo "Please copy docker/secret.env.template " >&2
  echo "to docker/cloud-run.env and customize it." >&2
  exit 1
fi

source "$DIR/cloud-run.env"

# Note: you will need to configure Docker and GCloud integration as described
# in https://cloud.google.com/container-registry/docs/advanced-authentication,
# e.g. by running 'gcloud auth configure-docker'.
"$(dirname "$0")/build-docker-image.sh"
@execute docker tag "${DOCKER_IMAGE?}" asia.gcr.io/${GCP_PROJECT?}/"${DOCKER_IMAGE?}"
@execute docker push asia.gcr.io/${GCP_PROJECT?}/"${DOCKER_IMAGE?}"

@execute gcloud run deploy \
  "${DOCKER_IMAGE?}" \
  --image asia.gcr.io/${GCP_PROJECT?}/"${DOCKER_IMAGE?}" \
  --allow-unauthenticated \
  --platform=managed \
  --region asia-northeast1 \
  --set-env-vars=GCP_PROJECT="${GCP_PROJECT?}",\
CLIENT_SECRET="$CLIENT_SECRET",\
CLIENT_ID="$CLIENT_ID",\
LOG_BUCKET="$LOG_BUCKET",\
SERVER_URL="$SERVER_URL",\
HASH_SALT="$HASH_SALT",\
COOKIE_AUTH_KEY="$COOKIE_AUTH_KEY",\
COOKIE_ENCRYPT_KEY="$COOKIE_ENCRYPT_KEY",\
JWT_KEY="$JWT_KEY"

echo OK
