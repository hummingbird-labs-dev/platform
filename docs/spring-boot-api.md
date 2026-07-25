# Spring Boot API delivery contract

The first API is a private, stateless Kubernetes workload. It is reachable
inside the cluster through its `ClusterIP` service and is not exposed through
an ingress or load balancer.

## Application requirements

The container image must:

- Listen on port `8080`.
- Run as a non-root user.
- Support a read-only root filesystem, using `/tmp` for writable temporary
  files when needed.
- Expose Spring Boot Actuator liveness and readiness endpoints:
  `/actuator/health/liveness` and `/actuator/health/readiness`.
- Be published with an immutable image tag or digest before its deployment
  overlay is merged.

The image build, source code, and registry publishing workflow belong in the
API's own repository.

## Deployment overlay

When the API exists, create `applications/<api-name>/` with a
`kustomization.yaml` that references `../../packages/spring-boot-api`. The
overlay must use a unique name prefix and replace the package's selector labels
so that its service cannot select pods from another API:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: applications
namePrefix: inventory-
resources:
  - ../../packages/spring-boot-api
images:
  - name: application
    newName: ghcr.io/hummingbird-labs-dev/inventory-api
    newTag: "1.0.0"
labels:
  - includeSelectors: true
    pairs:
      app.kubernetes.io/name: inventory-api
```

Replace `inventory` and the image reference with the actual API details. Add
only non-sensitive configuration.

Add that directory to `applications/kustomization.yaml` only when the image is
available. This prevents Flux from attempting to deploy a placeholder image.

## Networking and telemetry

The `applications` namespace begins with default-deny ingress. Add a narrowly
scoped ingress policy for the known calling workloads at the same time as the
API overlay. Coordinate metrics scraping and dashboards with the
`observability` repository; this repository defines the workload contract, not
the telemetry stack.
