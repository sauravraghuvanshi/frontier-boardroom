"""Runtime configuration. Reads from env. Production reads from Key Vault refs."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # Foundry — agent_reference API via AIProjectClient + managed identity.
    # Local-auth is disabled on the corp sub, so no connection string / key.
    azure_foundry_project_endpoint: str = ""
    azure_foundry_iq_index_name: str = "boardroom-iq"

    # Databricks
    databricks_host: str = ""
    databricks_token: str = ""
    databricks_endpoint_claude_sonnet: str = "databricks-claude-sonnet-4-6"
    databricks_endpoint_claude_opus: str = "databricks-claude-opus-4-6"

    # Model registry — format "<provider>:<endpoint>"
    model_ceo: str = "foundry:CEO@5"
    model_cfo: str = "databricks:databricks-claude-sonnet-4-6"
    model_cmo: str = "foundry:CMO@2"
    model_cto: str = "foundry:gpt-5"
    model_legal: str = "databricks:databricks-claude-opus-4-6"

    # Storage
    azure_storage_account: str = ""
    azure_blob_container: str = "boardroom-knowledge"

    # Foundry IQ Knowledge Base — lives on the Azure AI Search service
    # (`/knowledgebases('<name>')/retrieve`), NOT the Foundry project endpoint.
    # Replaces the direct vector_store_id path (retired 2026-05-25).
    azure_foundry_kb_name: str = "boardroom-iq"
    azure_search_endpoint: str = ""
    azure_search_index: str = "boardroom-knowledge-idx"
    azure_search_knowledge_source: str = "boardroom-knowledge-ks"

    # Speech & Language (AAD-token auth — keys blocked by tenant policy on corp sub)
    azure_speech_resource_id: str = ""
    azure_speech_region: str = "centralindia"
    azure_language_endpoint: str = ""

    # Telemetry
    appinsights_connection_string: str = ""

    # Demo safety
    use_fake_debate: bool = Field(default=False)
    public_demo_limits_enabled: bool = True
    public_sessions_per_client_hour: int = Field(default=10, ge=1)
    public_sessions_global_hour: int = Field(default=100, ge=1)
    public_debates_per_client_hour: int = Field(default=3, ge=1)
    public_debates_global_hour: int = Field(default=20, ge=1)
    public_prep_turns_per_client_hour: int = Field(default=12, ge=1)
    public_prep_turns_global_hour: int = Field(default=60, ge=1)
    public_active_runs_per_client: int = Field(default=1, ge=1)
    public_active_runs_global: int = Field(default=2, ge=1)
    trust_forwarded_client_ip: bool = False
    admin_api_token: str = ""
    entra_auth_required: bool = False

    # CORS / frontend
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def model_registry(self) -> dict[str, str]:
        return {
            "CEO": self.model_ceo,
            "CFO": self.model_cfo,
            "CMO": self.model_cmo,
            "CTO": self.model_cto,
            "Legal": self.model_legal,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
