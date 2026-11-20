# Moving a Compose project can change its database volume name

20 November 2026 · MOTSELL Engineering

We normalized the same Docker Compose project in two differently named directories. The PostgreSQL mount in `compose.yaml` stayed `pgdata:/var/lib/postgresql/data`, but Compose derived a different concrete volume name.

We used Docker Compose `v2.33.1-desktop.1` and the exact seven-file [Docker/PostgreSQL/Caddy starter ZIP](https://motsell.com/downloads/motsell-docker-postgres.zip), SHA-256:

```
f206737eefa861e1b9f198a750ad3163fd2cf9be957e0d0a9bab020bbe088c70
```

## What Compose actually resolved

| Directory | Project name option | PostgreSQL volume name |
| --- | --- | --- |
| `original-workspace` | Default | `original-workspace_pgdata` |
| `new-workspace` | Default | `new-workspace_pgdata` |
| `original-workspace` | `--project-name migration-drill` | `migration-drill_pgdata` |
| `new-workspace` | `--project-name migration-drill` | `migration-drill_pgdata` |

Caddy's two named volumes changed in the same way. The application build context and Caddyfile bind mount resolved to each new directory. All four configurations retained the private database network and no published database port.

## Reproduce the configuration check

Extract the same ZIP into two new temporary directories named `original-workspace` and `new-workspace`, so `compose.yaml` is directly inside each. Create a `synthetic.env` in each with the following **test-only** values:

```dotenv
DB_PASSWORD=synthetic-fixture-not-a-secret
SITE_ADDRESS=http://localhost
BIND_IP=127.0.0.1
```

We ran this command for each directory, targeting a deliberately nonexistent Docker daemon socket in our disposable scratch directory. It only normalizes the Compose configuration:

```bash
docker --host "unix://$scratch/no-daemon.sock" compose \
  --env-file "$directory/synthetic.env" \
  --project-directory "$directory" -f "$directory/compose.yaml" \
  config --format json
```

The second run in each directory added `--project-name migration-drill` before `config`. Inspect `.name` and `.volumes.pgdata.name` in the JSON. Ensure `$scratch` points to your own temporary directory and the socket does not exist; `$directory` is the extracted starter directory. Never publish a resolved Compose configuration from a real project: it can contain expanded secrets.

## Why this matters before a migration

On the same Docker host, a new project name can allocate a different volume if that name does not exist. The old volume may still be present. Check the original project identity and actual volume names before redeployment; do not remove the old volume while investigating.

On a different VPS, matching names do not copy any data. A consistent external database backup and a tested restoration are still required. This experiment did not connect to a Docker daemon, run containers, create volumes, test live migration or restore a database.

Official references: [Compose project names](https://docs.docker.com/compose/how-tos/project-name/), [named volumes](https://docs.docker.com/reference/compose-file/volumes/), [Compose config](https://docs.docker.com/reference/cli/docker/compose/config/).

Planning a VPS move? [Docker/PostgreSQL starter and recovery guide](https://motsell.com/en/vps-docker?utm_source=github&utm_medium=repository&utm_campaign=compose_project_name_20261120&utm_content=lab_note#docker-quick-start). MOTSELL operates a self-managed Linux VPS service; this configuration check works independently of any hosting provider.
