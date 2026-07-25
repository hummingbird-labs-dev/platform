# Platform

The declarative source of truth for the Hummingbird Labs Kubernetes platform.

This repository will define the desired state for cluster services and application
delivery: GitOps configuration, shared platform capabilities, and workload
deployments. Changes are made through version-controlled configuration so they
can be reviewed, validated, reconciled, and reverted.

> This repository is being established. The structure and workflows below
> describe the intended platform rather than components that are already running.

## Purpose

The platform provides a repeatable path for delivering services to Kubernetes
without requiring each workload to solve cluster integration, configuration, and
delivery independently.

It will contain:

- Cluster bootstrap configuration needed to establish GitOps reconciliation.
- GitOps application definitions and reconciliation boundaries.
- Shared platform services, such as ingress integration, certificate management,
  identity integration, and secrets delivery.
- Reusable deployment building blocks, including Helm charts, Kustomize bases,
  policies, and environment overlays.
- Application workload declarations and their delivery configuration.

## Repository boundaries

`platform` owns Kubernetes-level desired state and application delivery. It
does not provision the underlying infrastructure or duplicate platform-wide
architecture documentation.

| Repository                                                                 | Responsibility                                                                           |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| [`architecture`](https://github.com/hummingbird-labs-dev/architecture)     | Canonical system design, architecture decisions, service catalog, and operational model. |
| [`infrastructure`](https://github.com/hummingbird-labs-dev/infrastructure) | Foundational compute, networking, DNS, and shared infrastructure provisioning.           |
| [`configuration`](https://github.com/hummingbird-labs-dev/configuration)   | Host operating-system configuration and reusable machine automation.                     |
| [`platform`](https://github.com/hummingbird-labs-dev/platform)             | Kubernetes desired state, GitOps, shared services, and workload delivery.                |
| [`edge`](https://github.com/hummingbird-labs-dev/edge)                     | Internet-facing Caddy, TLS, DNS integration, and reverse-proxy routing.                  |
| [`observability`](https://github.com/hummingbird-labs-dev/observability)   | Telemetry stack operations, dashboards, alerts, recording rules, and runbooks.           |

Implementation details in this repository should link to the relevant
`architecture` documentation rather than recreate cross-platform designs.

## Delivery model

The target delivery model is GitOps:

```text
Pull request -> validation -> merged desired state -> GitOps reconciliation -> Kubernetes
```

GitOps controllers will reconcile the version-controlled desired state to the
cluster. Direct, untracked changes to managed resources should be avoided so
that the repository remains the authoritative record of intended platform
state.

## Setup

The initial setup installs Flux CD in a Kubernetes cluster and configures it to
reconcile this repository. The cluster must be reachable through `kubectl` and
use a CNI that enforces `NetworkPolicy` resources, such as Cilium or Calico.

1. Install the Flux CLI and confirm the cluster meets its prerequisites:

   ```sh
   brew install fluxcd/tap/flux
   flux check --pre
   ```

2. Create a fine-grained GitHub personal access token authorized for the
   `hummingbird-labs-dev` organization. Restrict it to the `platform`
   repository and grant **Contents: Read and write** and **Administration:
   Read and write**; Flux uses the latter to register its repository deploy
   key. If the organization requires SAML SSO, authorize the token for the
   organization. Expose it only in the current shell:

   ```sh
   source .env
   ```

3. Bootstrap Flux as an organization repository. This installs Flux in the
   cluster, registers an SSH deploy key with `hummingbird-labs-dev/platform`,
   and commits its generated controller and sync manifests to
   `bootstrap/flux-system/`. Do not add Flux's `--personal` flag:

   ```sh
   flux bootstrap github \
      --token-auth \
      --owner=hummingbird-labs-dev \
      --repository=platform \
      --branch=main \
      --path=bootstrap/flux-system
   ```

4. In the generated `bootstrap/flux-system/kustomization.yaml`, add
   `platform-kustomization.yaml` to `resources`, commit, and push the change.
   Flux will then reconcile `gitops/`, including the application namespace and
   its default-deny ingress policy.

5. Confirm that the source and Kustomizations reconcile:

   ```sh
   flux get sources git -A
   flux get kustomizations -A
   kubectl get namespace applications
   kubectl get networkpolicy -n applications
   ```

No application is deployed during setup. Add an API-specific overlay only once
its immutable container image and runtime configuration are ready.

## Proposed layout

```text
.
├── bootstrap/       # Initial cluster and GitOps-controller configuration
├── gitops/          # Reconciliation sources, applications, and tenancy boundaries
├── platform/        # Shared services operated for all workloads
├── applications/    # Workload declarations and delivery configuration
├── overlays/        # Environment- or cluster-specific customizations
├── packages/        # Reusable Helm charts, Kustomize bases, and common manifests
└── docs/            # Repository-specific operational and contribution documentation
```

The layout will evolve as implementation begins, but it should preserve clear
ownership, minimize duplicated manifests, and make environment differences
explicit.

## Operating principles

- **Desired state is reviewed state.** Platform changes are proposed through
  pull requests and validated before reconciliation.
- **Reuse over repetition.** Common capabilities belong in shared packages or
  platform services, not copied into individual workloads.
- **Safe delivery by default.** Workloads should use versioned configuration,
  explicit dependencies, health checks, and rollback-friendly releases.
- **Security is part of delivery.** Keep credentials, internal endpoints, and
  sensitive topology out of version control; integrate approved secret and
  identity mechanisms instead.
- **Observability is a platform concern.** Workload delivery should integrate
  with the observability capabilities operated by the `observability`
  repository.

## Roadmap

1. **Bootstrap GitOps** — Establish the initial cluster configuration and a
   reconciler that can apply version-controlled desired state.
2. **Establish shared services** — Deliver the platform capabilities required
   by workloads, with clear ownership and dependency boundaries.
3. **Onboard workloads** — Add reusable delivery patterns and migrate
   applications to declarative, reviewable deployment definitions.
4. **Strengthen delivery controls** — Add policy checks, automated validation,
   promotion patterns, and recovery documentation as the platform matures.

## Contributing

Keep changes focused, declarative, and reviewable. Refer to the
[`architecture`](https://github.com/hummingbird-labs-dev/architecture)
repository for platform-wide decisions, document repository-specific operating
details in `docs/`, and never commit credentials, private endpoints, or
sensitive network topology.
