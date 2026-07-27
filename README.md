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

| Repository | Responsibility |
| --- | --- |
| 🏗️ [`architecture`](https://github.com/hummingbird-labs-dev/architecture) | System design, decisions, service catalog, operational model |
| 🔧 [`infrastructure`](https://github.com/hummingbird-labs-dev/infrastructure) | Compute, networking, DNS, and shared infrastructure |
| ⚙️ [`configuration`](https://github.com/hummingbird-labs-dev/configuration) | OS configuration, machine automation, Caddy setup |
| ☸️ [`platform`](https://github.com/hummingbird-labs-dev/platform) | **← YOU ARE HERE** — Kubernetes state, GitOps, services, workloads |
| 🌐 [`edge`](https://github.com/hummingbird-labs-dev/edge) | Caddy, TLS, DNS, reverse-proxy routing |
| 📊 [`observability`](https://github.com/hummingbird-labs-dev/observability) | Telemetry, dashboards, alerts, runbooks |

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

| Folder | Purpose |
| --- | --- |
| `bootstrap/` | 🚀 Flux installation & sync configuration |
| `platform/` | ☸️ Cluster controllers, namespaces, policies |
| `gitops/` | 📋 Orchestration & reconciliation order |
| `deployments/` | 📦 Workloads (APIs, databases, etc.) |
| `packages/` | 📚 Reusable charts & templates |
| `.github/workflows/` | 🔍 Validation & GitOps checks |

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

## 🗺️ Roadmap

| Phase | Goal |
| --- | --- |
| 1️⃣ **Bootstrap** | Install Flux, establish GitOps reconciliation |
| 2️⃣ **Services** | Deploy shared platform services (ingress, certs, secrets) |
| 3️⃣ **Workloads** | Add reusable patterns, deploy applications |
| 4️⃣ **Controls** | Policies, validation, promotion, recovery docs |

## 🤝 Contributing

Keep changes:
- ✅ Focused and declarative
- ✅ Reviewed and validated
- ✅ Free of credentials and topology

Refer to [`architecture`](https://github.com/hummingbird-labs-dev/architecture) for platform decisions.
