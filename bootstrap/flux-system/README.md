# Flux bootstrap

Flux is the in-cluster GitOps controller. It watches this repository and
reconciles the Kubernetes configuration that has been merged to `main`.

## Bootstrap process

1. Create a fine-grained GitHub personal access token authorized for the
   `hummingbird-labs-dev` organization. Restrict it to the `platform`
   repository and grant **Contents: Read and write** and **Administration:
   Read and write**; Flux uses the latter to register its repository deploy
   key. If the organization requires SAML SSO, authorize the token for the
   organization. Do not store the token in this repository:

   ```sh
   export GITHUB_TOKEN='...'
   ```
2. Run the following from a workstation with access to the target cluster:

   ```sh
   flux bootstrap github \
     --owner=hummingbird-labs-dev \
     --repository=platform \
     --branch=main \
     --path=bootstrap/flux-system
   ```

   The `--owner` value is the organization; do not use Flux's `--personal`
   flag. By default, Flux registers an SSH deploy key for this repository.

3. The command creates and commits Flux-generated controller and sync manifests
   in this directory. Review that commit.
4. Add `platform-kustomization.yaml` to the generated
   `bootstrap/flux-system/kustomization.yaml` resource list, commit the change,
   and let Flux reconcile it.

The `platform` Kustomization then reconciles `gitops/`, which in turn applies
platform baselines and application declarations. Check reconciliation status
with:

```sh
flux get kustomizations
```

The target cluster name, authentication method, and bootstrap identity belong
in the relevant architecture and infrastructure documentation. Do not include
credentials or sensitive cluster connection details here.
