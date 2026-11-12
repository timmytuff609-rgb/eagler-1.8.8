# eagler-1.8.8

In GitHub Codespaces, file changes in this repository are automatically
committed with the message `Automated update` and pushed to the current branch
on `origin` after one second without further changes. The watcher checks for
changes every second and retries failed pushes every second. This starts when
the Codespace starts; rebuild the container to apply the configuration to an
already-running Codespace.

GitHub credentials with write access to this repository must be available to
Git for pushes to succeed. If authentication fails, run `gh auth login` and
`gh auth setup-git`; the watcher retries pending pushes. The `server` directory
is a regular folder in this repository, so its non-ignored changes are pushed
to the same `origin`.
