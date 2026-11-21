# How much disk does a compressed SQL backup need to restore?

21 November 2026 · MOTSELL Engineering

Two SQL backups differed in compressed size by a factor of about 144. After restoring them, both SQLite databases had exactly the same number of pages. The archive sizes alone would suggest very different disk needs.

## What we measured

We created two small databases with Python 3.9.6 and SQLite 3.43.2. Each had 512 synthetic rows, a 2,688-byte ASCII text value per row, an integer primary key and an index on the text. One contained repeated text; the other contained deterministic, varied text. Both databases and dumps stayed in memory, with no customer data or network requests.

| Measurement | Repeated text | Varied text |
| --- | ---: | ---: |
| Logical UTF-8 SQL dump (bytes) | 1,396,254 | 1,396,254 |
| Gzip-compressed dump (bytes) | 5,478 | 789,110 |
| Restored database pages (4,096 bytes each) | 1,091 | 1,091 |
| Restored database page bytes | 4,468,736 | 4,468,736 |

Both restores returned all 512 rows. Each source and restored table matched in full; its index was present, and SQLite's integrity check returned `ok`.

## Reproduce the experiment

The following procedure describes the fixture, not a tool for restoring an existing server:

1. Open two new in-memory SQLite source databases. Set page size to 4,096 bytes and temporary storage to memory. Create a `messages` table with integer primary key `id` and non-null text column `body`.
2. Insert IDs 0–511. For the first database, repeat the ASCII string `order-status-pending ` exactly 128 times per row. For the second, concatenate lowercase SHA-256 hex digests of the UTF-8 strings formed as decimal row ID, a colon and decimal chunk index (0–41). Each resulting text value has 2,688 bytes.
3. Create the index `messages_body` on the `body` column and commit. Join each Python SQLite connection's `iterdump()` output with newline separators, encode as UTF-8 and compress with gzip level 6 and timestamp zero.
4. Decompress each dump into a fresh in-memory database with the same page size and temporary storage in memory. Check the ordered rows, index and `PRAGMA integrity_check`; multiply `PRAGMA page_count` by `PRAGMA page_size` to compare main-database page bytes. Exact compressed byte counts and page layout can differ with software versions.

## Before buying a destination disk

Count what must coexist on each destination filesystem: the downloaded archive, unpacked data, temporary dumps, restored databases and indexes, application/container data, temporary files and an operating reserve. Count shared items only once. Compare the result with *free space after the OS and existing software*, not the advertised disk capacity. Keep an independent verified backup elsewhere; do not delete your only copy to make space.

For a running PostgreSQL source, the [database size function](https://www.postgresql.org/docs/17/functions-admin.html#FUNCTIONS-ADMIN-DBSIZE) reports its current size, including indexes. It is not a measurement of the destination restore peak. For Restic, [restore-size](https://restic.readthedocs.io/en/stable/manual_rest.html#getting-information-about-repository-data) estimates logical restored data. Neither includes every byte your application may need at restoration time. If major sizes or temporary-space needs are unknown, disk fit is still unknown. Rehearse restoration in an isolated compatible environment before moving live traffic.

Our example measures SQLite pages in memory, not filesystem allocation, peak disk or RAM usage, WAL, PostgreSQL restoration or performance on a VPS. It demonstrates the problem with a universal archive-size multiplier; 144 is **not** a sizing factor for real backups.

References: [SQLite PRAGMA documentation](https://www.sqlite.org/pragma.html#pragma_page_count), [Python gzip](https://docs.python.org/3/library/gzip.html#gzip.compress).

MOTSELL Engineering operates a self-managed Linux VPS service. AI assisted with lab automation and drafting; the results were executed and independently checked. The experiment is independent of the hosting provider. Related: [Docker VPS setup and recovery guide](https://motsell.com/en/vps-docker#docker-quick-start).
