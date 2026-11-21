# Uptime Kuma 2 restore drill with docker-volume-backup

We restored an Uptime Kuma monitor into a fresh Docker volume and checked two things in the running app. Its original successful check was present, and the restored monitor wrote a new successful check. Both checks were necessary to distinguish a working restore from a service that merely started.

## What we ran

We used Uptime Kuma 2.5.12 with SQLite and `offen/docker-volume-backup` 2.49.3 on local Linux arm64 containers. The test monitor checked Kuma's own loopback HTTP endpoint. The containers had no external network, and the backup container had no Docker socket. The data, account and monitor were synthetic.

1. Make one successful monitor check and note its timestamp. Stop the source Kuma instance cleanly. The monitoring gap lasts until your source or target is running again.
2. Mount the full source `/app/data` volume read-only at `/backup/kuma` in the backup container. Run the tool's manual backup into a separate archive location.
3. Restore the contents beneath `backup/kuma/` into a new empty volume. Match the original data directory layout and the runtime UID's file permissions. Keep the source volume intact until the target is verified. [Upstream restore guide](https://offen.github.io/docker-volume-backup/how-tos/restore-volumes-from-backup.html)
4. Before starting Kuma, compare the restored `kuma.db` SHA-256 with the stopped source and run SQLite `PRAGMA integrity_check` against the restored copy. We checked that the source's WAL had no remaining writes before comparing the DB.
5. Start the same Kuma image with the restored volume mounted at `/app/data`. Check the monitor identity and the previous check timestamp in the app, then wait for a new successful check.

For step 2, set `KUMA_VOLUME` to the volume you verified in the stopped container's mounts. Set `BACKUP_DIR` to a new private absolute directory. A mistyped volume name can cause Docker to create an empty volume.

```sh
docker run --rm --network none \
  --mount "type=volume,source=${KUMA_VOLUME:?},destination=/backup/kuma,readonly" \
  --mount "type=bind,source=${BACKUP_DIR:?},destination=/archive" \
  -e BACKUP_FILENAME=kuma-lab.tar.gz \
  --entrypoint /usr/bin/backup \
  offen/docker-volume-backup:v2.49.3@sha256:570a4bea8c19f824b22a4ce31e01afdf418a7bb616dcb17052f0a78b504ac54c
```

## Readback

The backup archive was 16,499 bytes. The SQLite file matched byte for byte before the target booted, and the integrity check returned `ok`. The restored app returned HTTP 200, reported the same active monitor, and returned these successful checks in its history.

| Check | UTC on 21 November 2026 |
| --- | --- |
| Before the backup, still present after restore | 15:01:44.923 |
| New check after restore | 15:02:14.112 |

This was a same-version local restore with one monitor. A real `/app/data` archive can contain account and monitor data. Keep it private and retain an off-host copy. Check your own notification delivery and target URLs before switching over. An upgrade or a MariaDB-backed Kuma instance needs a separate restore plan. [Kuma migration notes](https://github.com/louislam/uptime-kuma/wiki/Migration-From-v1-To-v2)

MOTSELL Engineering ran the drill. We operate a self-managed VPS service and used AI assistance for the test and write-up. If you're choosing a Linux host for an existing Compose stack, see the [Docker VPS options](https://motsell.com/en/vps-docker?utm_source=github&utm_medium=repository&utm_campaign=uptime_kuma_restore_20261121&utm_content=case_note#order).
