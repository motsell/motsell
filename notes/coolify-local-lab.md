# Coolify on an isolated 8 GiB Linux VM: deploy, route and reboot

20 November 2026 · MOTSELL Engineering field note

Can a self-hosted deployment panel build and serve a small application on a fresh Linux VM even if the test has no public DNS name? We checked that path with Coolify 4.7.6, using a disposable local VM, a synthetic static application and an HTTP route that could only be reached in the lab.

## Test environment

- Ubuntu 24.04.5 LTS (ARM64), Apple VZ/Lima; 4 virtual CPUs, 8 GiB allotted RAM and 80 GiB sparse disk. This is a local lab, not a MOTSELL production VPS benchmark.
- Coolify 4.7.6, installed with the documented manual approach and versioned release files; the initial main control-plane images and the app base image were pinned. Coolify selected its own helper and proxy auxiliaries. Docker Engine 29.10.0 and Compose 5.8.0.
- Fresh guest, no host filesystem mounts. Dashboard access via a private loopback SSH tunnel. No public DNS, ACME, customer data or production credentials.

## Reproduce the application part

Start with [Coolify's official self-hosting instructions](https://coolify.io/docs/start-with-self-hosted) and a fresh supported server. The lab used the native Dockerfile application resource, not a Git provider or a third-party account. The synthetic Dockerfile below uses the ARM64 image tested in this lab; use the architecture-appropriate reviewed image on other systems.

```dockerfile
FROM busybox:1.37.0@sha256:d82c2ab94640ded77cf76514ce6a84870761105058a4a9e51b05a8a79be97a6c
RUN mkdir -p /www && printf '%s\n' 'motsell-coolify-lab-v1' > /www/index.html && chmod 755 /www && chmod 644 /www/index.html
USER 65534:65534
EXPOSE 8080
CMD ["httpd", "-f", "-p", "8080", "-h", "/www"]
```

The default domain offered by Coolify used `sslip.io`. We deliberately did not request it. In the application settings we replaced it with `http://motsell-coolify-lab.test`, a lab-only hostname, with internal port 8080. No public record was created. We confirmed the DNS mismatch warning in the UI only for this isolated HTTP setup; it is not a reason to bypass validation for a public deployment. Configure real DNS and HTTPS normally for production. See the [domain documentation](https://coolify.io/docs/core/networking/domains).

After deploying in the UI, we checked the proxy from inside the guest: the configured Host header returned HTTP 200 and the exact marker, a mismatching Host did not return that marker. The application ran as UID 65534 without any directly published application port. The guest reverse proxy was reachable only within the lab; no public host forwarding was enabled.

## Results

| Rehearsal | Observation |
| --- | --- |
| Native Dockerfile build and deploy | PASS — container running; correct local HTTP response |
| Wrong-host routing check | PASS — no application marker returned |
| Application container restart | PASS — start timestamp changed; correct marker returned again |
| Full VM stop/start | PASS — boot ID changed; the application and proxy started automatically and returned the same marker; control health returned 200 |

We did **not** verify public HTTPS/ACME, x86_64, sustained load, production capacity, application volume persistence or restoration from backups. The marker is part of the image; getting it back after a reboot is not evidence of recovery of user data. The VM was stopped after the test and synthetic backup material was retained privately.

For planning a self-managed VPS, compare CPU/RAM/disk needs and responsibility for upgrades and backups. Our [Docker VPS guide](https://motsell.com/en/vps-docker?utm_source=github&utm_medium=repository&utm_campaign=coolify_lab_20261120&utm_content=report) includes current plans and links to the Coolify and Dokploy requirements. The test above is not an installation service or a promise that every workload will fit.

MOTSELL Engineering is a VPS provider. AI assistance was used for lab automation and drafting; the stated checks were executed and reviewed.
