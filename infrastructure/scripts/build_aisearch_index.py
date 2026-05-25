"""
build_aisearch_index.py — provisions the Azure AI Search index + indexer that
backs the Foundry IQ Knowledge Base (`boardroom-iq`).

Pipeline:
  blob (<storage-account>/boardroom-knowledge)
    -> SearchIndexerDataSource (MI auth, no keys)
    -> Skillset: SplitSkill + AzureOpenAIEmbeddingSkill (text-embedding-3-small)
    -> Index `boardroom-knowledge-idx` (HNSW vector + semantic config)
    -> Indexer (scheduled hourly)

Idempotent. `--force` deletes and recreates index/indexer/skillset/datasource.

Env:
  AZURE_SEARCH_ENDPOINT          (e.g. https://srch-frontier-prod-xxx.search.windows.net)
  AZURE_SEARCH_INDEX             default: boardroom-knowledge-idx
  AZURE_STORAGE_ACCOUNT          required (storage account hosting the blob container)
  AZURE_BLOB_CONTAINER           default: boardroom-knowledge
  AZURE_STORAGE_RESOURCE_ID      ARM resource id of the storage account (for MI-auth datasource)
  AZURE_AOAI_ENDPOINT            Foundry/AOAI endpoint for the embedding deployment
  AZURE_AOAI_EMBEDDING_DEPLOY    default: text-embedding-3-small
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from azure.identity import DefaultAzureCredential


SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/")
INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX", "boardroom-knowledge-idx")
DATASOURCE_NAME = f"{INDEX_NAME}-ds"
SKILLSET_NAME = f"{INDEX_NAME}-ss"
INDEXER_NAME = f"{INDEX_NAME}-idx"

STORAGE_ACCOUNT = os.environ["AZURE_STORAGE_ACCOUNT"]
CONTAINER = os.environ.get("AZURE_BLOB_CONTAINER", "boardroom-knowledge")
STORAGE_RESOURCE_ID = os.environ.get("AZURE_STORAGE_RESOURCE_ID", "")

AOAI_ENDPOINT = os.environ.get("AZURE_AOAI_ENDPOINT", "")
EMBEDDING_DEPLOY = os.environ.get("AZURE_AOAI_EMBEDDING_DEPLOY", "text-embedding-3-small")
EMBEDDING_DIMS = int(os.environ.get("AZURE_AOAI_EMBEDDING_DIMS", "1536"))


def _build_clients():
    from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient

    cred = DefaultAzureCredential()
    return (
        SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=cred),
        SearchIndexerClient(endpoint=SEARCH_ENDPOINT, credential=cred),
    )


def build_index(index_client, *, force: bool) -> None:
    from azure.search.documents.indexes.models import (
        HnswAlgorithmConfiguration,
        SearchableField,
        SearchField,
        SearchFieldDataType,
        SearchIndex,
        SemanticConfiguration,
        SemanticField,
        SemanticPrioritizedFields,
        SemanticSearch,
        SimpleField,
        VectorSearch,
        VectorSearchProfile,
    )

    if force:
        try:
            index_client.delete_index(INDEX_NAME)
            print(f"[info] deleted existing index {INDEX_NAME}")
        except Exception:
            pass

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
        SearchableField(name="title", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="source_uri", type=SearchFieldDataType.String, filterable=True, retrievable=True),
        SimpleField(
            name="tags",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
        ),
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIMS,
            vector_search_profile_name="hnsw-default",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw-default")],
        profiles=[VectorSearchProfile(name="hnsw-default", algorithm_configuration_name="hnsw-default")],
    )
    semantic = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name="default",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="title"),
                    content_fields=[SemanticField(field_name="content")],
                ),
            )
        ]
    )
    index = SearchIndex(
        name=INDEX_NAME, fields=fields, vector_search=vector_search, semantic_search=semantic
    )
    index_client.create_or_update_index(index)
    print(f"[ok] index {INDEX_NAME} created/updated")


def build_datasource(indexer_client, *, force: bool) -> None:
    from azure.search.documents.indexes.models import (
        SearchIndexerDataContainer,
        SearchIndexerDataSourceConnection,
        SearchIndexerDataSourceType,
    )

    if force:
        try:
            indexer_client.delete_data_source_connection(DATASOURCE_NAME)
        except Exception:
            pass

    # MI-auth: connection_string = "ResourceId=<arm-id>;"
    if not STORAGE_RESOURCE_ID:
        raise SystemExit("AZURE_STORAGE_RESOURCE_ID required for MI-auth datasource")
    conn_str = f"ResourceId={STORAGE_RESOURCE_ID};"

    ds = SearchIndexerDataSourceConnection(
        name=DATASOURCE_NAME,
        type=SearchIndexerDataSourceType.AZURE_BLOB,
        connection_string=conn_str,
        container=SearchIndexerDataContainer(name=CONTAINER),
    )
    indexer_client.create_or_update_data_source_connection(ds)
    print(f"[ok] datasource {DATASOURCE_NAME} -> {STORAGE_ACCOUNT}/{CONTAINER}")


def build_skillset(indexer_client, *, force: bool) -> None:
    from azure.search.documents.indexes.models import (
        AzureOpenAIEmbeddingSkill,
        AzureOpenAIVectorizerParameters,
        InputFieldMappingEntry,
        OutputFieldMappingEntry,
        SearchIndexerSkillset,
        SplitSkill,
    )

    if force:
        try:
            indexer_client.delete_skillset(SKILLSET_NAME)
        except Exception:
            pass

    if not AOAI_ENDPOINT:
        raise SystemExit("AZURE_AOAI_ENDPOINT required for embedding skill")

    split = SplitSkill(
        text_split_mode="pages",
        maximum_page_length=2000,
        page_overlap_length=200,
        context="/document",
        inputs=[InputFieldMappingEntry(name="text", source="/document/content")],
        outputs=[OutputFieldMappingEntry(name="textItems", target_name="pages")],
    )
    embed = AzureOpenAIEmbeddingSkill(
        context="/document/pages/*",
        resource_url=AOAI_ENDPOINT,
        deployment_name=EMBEDDING_DEPLOY,
        model_name=EMBEDDING_DEPLOY,
        dimensions=EMBEDDING_DIMS,
        inputs=[InputFieldMappingEntry(name="text", source="/document/pages/*")],
        outputs=[OutputFieldMappingEntry(name="embedding", target_name="contentVector")],
    )
    skillset = SearchIndexerSkillset(
        name=SKILLSET_NAME,
        description="Boardroom KB: split + embed",
        skills=[split, embed],
    )
    indexer_client.create_or_update_skillset(skillset)
    print(f"[ok] skillset {SKILLSET_NAME} created/updated")


def build_indexer(indexer_client, *, force: bool) -> None:
    from azure.search.documents.indexes.models import (
        FieldMapping,
        IndexingSchedule,
        SearchIndexer,
    )

    if force:
        try:
            indexer_client.delete_indexer(INDEXER_NAME)
        except Exception:
            pass

    # Document key must be base64-encoded — raw blob URLs contain '/' and ':'
    # which are illegal in Search keys. `base64Encode` mapping function fixes it.
    from azure.search.documents.indexes.models import FieldMappingFunction

    indexer = SearchIndexer(
        name=INDEXER_NAME,
        data_source_name=DATASOURCE_NAME,
        target_index_name=INDEX_NAME,
        skillset_name=SKILLSET_NAME,
        schedule=IndexingSchedule(interval="PT1H"),
        field_mappings=[
            FieldMapping(
                source_field_name="metadata_storage_path",
                target_field_name="id",
                mapping_function=FieldMappingFunction(name="base64Encode"),
            ),
            FieldMapping(source_field_name="metadata_storage_name", target_field_name="title"),
            FieldMapping(source_field_name="metadata_storage_path", target_field_name="source_uri"),
            FieldMapping(source_field_name="content", target_field_name="content"),
        ],
    )
    indexer_client.create_or_update_indexer(indexer)
    indexer_client.run_indexer(INDEXER_NAME)
    print(f"[ok] indexer {INDEXER_NAME} created + running")


def poll_indexer(indexer_client, *, timeout_s: int = 600) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status = indexer_client.get_indexer_status(INDEXER_NAME)
        last = getattr(status, "last_result", None)
        if last is None:
            print("[info] indexer queued…")
        else:
            print(f"[info] indexer status={last.status} items={last.item_count} errors={last.failed_item_count}")
            if last.status in ("success", "transientFailure", "persistentFailure"):
                return
        time.sleep(15)
    print("[warn] indexer poll timed out — check Azure portal")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="delete + recreate everything")
    ap.add_argument("--no-poll", action="store_true", help="skip indexer status polling")
    args = ap.parse_args()

    index_client, indexer_client = _build_clients()
    build_index(index_client, force=args.force)
    build_datasource(indexer_client, force=args.force)
    build_skillset(indexer_client, force=args.force)
    build_indexer(indexer_client, force=args.force)
    if not args.no_poll:
        poll_indexer(indexer_client)
    print("build_aisearch_index: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
