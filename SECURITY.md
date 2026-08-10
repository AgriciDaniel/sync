# Security Policy

## Supported Version

The private `0.1.x` line is currently supported. Older snapshots are not
maintained.

## Reporting

Use a private GitHub security advisory. Do not open an issue containing a
credential, exploit detail, private run artifact, local path, or client data.
If the advisory surface is unavailable, contact the repository owner through a
previously verified private channel.

Include the affected revision, a minimal sanitized reproduction, impact, and a
suggested verification command. Do not test against third-party or production
systems without explicit authorization.

## Secret Response

If a secret reaches Git history, treat it as compromised. Revoke or rotate it at
the provider first, then remove it from reachable history and verify every
remote reference. Deleting only the working-tree file is insufficient.

## Release Controls

Release gates scan source files and archives for common API keys, private keys,
OAuth tokens, local home paths, unsafe links, unreviewed raw material, and
forbidden ZIP entries. These are deterministic defenses, not proof that
arbitrary content is secret-free.
