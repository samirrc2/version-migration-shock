# Code Ocean-compatible capsule environment for the Version-Migration artifact.
# The default (keys-free) reproduction needs only Python 3.10+ and PyYAML; the
# remaining packages are for the OPTIONAL live re-collection and figure rebuild.
FROM python:3.12-slim

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash coreutils && rm -rf /var/lib/apt/lists/*

RUN pip install -U --no-cache-dir \
    pyyaml==6.0.3 \
    matplotlib==3.11.1 \
    openai==1.40.0 \
    google-genai==0.3.0 \
    requests==2.34.2

WORKDIR /code
# Default Reproducible Run (keys-free, $0):
#   bash reproduce.sh
