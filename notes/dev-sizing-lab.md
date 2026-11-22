# Next.js on 4 and 8 GiB: why a single build benchmark can mislead

20 November 2026 · MOTSELL Engineering field note

We wanted to find out whether a small Next.js project actually needs a larger development VM. The first comparison appeared to show a dramatic improvement. Returning to the original configuration told a different story. Here are all the observations, including the repeat on the smaller machine.

## Setup

One isolated local ARM64 Ubuntu 24.04.5 VM on Apple VZ/Lima, stopped and resized in sequence: A1 (2 vCPU, 4 GiB), B (4 vCPU, 8 GiB), A2 (2 vCPU, 4 GiB). Same virtual disk, kernel 6.8.0-147-generic, Node 24.22.3, npm 11.19.1, Next.js 16.4.6, React 19.3.1 and TypeScript 5.9.3. No swap. This was not a hosted VPS or an x86-64 benchmark.

The intentionally small [synthetic fixture](dev-sizing-lab/fixture/) has 12 statically generated note pages, a client-side filter, a local SVG and one dynamic JSON endpoint. No database, external fonts, AI model calls, private code or credentials. The locked dependencies were installed once; source and lock hashes remained identical through the three VM configurations.

In each block we ran three pairs: a build after deleting the generated `.next` directory, immediately followed by a build leaving `.next` in place. The second case is called a repeat build here, not a proven cache hit. Dependency install time and OS page-cache flushing are outside this test. Wall time was measured using a monotonic clock; Linux guest-wide `MemAvailable` was sampled every 100 ms. It includes the guest kernel, cache and other guest processes: it is not peak application RSS or a cgroup memory high-water mark.

## All results

Seconds, three observations per cell; median in bold.

| Sequence | Configuration | Clean-directory build (s) | Repeat build (s) | Lowest sampled `MemAvailable` during builds (MiB, rounded down) |
| --- | --- | --- | --- | ---: |
| A1 | 2 vCPU / 4 GiB | 10.422, 9.727, 10.712 — **10.422** | 4.050, 3.845, 7.058 — **4.050** | 2,863 |
| B | 4 vCPU / 8 GiB | 3.928, 3.223, 3.024 — **3.223** | 1.313, 1.407, 1.311 — **1.313** | 6,754 |
| A2 | 2 vCPU / 4 GiB | 4.626, 3.819, 3.928 — **3.928** | 1.512, 1.412, 1.412 — **1.412** | 2,893 |

All 18 builds exited successfully; no guest OOM kills. Both configurations served the expected home and note pages, local asset and exact JSON from localhost, and returned 404 for a deliberate missing note. An initial smoke assertion on A1 was corrected because React inserted a markup comment inside the expected marker; the same built application passed the corrected smoke test. The build measurement code was unchanged. The original A1 build observations are retained rather than discarded.

## What the numbers mean

If we'd stopped after A1 and B, we could have claimed the upgrade made a clean build over three times faster. A2 on the original configuration shows why that would be misleading. The same smaller VM varied by more than twofold between blocks, and the later clean-build times overlap the observed larger-VM range. CPU and RAM also changed together. Host scheduling, time and cache effects were not isolated. None of these observations establishes a general performance advantage for a VPS plan.

For this fixture, 4 GiB completed builds with substantial sampled guest memory available. That does not make 4 GiB a universal minimum for a real project, and it doesn't test an IDE, language server, database or AI coding session. For a larger repository, measure the whole process tree, concurrent services and memory pressure; consider building in CI and deploying only runtime artifacts. The [Next.js memory guide](https://nextjs.org/docs/app/guides/memory-usage) explains why dependencies and build settings matter. [VS Code Remote SSH](https://code.visualstudio.com/docs/remote/ssh) and [Claude Code](https://code.claude.com/docs/en/setup) have separate requirements; those were not exercised here.

## Reproduce the measurement

The exact fixture, lockfile, final [benchmark harness](dev-sizing-lab/benchmark.py) and [sanitized numeric results](dev-sizing-lab/results.json) are included. The harness needs an otherwise empty, disposable ARM64 Linux VM (not an existing application server). Copy the contents of `notes/dev-sizing-lab` into a **new empty** `/home/<user>/motsell-next-sizing` directory; the harness deliberately checks that directory name and Linux architecture. Obtain Node's official `node-v24.22.3-linux-arm64.tar.xz`, verify its checksum against the [official release checksums](https://nodejs.org/dist/v24.22.3/SHASUMS256.txt) (`6e51a2ada00f0011cc266f65d98922b403d7ad88f809ca2aa615a5fe1ce6e86c` in this lab), then extract into that directory. In `fixture`, use that pinned Node on your PATH and run `npm ci --ignore-scripts --no-fund --no-audit --registry=https://registry.npmjs.org/` against the included lockfile. No install lifecycle scripts were run in the lab.

From the parent directory, run `python3 benchmark.py 2c4g` on the 2 CPU / 4 GiB guest, then stop and resize the same VM to 4 CPU / 8 GiB and run `python3 benchmark.py 4c8g`. Preserve the original `evidence` directory before another 2c4g run; the script writes profile-specific result files. Use fresh separate paths for any repeat comparison. The script removes only generated build output in its fixture and starts a loopback-only server. Use a task-owned test VM with no credentials or unrelated services; never run it against production. Results depend on your environment. No network or load-test performance is claimed.

Choosing a server for development? [Compare live VPS plans and monthly costs](https://motsell.com/en/vps-development?utm_source=github&utm_medium=repository&utm_campaign=dev_sizing_20261120&utm_content=report#calculator). Select a plan based on your own workload; these observations are not a guarantee about MOTSELL hardware or third-party service availability.

Moving a website? [Check memory and disk before choosing a VPS](https://motsell.com/en/guides/vps-for-websites?utm_source=github&utm_medium=repository&utm_campaign=dev_sizing_20261120&utm_content=website_guide). The guide covers what to measure with a web app, API and database running together.

MOTSELL Engineering operates a VPS service. AI assisted with building the synthetic fixture, test automation and drafting; the observations were executed and independently checked.
