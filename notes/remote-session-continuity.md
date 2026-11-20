# Lose the SSH connection, keep the build running

20 November 2026 · MOTSELL Engineering

A laptop can disconnect halfway through a build. If the build is running inside a named tmux session on the remote machine, reopening SSH need not mean starting over. We tested that on a small Linux VM, using the same synthetic Next.js project as our [sizing lab](dev-sizing-lab.md).

## What happened

The isolated local VM ran Ubuntu 24.04.5 ARM64, 2 vCPU, 4 GiB configured RAM, Node.js 24.22.3, Next.js 16.4.6 and tmux 3.4. The test used two actual SSH client terminations, not just a manual detach.

| Stage | Attached clients | Observed result |
| --- | ---: | --- |
| Build started | 1 | Build running |
| First SSH connection lost | 0 | Same build continued |
| Build completed | 0 | Exit 0; local app started |
| Reconnected over SSH | 1 | Same tmux session and running app |
| Second SSH connection lost | 0 | HTTP checks still passed |
| Reconnected again | 1 | Same session and app; HTTP checks passed |

The build kept its identity across the first disconnect. The same app returned successful home-page and API responses at all four app checkpoints, and the source tree stayed unchanged throughout. The HTTP checks were inside the guest, not over the Internet.

## Try it with your own development project

On a remote Linux machine where tmux is installed, open SSH and create a named session:

```sh
tmux new-session -s dev
```

Run your build inside that session. To leave deliberately without stopping it, press `Ctrl-b`, then `d`. After reconnecting over SSH:

```sh
tmux list-sessions
tmux attach-session -t dev
```

If `dev` no longer exists, check what happened before restarting the job. See the [official tmux guide](https://github.com/tmux/tmux/wiki/Getting-Started#attaching-and-detaching).

## What this does not prove

This was one small fixture on a local VM, not a MOTSELL VPS performance test. It did not test Claude Code, VS Code Remote SSH, server reboot, an Internet outage or application uptime under traffic. tmux is useful for surviving a client disconnect while the server stays up; it is not a backup or a service supervisor.

MOTSELL Engineering maintains this note and offers self-managed Linux VPS. If you're choosing a machine for remote development, see our [VPS configurations and monthly cost calculator](https://motsell.com/en/vps-development?utm_source=github&utm_medium=repository&utm_campaign=remote_continuity_20261120&utm_content=lab_note#calculator).
