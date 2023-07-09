FROM node as frontend-builder
ARG GIT_TOKEN
RUN git clone https://$GIT_TOKEN@github.com/long2ice/meilisync-web.git /meilisync-web
WORKDIR /meilisync-web
RUN npm install && npm run build

FROM python:3.11 as builder
RUN mkdir -p /meilisync_admin
WORKDIR /meilisync_admin
COPY pyproject.toml poetry.lock /meilisync_admin/
ENV POETRY_VIRTUALENVS_CREATE false
RUN pip3 install pip --upgrade && pip3 install poetry --upgrade --pre && poetry install --no-root --only main

FROM python:3.11-slim
WORKDIR /meilisync_admin
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY . /meilisync_admin
COPY --from=frontend-builder /meilisync-web/dist /meilisync_admin/static
CMD ["python", "-m", "meilisync_admin.app"]
