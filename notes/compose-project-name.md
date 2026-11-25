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

## Compare the two resolved configurations

On 25 November we repeated the four normalization runs and compared the resulting files with the released [Compose Check 0.2.0](https://github.com/motsell/compose-check/releases/tag/v0.2.0).

| Configuration pair | Changed physical volume names | Changed physical network names | Other review cues |
| --- | ---: | ---: | --- |
| Default project names | 3 | 2 | Project name, build context, bind mount source |
| Same explicit project name | 0 | 0 | Build context, bind mount source |

The explicit project name removed the volume and network name changes. It did not remove the differences in local file paths. Both comparisons exited with code 1, indicating important review cues, not a failed restore.

To compare your own private normalized JSON files, use the [offline browser tool](https://motsell.com/tools/motsell-compose-check-en.html?utm_source=github&utm_medium=repository&utm_campaign=compose_check_20261119&utm_content=project_name_compare) or install the reviewed release package from GitHub. The npm registry's 0.1.0 version still checks a single snapshot; comparison requires 0.2.0. No Docker daemon or database was started in this test.

## Why this matters before a migration

On the same Docker host, a new project name can allocate a different volume if that name does not exist. The old volume may still be present. Check the original project identity and actual volume names before redeployment; do not remove the old volume while investigating.

On a different VPS, matching names do not copy any data. A consistent external database backup and a tested restoration are still required. This experiment did not connect to a Docker daemon, run containers, create volumes, test live migration or restore a database.

Official references: [Compose project names](https://docs.docker.com/compose/how-tos/project-name/), [named volumes](https://docs.docker.com/reference/compose-file/volumes/), [Compose config](https://docs.docker.com/reference/cli/docker/compose/config/).

Planning a VPS move? [Docker/PostgreSQL starter and recovery guide](https://motsell.com/en/vps-docker?utm_source=github&utm_medium=repository&utm_campaign=compose_project_name_20261120&utm_content=lab_note#docker-quick-start). MOTSELL operates a self-managed Linux VPS service; this configuration check works independently of any hosting provider.
