# Apache Airflow

Airflow orchestration platform deployed on Kubernetes using the official Airflow Helm chart with KubernetesExecutor.

## Architecture

- **Executor**: KubernetesExecutor (each task runs in its own Pod)
- **Database**: PostgreSQL (via Helm chart)
- **Scheduler**: Runs continuously to trigger DAGs
- **Webserver**: UI accessible via port 8080
- **Triggerer**: Handles asynchronous task events

## Deployment

This application is deployed via Flux HelmRelease, which manages the official Apache Airflow Helm chart:

- `helmrepository.yaml` — Flux HelmRepository pointing to the Apache Airflow Helm repo
- `helmrelease.yaml` — Flux HelmRelease defining the Airflow deployment
- `infisical.yaml` — Secrets management via Infisical (database credentials)

## Configuration

### Secrets in Infisical

Airflow pulls configuration from two Infisical paths using the `sources`/`targets` format:

**Hostnames** — `/lan/hostnames` (prod):
- Key: `AIRFLOW_URL` — Your Airflow webserver URL (e.g., `http://airflow.yourdomain.lan:8080`)

**Databases** — `/databases` (prod):
- Key: `AIRFLOW_DATABASE_CONNECTION` — PostgreSQL connection string (e.g., `postgresql://airflow:password@airflow-postgresql:5432/airflow`)
- Key: `AIRFLOW_DB_USERNAME` — PostgreSQL username (e.g., `airflow`)
- Key: `AIRFLOW_DB_PASSWORD` — PostgreSQL password

The InfisicalStaticSecret creates a single `airflow-config` Kubernetes Secret in the `applications` namespace with all keys available. The secrets-operator reconciles every 60 seconds.

### PostgreSQL Credentials

The PostgreSQL database is deployed as a subchart within the Airflow Helm release. The credentials in `helmrelease.yaml` (`postgresql.auth.username` and `password`) must match the values stored in Infisical at `/databases`.

To update credentials:
1. Update `AIRFLOW_DB_USERNAME` and `AIRFLOW_DB_PASSWORD` in Infisical at `/databases`
2. Update the matching values in `helmrelease.yaml` under `postgresql.auth`
3. The connection string in `AIRFLOW_DATABASE_CONNECTION` should also be updated to match

### Database Credentials

Database credentials are part of the `database_connection` secret. Example format:
```
postgresql://airflow:your-secure-password@postgres-hostname:5432/airflow
```

### Values Customization

To customize Airflow configuration, update the `helmrelease.yaml` file:

- Modify the `spec.values` section to override any Airflow Helm chart values
- Changes will be automatically reconciled by Flux

## DAGs

DAGs should be placed in `/opt/airflow/dags` inside the container. Currently, DAG synchronization is disabled. To enable git-sync:

```yaml
dags:
  gitSync:
    enabled: true
    repo: 'https://github.com/your-org/your-dags-repo'
    branch: main
    subPath: dags
```

## Access

- **Webserver**: `http://localhost:8080` (port-forward or configure Ingress)
- **Default user**: `admin` / `admin` (change in production)

## Scaling

### Scheduler Replicas
Increase scheduler replicas (be careful: only one should be active at a time in older versions):
```yaml
scheduler:
  replicaCount: 1
```

### Worker Resources
To adjust worker Pod resources for KubernetesExecutor tasks, modify:
```yaml
workers:
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
```

## Production Checklist

- [ ] Change default admin password
- [ ] Configure proper resource limits
- [ ] Enable Ingress with TLS
- [ ] Set up proper logging and monitoring
- [ ] Configure DAG auto-sync from Git
- [ ] Set up SMTP for email alerts
- [ ] Configure Airflow variables and connections in Infisical

## References

- [Apache Airflow Helm Chart](https://airflow.apache.org/docs/helm-chart/stable/index.html)
- [KubernetesExecutor Documentation](https://airflow.apache.org/docs/apache-airflow/stable/executor/kubernetes.html)
