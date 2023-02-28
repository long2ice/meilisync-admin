FROM python:3.9 as builder
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
RUN mkdir -p /meilisync_admin
WORKDIR /meilisync_admin
COPY pyproject.toml poetry.lock /meilisync_admin/
ENV POETRY_VIRTUALENVS_CREATE false
RUN pip3 install poetry && poetry install --no-root -E mysql -E postgres
COPY . /meilisync_admin
RUN poetry install -E all

FROM python:3.9-slim
WORKDIR /meilisync_admin
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /meilisync_admin /meilisync_admin
