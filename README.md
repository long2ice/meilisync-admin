# meilisync-admin

This is a web admin dashboard for [meilisync](https://github.com/long2ice/meilisync), providing a user-friendly
interface to manage meilisync.

## Features

- Support multiple source and meilisearch instances.
- Support Sync task management.
- Admin management and access control.
- Action logs audit.
- i18n support.
- Feature request and technical support.
- More features coming soon.

## Demo

Check the demo at: https://meilisync-admin-demo.long2ice.io

- **email**: `demo@meilisync.com`
- **password**: `demo`

## Screenshot

![meilisync-admin](./images/meilisync-admin.png)

## Deployment

We recommend using [docker-compose](https://docs.docker.com/compose/) to deploy meilisync-admin.

```yaml
version: "3"
services:
  meilisync-admin:
    image: ghcr.io/long2ice/meilisync-admin/meilisync-admin
    restart: always
    network_mode: host
    environment:
      - DB_URL=mysql://root:password@localhost:3306/meilisync_admin
      - REDIS_URL=redis://localhost:6379/0
      - SECRET_KEY=secret
      - SENTRY_DSN=
```

## Frontend

The frontend of `meilisync-admin` is written in [Vue.js](https://vuejs.org/), you can find the source code
at [meilisync-web](https://github.com/long2ice/meilisync-web).

## License

This project is licensed under the
[Apache-2.0](https://github.com/meilisync/meilisync/blob/main/LICENSE) License.
