# UTPython Lab
The Colaboratory notebook files for UTPython, the Introduction to Python Programming course at the University of Tokyo.
https://sites.google.com/view/ut-python/

# Text Book
https://utokyo-ipp.github.io/toc.html

# How to set up development environment

Install the Python 3 virtualenv:

```shell
virtualenv -p python3 venv
. venv/bin/activate
pip install jupyter prog_edu_assistant_tools
```

Install Bazel (http://bazel.build) and build
the notebooks:

```shell
bazel build ...
```

# Build the student notebooks

```shell
./build-student.sh
```

The Jupyter version of the student notebooks can be found in `tmp/student`,
and Colab version of the student notebooks is in `tmp/colab_student`.

# Build the deployment image

```shell
docker/build-docker-image.sh
```

# Run the service locally for testing

```shell
docker/start-local-server.sh
```

# Deploy the autograder to Google Cloud Run

   * Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install), including Go support.
   * Authorize and configure the GCP project by running
     ```
     gcloud init
     ```
   * Create a [Cloud Storage](https://console.cloud.google.com/storage/browser) bucket for storing logs
   * Enable [Google Cloud Run](https://cloud.google.com/cloud-build/docs/deploying-builds/deploy-cloud-run)
   * Create a [OAuth2 client ID](https://console.cloud.google.com/apis/credentials) and download
     it in JSON format.
   * Create a RSA private key for JWT signing. There are multiple ways of doing that,
     for example, using the `keytool.go` from http://github.com/google/prog-edu-assistant:
     ```
     cd ../prog-edu-assistant
     go run go/cmd/keytool/keytool.go \
       --action createkey \
       --output_private_key jwt.priv \
       --output_public_key jwt.pub
     ```
     Another option is to use `openssl` command:
     ```
     openssl genrsa -out jwt.priv 2048
     ```
     Copy the private key file to Google Cloud storage (any bucket is okay):
     ```
     gsutil cp jwt.priv gs://<bucket-name>/
     ```

   * Copy the file `docker/cloud-run.env.template` to `docker/cloud-run.env` and fill in
     the details. You may need to skip the SERVER_URL if you do not know the deployment
     URL yet.

   * Run the deployment command:
     ```
     ./docker/deploy-cloud-run.sh
     ```

   * If it was the first time to deploy, find the deployment URL in the
     [Google Cloud console](https://console.cloud.google.com/run/detail/asia-northeast1/utpython-autograder/metrics),
     and update `SERVER_URL` in `docker/cloud-run.env`. You also need to edit the Colab submission
     snippet (`preamble.py`), update the server URL and rebuild the student Colab notebooks.

# How to run the integration tests

This repository includes a script for quickly sending a few requests to a locally running instance
of autograder backend to verify that it can handle canonical and non-canonical submissions correctly.
The contents of the submission is automatically constructed from two parts:

   * The student notebook provides the template of the ipynb file (because each submission uploads
     the full .ipynb file that student is workin on).

   * The master notebook provides submission code snippets: canonical solutions are those marked
     with `%%solution` magic, and non-canonical submissions are those marked with `%%submission`.
     The canonical solutions are expected to result in passed tests. For non-canonical submission
     snippets, the script expect to find a python snippet with assertions in a cell immediately
     following the `%%submission` snippet.

Run the integration tests:

```shell
# Start the local autograder backend (Docker based):
docker/start-local-server.sh
```

Wait until the backend is ready. It will build the Docker image and report the URL
it is listening at. The test assumes the URL is `http://localhost:8000'.

```shell
# Build the student notebooks and extract them to ./tmp/student:
./build-student.sh
# Run the integration tests:
./test-all.sh
```

Note, that the above command prints the outcomes of submissions, which occasionally
contains error messages. This is by design, as the integration test sends not only
correct submissions, but incorrect submissions too. To understand whether the integration
test itself passed or failed, you need to look for the final `OK` message printed
by the script and check the status code of the script.

       
