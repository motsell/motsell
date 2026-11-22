# What an open tab sees after a Next.js release switch

The old tab reached the new page, but its earlier JavaScript URL returned 404. We measured navigation and asset availability separately because each can fail while the current release serves a working home page.

We built two versions of a small App Router app with Next.js 16.4.6 and Node 24.15.0. Both ran behind one loopback proxy on a macOS ARM64 host. Chromium 159.0.8154.6 opened `release-a`, and we switched the upstream before clicking a link with prefetch disabled. We repeated the experiment and observed the same results.

| Check | Observation |
|---|---|
| Navigation with A still active | The route fetch returned 200. Chromium stayed in the same document. |
| Navigation after the switch to B | The request carried `x-deployment-id: release-a`. B returned 200 with `x-nextjs-deployment-id: release-b`, and Chromium made a separate document request that returned 200. |
| The same JavaScript URL copied from A | The separate asset probe went **200 → 404 → 200**. A served the file, B alone lacked it, and routing that asset request back to A while B remained active restored the original bytes. The first and last checksums matched. |

Changing only the asset URL’s `?dpl=` value while B served the request left the 404 unchanged. The query parameter lets caches distinguish releases. An origin or CDN still needs the previous build’s file to answer the old URL. The reload in this run followed the deployment ID mismatch on a navigation response. [Next.js `deploymentId` documentation](https://nextjs.org/docs/app/api-reference/config/next-config-js/deploymentId)

For a staging check, keep a tab open across the switch and record the route fetch, any document request, and one build-specific JavaScript URL from before the switch. Check the old URL again while the new build serves the site. For this test we retained the previous build as an asset origin. [Next.js guidance on immutable assets](https://nextjs.org/docs/app/guides/self-hosting#immutable-assets)

For a Docker deployment, see our [Docker setup notes and Linux VPS options](https://motsell.com/en/vps-docker?utm_source=github&utm_medium=referral&utm_campaign=next_release_skew_20261122&utm_content=nextjs_showcase).

AI assisted with the synthetic test script and drafting. We checked the results in Chromium.
