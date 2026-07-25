# Applications

Each API deployment belongs in its own directory and must be included in the
root `kustomization.yaml` only after its image and configuration are ready.

Use `../packages/spring-boot-api` as the starting point for a private Spring
Boot API. The overlay must:

- Set an immutable image tag or digest.
- Set `namespace: applications`.
- Provide non-sensitive runtime configuration with a `ConfigMap` or
  `configMapGenerator`.
- Use the package's `ClusterIP` service; do not add an `Ingress` or
  `LoadBalancer` for the first private API.
- Add a narrow `NetworkPolicy` allow rule once the API's in-cluster callers are
  known.

Do not commit credentials. Introduce a managed external-secret integration only
when the API requires sensitive configuration.
