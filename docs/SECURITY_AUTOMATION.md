# Security Automation

Cairn ships GitHub-native security automation by default:

| Concern | Source of truth |
| --- | --- |
| Dependency update PRs | [../.github/dependabot.yml](../.github/dependabot.yml) |
| Lockfile freshness | [../Makefile](../Makefile), [../.github/workflows/security.yml](../.github/workflows/security.yml) |
| Vulnerability scanning | [../.github/workflows/security.yml](../.github/workflows/security.yml) |
| Secret scanning | [../.github/workflows/security.yml](../.github/workflows/security.yml), [../.pre-commit-config.yaml](../.pre-commit-config.yaml) |

Dependabot is the default updater because it is built into GitHub and covers both
Poetry-managed Python dependencies and GitHub Actions versions. If a downstream
application needs Renovate policies, replace the Dependabot config rather than
running both bots against the same dependency graph.

The security workflow runs on pull requests, pushes to `master`, a weekly
schedule, and manual dispatch. It keeps local development fast by leaving
network-backed vulnerability and secret scans in CI while keeping the cheap
lockfile freshness check in `make check`.
