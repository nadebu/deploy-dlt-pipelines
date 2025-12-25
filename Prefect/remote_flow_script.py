import os

import dlt
from prefect_gcp import GcpCredentials
from prefect_github import GitHubCredentials

from prefect import flow, task


def set_github_path_env():
    pat = GitHubCredentials.load("github-pat").token.get_secret_value()
    os.environ["SOURCES__SUCCESS_TOKEN"] = pat


def make_bq_destination():
    # get service account info
    gcp = GcpCredentials.load("gcp-creds")
    creds = gcp.service_account_info.get_secret_value() or {}

    # get project id
    project = creds.get("project_id")

    # create a bigquery destination
    return dlt.destinations.bigquery(credentials=creds, project_id=project)


@task(log_prints=True)
def run_resource(resource_name: str, bq_dest: dlt.destinations.bigquery):
    import github_pipeline

    source = github_pipeline.github_source.with_resources(resource_name)
    pipeline = dlt.pipeline(
        pipeline_name=f"github_remote_demo_{resource_name}",
        destination=bq_dest,
        dataset_name="demo_remote_github",
        progress="log",
    )

    info = pipeline.run(source)
    print(f"{resource_name} -> {info}")
    return info


@flow(log_prints=True)
def main():
    # set env variables
    set_github_path_env()

    # create bigquery destination
    bq_dest = make_bq_destination()

    a = run_resource("repos", bq_dest)
    b = run_resource("contributors", bq_dest)
    c = run_resource("releases", bq_dest)
    return a, b, c


if __name__ == "__main__":
    main()
