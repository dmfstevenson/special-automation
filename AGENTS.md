## Fleet memory

Shared memory and global instructions live in Fleet (`~/.fleet`, private repo `dmfstevenson/fleet`).
At session start read `~/.fleet/instructions/global.md` and `~/.fleet/memory/MEMORY.md`.
Save durable facts and decisions to `~/.fleet/memory/` using `~/.fleet/skills/shared/fleet-memory/SKILL.md`,
never only in this repo or a machine-local folder.
If `~/.fleet` is missing: `git clone ssh://git@ssh.github.com:443/dmfstevenson/fleet.git ~/fleet && python3 ~/fleet/scripts/configure_host.py`.
