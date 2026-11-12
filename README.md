# eagler-1.8.8

In GitHub Codespaces, file changes in this repository and its `server`
submodule are automatically committed with the message `Automated update` and
pushed to the current branch on each repository's `origin` after 30 seconds
without further changes. This starts when the Codespace starts; rebuild the
container to apply the configuration to an already-running Codespace.

GitHub credentials with write access to each repository's `origin` must be
available to Git for pushes to succeed. If authentication fails, run
`gh auth login` and `gh auth setup-git`; the watcher retries pending pushes.
If you do not have write access to the server submodule's origin, use a
writable fork and update both the submodule remote and `.gitmodules`.

The `server` directory is a separate Git submodule. Changes there are pushed to
the submodule's own remote; when its commit changes, the main repository's
watcher also commits and pushes the updated submodule reference.
