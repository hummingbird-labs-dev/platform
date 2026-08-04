"""Airflow DAG skeleton that runs the etl-ynab image using KubernetesPodOperator.
Replace image name and arguments as needed.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

with DAG(
    dag_id='ynab_etl',
    schedule_interval='@daily',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={'retries': 2, 'retry_delay': timedelta(minutes=5)},
) as dag:

    run_etl = KubernetesPodOperator(
        task_id='run_etl_container',
        name='ynab-etl-run',
        namespace='default',
        image='REPLACE_WITH_IMAGE:latest',
        cmds=['python','-m','etl.main'],
        get_logs=True,
    )

    run_etl
