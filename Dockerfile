FROM node as frontend-builder
ARG GIT_TOKEN
RUN git clone https://$GIT_TOKEN@github.com/long2ice/meilisync-web.git /meilisync-web
WORKDIR /meilisync-web
RUN npm install && npm run build

FROM python:3.11 as builder
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
RUN mkdir -p /meilisync_admin
WORKDIR /meilisync_admin
COPY pyproject.toml poetry.lock /meilisync_admin/
ENV POETRY_VIRTUALENVS_CREATE false
COPY . /meilisync_admin
RUN poetry install

FROM python:3.11-slim
WORKDIR /meilisync_admin
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /meilisync_admin /meilisync_admin
COPY --from=frontend-builder /meilisync-web/dist /meilisync_admin/static
CMD ["python", "-m", "meilisync_admin.app"]
