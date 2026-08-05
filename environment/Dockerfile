# hash:sha256:80edfb36c5fc014388b1356a217df2b23f19380ed3e20eed24431446815619e3
# Code Ocean capsule environment (exported from the working capsule).
# Local development: use requirements.txt + Python ≥3.10; default reproduce needs only pyyaml.
FROM registry.codeocean.com/codeocean/py-r:python3.12.8-R4.4.2-JupyterLab4.3.5-RStudiorstudio-server-2024.12.1-563-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive

RUN pip install -U --no-cache-dir \
    google-genai==0.3.0 \
    matplotlib==3.11.1 \
    openai==1.40.0 \
    pyyaml==6.0.3 \
    requests==2.34.2

# Capsule layout: /code = code/; /data = data/; /results writable.
# Default Reproducible Run entry: /code/run → bash code/reproduce.sh
