# A fresh Caddy volume broke local HTTPS while Postgres kept its data

The row was still in Postgres. The HTTPS client refused the connection.

We ran a small recovery drill on our Docker Compose starter at MOTSELL Engineering. The setup had Caddy, a Python app and PostgreSQL. A synthetic `/probe` endpoint read one known row. A client on the same private Docker network checked both the server certificate and that row. [Compose starter](https://motsell.com/en/vps-docker?utm_source=github&utm_medium=referral&utm_campaign=caddy_ca_rehearsal_20261125&utm_content=lab_starter#docker-quick-start)

## Three changes and one row

| Change | Result |
|---|---|
| Recreated all three containers with the same volumes | The original CA still worked and `/probe` returned the row over HTTPS. |
| Recreated Caddy with an empty `/data` volume | The client rejected the certificate. With the new CA, it could read the same row. |
| Reattached Caddy's original `/data` volume | The original CA worked again. The client using the temporary CA failed verification. |

A separate SQL query found the same row in every phase. Caddy's CA fingerprint changed only while the empty volume was attached. That was enough to break the client even though the application and its data were still there.

## What to check after a restore

If you use Caddy's internal CA, check the client with its existing trust configuration before declaring the service back. Then make that client read something known from the application. If the database survived but the client rejects TLS, check which `/data` volume Caddy is using. Keep the CA private key in protected storage. Use only the public root certificate on the verifying client.

We ran this on one disposable Ubuntu ARM64 guest with Caddy 2.11.9 and PostgreSQL 17.12. The client verified the hostname and certificate chain using a supplied local root. We published no ports. Public DNS, ACME and copying a backup to another host would need their own drills. [Caddy's local HTTPS documentation](https://caddyserver.com/docs/automatic-https#local-https)

AI assisted with the synthetic test script and drafting. The results are from the live run.
