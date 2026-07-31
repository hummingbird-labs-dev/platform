# 🚀 Platform

> The declarative source of truth for the Hummingbird Labs Kubernetes platform.

This repository defines the desired state for cluster services and application delivery: GitOps configuration, shared platform capabilities, and workload deployments. All changes are version-controlled so they can be reviewed, validated, reconciled, and reverted.

> ⚠️ **Status**: This repository is being established. Configuration is ready to reconcile after [Flux setup](#setup) is completed.

## 🎯 Purpose

The platform provides a repeatable path for delivering services to Kubernetes without requiring each workload to solve cluster integration, configuration, and delivery independently.

**Includes:**

- ✅ Cluster bootstrap configuration for GitOps reconciliation
- ✅ GitOps application definitions and reconciliation boundaries
- ✅ Shared platform services (ingress, certificates, identity, secrets)
- ✅ Reusable deployment building blocks (Helm charts, Kustomize bases, policies)
- ✅ Application workload declarations and delivery configuration

## 🗂️ Repository Boundaries

`platform` owns Kubernetes-level desired state and application delivery. It does not provision underlying infrastructure or duplicate architecture documentation.

| Repository                                                                    | Responsibility                                                     |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| 🏗️ [`architecture`](https://github.com/hummingbird-labs-dev/architecture)     | System design, decisions, service catalog, operational model       |
| 🔧 [`infrastructure`](https://github.com/hummingbird-labs-dev/infrastructure) | Compute, networking, DNS, and shared infrastructure                |
| ⚙️ [`configuration`](https://github.com/hummingbird-labs-dev/configuration)   | OS configuration, machine automation, Caddy setup                  |
| ☸️ [`platform`](https://github.com/hummingbird-labs-dev/platform)             | **← YOU ARE HERE** — Kubernetes state, GitOps, services, workloads |
| 🌐 [`edge`](https://github.com/hummingbird-labs-dev/edge)                     | Caddy, TLS, DNS, reverse-proxy routing                             |
| 📊 [`observability`](https://github.com/hummingbird-labs-dev/observability)   | Telemetry, dashboards, alerts, runbooks                            |

## 📐 Delivery Model

**GitOps workflow:**

```
Pull Request → Validation → Merged State → Flux Reconciliation → Kubernetes
```

Version-controlled desired state is reconciled to the cluster by Flux controllers. Direct, untracked changes should be avoided so the repository remains the authoritative record.

## ⚡ Quick Start

### Prerequisites

- ✅ `kubectl` configured to reach your cluster
- ✅ Kubernetes cluster with `NetworkPolicy` support (Cilium, Calico, etc.)
- ✅ GitHub personal access token for the organization

### Installation

**1️⃣ Install Flux CLI and verify cluster:**

```sh
brew install fluxcd/tap/flux
flux check --pre
```

**2️⃣ Create fine-grained GitHub token:**

- Organization: `hummingbird-labs-dev`
- Repository: `platform` only
- Permissions: **Contents: Read and write**
- Store in `.env` (ignored by Git)

```sh
source .env
```

**3️⃣ Bootstrap Flux:**

```sh
flux bootstrap github \
   --token-auth \
   --owner=hummingbird-labs-dev \
   --repository=platform \
   --branch=main \
   --path=bootstrap/flux-system
```

**4️⃣ Enable platform reconciliation:**

Add `platform-kustomization.yaml` to `bootstrap/flux-system/kustomization.yaml` resources, then commit and push.

**5️⃣ Verify:**

```sh
flux get sources git -A
flux get kustomizations -A
kubectl get namespace applications
kubectl get networkpolicy -n applications
```

## 📁 Folder Structure

```
platform/
├── 🔧 bootstrap/flux-system/          Flux bootstrap & controllers
├── 📦 platform/                       Kubernetes configuration
│   ├── controllers/                   Shared cluster controllers
│   │   ├── arc/                       GitHub Actions Runner Controller
│   │   ├── metallb/                   LoadBalancer IP management
│   │   └── ingress-nginx/             Ingress routing
│   └── namespaces/                    Namespace & security policies
├── 📋 gitops/                         Flux Kustomization orchestration
├── 🚀 deployments/                    Application workloads
│   ├── platform-api/
│   ├── postgresql/
│   └── ...
├── 📦 packages/spring-boot-api/       Reusable Helm chart
└── 🔍 .github/workflows/              CI/CD validation
```

| Folder               | Purpose                                      |
| -------------------- | -------------------------------------------- |
| `bootstrap/`         | 🚀 Flux installation & sync configuration    |
| `platform/`          | ☸️ Cluster controllers, namespaces, policies |
| `gitops/`            | 📋 Orchestration & reconciliation order      |
| `deployments/`       | 📦 Workloads (APIs, databases, etc.)         |
| `packages/`          | 📚 Reusable charts & templates               |
| `.github/workflows/` | 🔍 Validation & GitOps checks                |

## 🌐 Networking & Ingress

### MetalLB & nginx-ingress Controller

The platform uses two complementary components to route external traffic to Kubernetes services:

**🔌 MetalLB** — Virtual IP Manager

- Watches for `LoadBalancer` services
- Assigns real IPs from a configured pool
- Makes IPs available on your network

**🔀 nginx-ingress Controller** — Smart Router

- Reads `Ingress` routing rules
- Configures nginx at the MetalLB-assigned IP
- Routes traffic by hostname and path
- Example: `api.example.com` → service port 8080

### Architecture Diagram

```
                   🌍 External Request
                          ↓
                   🔴 Reverse Proxy
               (Caddy or similar)
                          ↓
         ┌────────────────────────────────┐
         │   MetalLB IP Manager            │
         │   (Assigns LoadBalancer IP)     │
         └────────────────────────────────┘
                          ↓
         ┌────────────────────────────────┐
         │   nginx-ingress Controller      │
         │   • Reads Ingress rules         │
         │   • Routes by hostname/path     │
         │   • Terminates TLS             │
         └────────────────────────────────┘
                          ↓
         ┌────────────────────────────────┐
         │   Application Services         │
         │   (ClusterIP, port 8080, etc)  │
         └────────────────────────────────┘
                          ↓
         ┌────────────────────────────────┐
         │   Your Kubernetes Workloads    │
         │   (Pods, Deployments, etc)     │
         └────────────────────────────────┘
```

**Configuration Files:**

- 📍 `platform/controllers/metallb/` — MetalLB Helm chart & IP pools
- 🔀 `platform/controllers/ingress-nginx/` — nginx-ingress configuration

No additional configuration needed—just define an `Ingress` resource in your deployment!

## 🐳 Automatic Image Updates

The platform uses **Flux Image Automation** to automatically detect new container image versions from your private registry and update deployments.

### How It Works

Three Flux components work together in the `image-automation` namespace:

1. **ImageRepository** — Scans your registry every 5 minutes for new tags
2. **ImagePolicy** — Selects versions matching your criteria (e.g., SemVer)
3. **ImageUpdateAutomation** — Commits tag updates to Git automatically

**Flow:**

```
New Image Tagged → ImageRepository Detects → ImagePolicy Selects →
ImageUpdateAutomation Commits → Flux Deploys → Pods Updated
```

### Example: platform-api

The `platform-api` deployment has image automation enabled:

```yaml
# deployments/platform-api/helm-release.yaml
image:
  repository: registry.lan.hummingbirdlabs.dev/platform-api
  tag: 1.0.9 # ← Automatically updated by Flux
```

When you push `1.0.10` to `registry.lan.hummingbirdlabs.dev/platform-api:1.0.10`:

1. ImageRepository polls and finds the new tag (within 5 minutes)
2. ImagePolicy selects it as the latest SemVer match
3. ImageUpdateAutomation updates the tag in Git
4. Flux reconciles and redeploys the application
5. New pods start with the new image

### Monitoring Image Automation

**Check detected tags:**

```bash
kubectl get imagerepository -n image-automation
kubectl describe imagerepository platform-api -n image-automation
```

**Watch for automatic commits:**

```bash
git log --oneline | grep "chore(images)"
```

**Monitor deployment:**

```bash
kubectl get deployment -n applications -w
```

### Adding Image Automation to a New App

To add automatic image updates for a new application:

**1. Create ImageRepository:**

```yaml
# platform/controllers/image-automation/image-repository-<app>.yaml
apiVersion: image.toolkit.fluxcd.io/v1
kind: ImageRepository
metadata:
  name: <app>
  namespace: image-automation
spec:
  image: registry.lan.hummingbirdlabs.dev/<app>
  interval: 5m0s
```

**2. Create ImagePolicy:**

```yaml
# platform/controllers/image-automation/image-policy-<app>.yaml
apiVersion: image.toolkit.fluxcd.io/v1
kind: ImagePolicy
metadata:
  name: <app>
  namespace: image-automation
spec:
  imageRepositoryRef:
    name: <app>
  policy:
    semver:
      range: "*" # or adjust range (e.g., '1.x', '>= 1.0.0')
```

**3. Add marker to HelmRelease:**

```yaml
# deployments/<app>/helm-release.yaml
image:
  repository: registry.lan.hummingbirdlabs.dev/<app>
  tag: 1.0.0 # {"$imagepolicy": "image-automation:<app>:tag"}
```

**4. Add to kustomization:**

```yaml
# platform/controllers/image-automation/kustomization.yaml
resources:
  - image-repository-<app>.yaml
  - image-policy-<app>.yaml
  # (ImageUpdateAutomation watches all deployments path automatically)
```

**5. Commit and push** — the rest happens automatically!

### Versioning Strategies

Customize version selection by changing the ImagePolicy `range`:

```yaml
# All versions
policy:
  semver:
    range: '*'

# Only patch updates (e.g., 1.0.x)
policy:
  semver:
    range: '1.0.x'

# Only minor and patch (e.g., 1.x, skip 2.0.0)
policy:
  semver:
    range: '<2'

# Specific constraint
policy:
  semver:
    range: '>= 1.0.0, < 2.0.0'
```

### Troubleshooting

**ImageRepository not detecting tags:**

- Check registry connectivity: `kubectl logs -n flux-system deployment/image-reflector-controller`
- Verify image name and registry URL exactly match
- Ensure credentials are configured if registry requires auth

**ImageUpdateAutomation not committing:**

- Verify Git token has write permissions
- Check logs: `kubectl logs -n flux-system deployment/image-automation-controller`
- Ensure image tag marker comment is present and formatted correctly

**Commits pushed but deployment not updating:**

- Verify HelmRelease is watching the repository: `kubectl get helmrelease -A`
- Check for conflicts in Git that prevent fast-forward merges
- Restart the kustomize-controller if CRDs were recently added

---

## 🚀 Adding a Spring Boot API

The first API should be a **private, stateless workload**:

- ✅ Reachable only inside the cluster
- ✅ No ingress, load balancer, or database
- ✅ Health checks configured

### API Requirements

Your container image must:

- 🔧 Listen on port **8080**
- 👤 Run as a **non-root user**
- 📁 Support a **read-only root filesystem** with `/tmp` available
- 💚 Expose Spring Boot Actuator endpoints:
  - `/actuator/health/liveness`
  - `/actuator/health/readiness`

### Deployment

Create a `HelmRelease` in `deployments/<api-name>/`:

```yaml
apiVersion: helm.toolkit.fluxcd.io/v1
kind: HelmRelease
metadata:
  name: platform-api
  namespace: flux-system
spec:
  interval: 10m
  releaseName: platform-api
  targetNamespace: applications
  chart:
    spec:
      chart: ./packages/spring-boot-api
      reconcileStrategy: Revision
      sourceRef:
        kind: GitRepository
        name: flux-system
        namespace: flux-system
  values:
    nameOverride: platform-api
    image:
      repository: ghcr.io/hummingbird-labs-dev/platform-api
      tag: "1.0.0"
```

Then add to `deployments/kustomization.yaml` with a narrow network policy.

## 📋 Operating Principles

- 🔍 **Desired state is reviewed state** — All changes via pull requests
- 🔄 **Reuse over repetition** — Shared packages, not copied configuration
- 🛡️ **Safe delivery by default** — Versioned, health-checked, rollback-friendly
- 🔐 **Security first** — No credentials, internal endpoints, or topology in Git
- 📊 **Observability built-in** — Integrate with observability repository

### Application secrets (managed by Infisical)

Workloads in the `applications` namespace consume secrets via native
Kubernetes `Secret` objects that are continuously reconciled from the
self-hosted Infisical instance by the
[Infisical Secrets Operator](platform/controllers/secrets-operator).
Authentication uses
[Kubernetes Auth](https://infisical.com/docs/documentation/platform/identities/kubernetes-auth):
Infisical validates a short-lived ServiceAccount token via the cluster's
`TokenReview` API, so no client secrets are stored in Git.

#### Shared platform bootstrap

Once, at the platform level (`platform/controllers/infisical-bootstrap/`), the
repository defines:

- `ServiceAccount infisical-secrets` in `applications` — shared by every
  app in that namespace.
- `ClusterRoleBinding` to `system:auth-delegator` on that SA — lets
  Infisical validate the client's own token (no long-lived reviewer JWT).
- `Secret infisical-identity` — holds the single machine identity ID used
  by every app in `applications`.
- `InfisicalConnection infisical` — points at the cluster-internal
  Infisical service.
- `InfisicalAuth applications` — the shared K8s auth CR that every
  `InfisicalStaticSecret` in the namespace references.

One placeholder must be filled in after the Infisical UI setup:

| Placeholder | File | Where to get it |
| --- | --- | --- |
| `REPLACE_WITH_MACHINE_IDENTITY_ID` | `platform/controllers/infisical-bootstrap/identity-secret.yaml` | Infisical UI → Access → Identities → `applications-k8s` → Identity ID |

#### One-time Infisical UI setup

1. Create a Machine Identity called `applications-k8s` at the
   **Organization** level:
   - Delete the default Universal Auth method.
   - Add **Kubernetes Auth** with:
     - Kubernetes host: `https://kubernetes.default.svc.cluster.local`
     - Token Reviewer JWT: *leave empty* (client-JWT self-review)
     - Allowed service account names: `infisical-secrets`
     - Allowed namespaces: `applications`
     - Verify TLS Certificate: off (PoC; can be tightened later)
2. Copy the Identity ID into
   `platform/controllers/infisical-bootstrap/identity-secret.yaml` and commit.

#### Onboarding a new app

For each application that needs secrets from Infisical:

1. **In Infisical UI**: use the shared `Hummingbirdlabs.dev` project
   (one project, all apps). Ensure the `prod` environment exists, add
   this app's secrets — either at path `/` or under a folder like
   `/<app>` if you want isolation. The shared `applications-k8s`
   identity is already attached with **Viewer** role, so new apps get
   read access automatically. Copy the Project Slug (visible in the
   URL bar while inside the project, e.g. `hummingbirdlabs-dev-a1b2`).
2. **In this repo**: add a single `infisical.yaml` file under the app's
   directory containing only an `InfisicalStaticSecret` (see
   `applications/homepage/infisical.yaml` as the canonical example). Set:
   - `spec.sources[0].projectSlug` to the Project Slug from step 1.
   - `spec.sources[0].secretPath` to `/` or `/<folder>` matching where
     the secrets live in Infisical.
   - `spec.targets[0].name` to the K8s Secret name the app's Deployment
     already reads via `envFrom`.
   - **Recommended:** always use `spec.targets[0].template` to
     *explicitly* project only the keys this app needs. This decouples
     what a folder holds from what a single app sees, so you can safely
     store many shared secrets in one folder (e.g. `/lan/hostnames`)
     without leaking unrelated values into every consumer's Secret.
     Access each source value as `{{ .KEY_NAME.Value }}`.

   Example template pattern:

   ```yaml
   targets:
     - name: <app>-secret
       kind: Secret
       creationPolicy: Owner
       template:
         engineVersion: v1
         data:
           APP_URL: "{{ .APP_URL.Value }}"
           # only the keys this app actually needs
   ```
3. **In the app's kustomization**: add `- infisical.yaml` to `resources`.
4. Commit; the operator will create and refresh the target Secret every
   60s. Roll the app to pick up the values:

   ```sh
   kubectl rollout restart deployment/<app> -n applications
   ```

The app's `Deployment` and other manifests do not change — the operator
simply becomes the thing that produces the `Secret` that `envFrom`
already references.

### Platform API ingress host

For `applications/platform-api`, keep the ingress hostname in `applications/platform-api/.env` and generate the Secret in `applications`:

```sh
kubectl create secret generic platform-api-secret \
  -n applications \
  --from-env-file=applications/platform-api/.env \
  --dry-run=client -o yaml | kubectl apply -f -
```

Then reconcile the release with:

```sh
kubectl apply -k applications/platform-api
```

### Infisical bootstrap secrets

The self-hosted Infisical instance in `platform/controllers/infisical` requires a
Kubernetes Secret named `infisical-secrets` in the `infisical` namespace. It holds
`AUTH_SECRET`, `ENCRYPTION_KEY`, `SITE_URL`, and `ALLOW_INTERNAL_IP_CONNECTIONS`.
Keep values in `platform/controllers/infisical/.env` (gitignored) using
[`.env.example`](platform/controllers/infisical/.env.example) as a template:

```sh
openssl rand -base64 32           # → AUTH_SECRET
openssl rand -hex 16              # → ENCRYPTION_KEY
```

Create the Secret **before** Flux reconciles the HelmRelease (otherwise the
Infisical pods will crash-loop waiting for it):

```sh
kubectl create namespace infisical --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic infisical-secrets \
  -n infisical \
  --from-env-file=platform/controllers/infisical/.env \
  --dry-run=client -o yaml | kubectl apply -f -
```

> ⚠️ **Store `ENCRYPTION_KEY` outside the cluster.** Without it, encrypted data in
> the Infisical database cannot be recovered — even from a backup.

The bundled in-cluster PostgreSQL and Redis are **not** highly available. Their
data is persisted via **two hand-provisioned `PersistentVolume` objects**
(`platform/controllers/infisical/persistent-volumes.yaml`) that map to
directories on node `k8s-node-1`:

| Component | PV name | Host path on `k8s-node-1` | Size |
| --------- | --------------------- | ------------------------- | ---- |
| Postgres  | `infisical-postgres`  | `/opt/infisical/postgres` | 8 Gi |
| Redis     | `infisical-redis`     | `/opt/infisical/redis`    | 8 Gi |

Both PVs use a dedicated non-provisioning `StorageClass` called
`infisical-manual` (`provisioner: kubernetes.io/no-provisioner`), so no
dynamic provisioner is needed and no other workload can accidentally claim
these volumes. The Postgres and Redis pods are pinned to `k8s-node-1` via
`nodeAffinity` on the PVs; node failure will make the data unavailable
until `k8s-node-1` returns. Suitable for proof-of-concept only.

Before Flux reconciles for the first time, create the host directories on
`k8s-node-1`:

```sh
sudo mkdir -p /opt/infisical/postgres /opt/infisical/redis
sudo chmod 0700 /opt/infisical/postgres /opt/infisical/redis
```

Infisical is exposed via the existing `ingress-nginx` controller at the hostname configured in
`platform/controllers/infisical/helm-release.yaml` (`ingress.hostName`), which
must match `SITE_URL`.

## 🗺️ Roadmap

| Phase            | Goal                                                      |
| ---------------- | --------------------------------------------------------- |
| 1️⃣ **Bootstrap** | Install Flux, establish GitOps reconciliation             |
| 2️⃣ **Services**  | Deploy shared platform services (ingress, certs, secrets) |
| 3️⃣ **Workloads** | Add reusable patterns, deploy applications                |
| 4️⃣ **Controls**  | Policies, validation, promotion, recovery docs            |

## 🤝 Contributing

Keep changes:

- ✅ Focused and declarative
- ✅ Reviewed and validated
- ✅ Free of credentials and topology

Refer to [`architecture`](https://github.com/hummingbird-labs-dev/architecture) for platform decisions.
