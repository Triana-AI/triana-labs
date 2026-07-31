FROM python:3.13.14-slim-bookworm@sha256:9d7f287598e1a5a978c015ee176d8216435aaf335ed69ac3c38dd1bbb10e8d64

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY container-requirements.txt /tmp/container-requirements.txt
RUN python -m pip install \
      --disable-pip-version-check \
      --no-cache-dir \
      --require-hashes \
      --requirement /tmp/container-requirements.txt \
    && rm /tmp/container-requirements.txt

COPY dist/triana-0.0.0-py3-none-any.whl /tmp/triana-0.0.0-py3-none-any.whl
RUN python -m pip install \
      --disable-pip-version-check \
      --no-cache-dir \
      --no-deps \
      /tmp/triana-0.0.0-py3-none-any.whl \
    && rm /tmp/triana-0.0.0-py3-none-any.whl

USER 65532:65532
WORKDIR /workspace
ENTRYPOINT ["triana"]
