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

# Build the deployment image

```shell
docker/build-docker-image.sh
```

# Run the service locally for testing

```shell
docker/start-local-server.sh
```
