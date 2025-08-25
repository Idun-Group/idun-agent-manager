from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="IDUN_MANAGER_", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/idun_manager"
    traefik_entrypoint: str = "web"
    docker_network: str = "idun_network"
    artifact_registry_type: str = "local"  # local|gcr|ghcr|ecr
    deployment_type: str = "local"  # local|gcp|k8s

    # Optional credentials for cloud providers
    gcp_project_id: str | None = None
    gcp_region: str | None = None
    gcp_service_account_json: str | None = None

    # Registry credentials
    registry_url: str | None = None
    registry_username: str | None = None
    registry_password: str | None = None
