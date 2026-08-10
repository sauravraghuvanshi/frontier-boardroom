// ============================================================================
// Frontier Boardroom — main.bicep
// Provisions: App Service plan + 2 web apps, ACR, Storage, Foundry project,
// Databricks workspace (Premium), Speech, Language, App Insights, Key Vault.
// Managed identity wired through everywhere.
// ============================================================================

targetScope = 'resourceGroup'

@description('Short env tag, e.g. dev, staging, prod')
param env string = 'dev'

@description('Azure region')
param location string = resourceGroup().location

@description('Object id of the principal that should get Key Vault Secrets Officer (you, normally)')
param adminObjectId string

@description('Anthropic API key — written to Key Vault, consumed by Databricks endpoints')
@secure()
param anthropicApiKey string = ''

@description('Enable tenant-bound App Service Authentication on both web apps')
param enableEntraAuth bool

@description('Client ID of the single-tenant Entra app registration used by App Service Authentication')
param entraClientId string

@description('Name of the Key Vault secret containing the App Service Authentication client secret')
param entraClientSecretName string = 'appservice-auth-client-secret'

var prefix = 'frontier-${env}'
var storageName = take(toLower(replace('stfrontier${env}${uniqueString(resourceGroup().id)}', '-', '')), 24)
var acrName = take(toLower('acrfrontier${env}${uniqueString(resourceGroup().id)}'), 50)
var kvName = take('kv-${prefix}-${uniqueString(resourceGroup().id)}', 24)

// ---------- Log Analytics + App Insights ----------
module insights 'insights.bicep' = {
  name: 'insights'
  params: {
    name: 'appi-${prefix}'
    location: location
  }
}

// ---------- Storage ----------
module storage 'storage.bicep' = {
  name: 'storage'
  params: {
    name: storageName
    location: location
  }
}

// ---------- Container Registry ----------
resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: acrName
  location: location
  sku: { name: 'Standard' }
  properties: {
    adminUserEnabled: false
  }
}

// ---------- Foundry project (placeholder) ----------
module foundry 'foundry.bicep' = {
  name: 'foundry'
  params: {
    name: 'aif-${prefix}'
    location: location
    storageAccountId: storage.outputs.id
  }
}

// ---------- Databricks: reusing existing workspace adb-7405606075294687 (see DEPLOYMENT.md) ----------

// ---------- Speech ----------
module speech 'speech.bicep' = {
  name: 'speech'
  params: {
    name: 'speech-${prefix}'
    location: location
  }
}

// ---------- Azure AI Search — backs the Foundry IQ KB (boardroom-iq) ----------
module search 'aisearch.bicep' = {
  name: 'search'
  params: {
    name: take(toLower('srch-${prefix}-${uniqueString(resourceGroup().id)}'), 60)
    location: location
    foundryPrincipalId: foundry.outputs.projectPrincipalId
  }
}

// ---------- Language ----------
resource language 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: 'lang-${prefix}'
  location: location
  kind: 'TextAnalytics'
  sku: { name: 'S' }
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: 'lang-${prefix}'
    publicNetworkAccess: 'Enabled'
  }
}

// ---------- Key Vault ----------
resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: kvName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    publicNetworkAccess: 'Disabled'
  }
}

// Admin gets Secrets Officer
resource kvAdminRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: kv
  name: guid(kv.id, adminObjectId, 'kv-secrets-officer')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7')
    principalId: adminObjectId
  }
}

// Optional secret pre-population
resource anthropicSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(anthropicApiKey)) {
  parent: kv
  name: 'anthropic-api-key'
  properties: { value: anthropicApiKey }
}

// ---------- Private networking ----------
module network 'network.bicep' = {
  name: 'network'
  params: {
    prefix: prefix
    location: location
    vaultId: kv.id
  }
}

// ---------- App Service plan + 2 apps ----------
module apps 'appservice.bicep' = {
  name: 'apps'
  params: {
    prefix: prefix
    location: location
    acrLoginServer: acr.properties.loginServer
    keyVaultName: kv.name
    appInsightsConnectionString: insights.outputs.connectionString
    storageAccountName: storage.outputs.name
    speechRegion: location
    speechResourceId: speech.outputs.id
    languageEndpoint: language.properties.endpoint
    searchEndpoint: search.outputs.searchEndpoint
    searchIndexName: 'boardroom-knowledge-idx'
    foundryKbName: 'boardroom-iq'
    backendSubnetId: network.outputs.appServiceSubnetId
    enableEntraAuth: enableEntraAuth
    entraClientId: entraClientId
    entraTenantId: subscription().tenantId
    entraClientSecretName: entraClientSecretName
  }
}

module appServicePrivateEndpoint 'appservice-private-endpoint.bicep' = if (enableEntraAuth) {
  name: 'appServicePrivateEndpoint'
  params: {
    prefix: prefix
    location: location
    backendId: apps.outputs.backendId
    privateEndpointSubnetId: network.outputs.privateEndpointSubnetId
    vnetId: network.outputs.vnetId
  }
}

// Existing speech account (needed for scoped role assignment)
resource speechAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: 'speech-${prefix}'
}

// Cognitive Services Speech User on speech account for backend MI
resource speechBackendUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: speechAccount
  name: guid(speechAccount.id, 'app-${prefix}-backend', 'speech-user')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'f2dc8367-1007-4938-bd23-fe263f013447')
    principalId: apps.outputs.backendPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Cognitive Services User on language account for backend MI (TextAnalytics read)
resource languageBackendUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: language
  name: guid(language.id, 'app-${prefix}-backend', 'cogsvc-user')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')
    principalId: apps.outputs.backendPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Backend resolves its runtime Key Vault references.
resource kvBackendUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: kv
  name: guid(kv.id, 'app-${prefix}-backend', 'kv-secrets-user')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: apps.outputs.backendPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource entraAuthSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' existing = if (enableEntraAuth) {
  parent: kv
  name: entraClientSecretName
}

// Frontend can resolve only the Easy Auth secret, not model credentials.
resource kvFrontendAuthSecretUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableEntraAuth) {
  scope: entraAuthSecret
  name: guid(entraAuthSecret.id, 'app-${prefix}-frontend', 'kv-auth-secret-user')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: apps.outputs.frontendPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Storage data roles are scoped to the storage account, never the resource group.
module storageBackendReader 'storage-role.bicep' = {
  name: 'storageBackendReader'
  params: {
    storageName: storage.outputs.name
    principalId: apps.outputs.backendPrincipalId
    roleKey: 'backend-blob-reader'
  }
}

// AcrPull for both apps
resource acrBackendPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: acr
  name: guid(acr.id, 'app-${prefix}-backend', 'acrpull')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: apps.outputs.backendPrincipalId
    principalType: 'ServicePrincipal'
  }
}
resource acrFrontendPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: acr
  name: guid(acr.id, 'app-${prefix}-frontend', 'acrpull')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: apps.outputs.frontendPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// ---------- AI Search role assignments (KB-backing index) ----------
// Foundry MI roles are declared inside the search module itself (compile-time
// scope). Backend role is broken out into a sub-module to avoid a cycle
// (apps consumes searchEndpoint; backend principalId comes from apps).
module searchBackendReader 'aisearch-role.bicep' = {
  name: 'searchBackendReader'
  params: {
    searchName: search.outputs.searchName
    principalId: apps.outputs.backendPrincipalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    roleKey: 'search-index-data-reader'
  }
}

// AI Search service MI: read blob source for indexer.
module searchBlobReader 'storage-role.bicep' = {
  name: 'searchBlobReader'
  params: {
    storageName: storage.outputs.name
    principalId: search.outputs.searchPrincipalId
    roleKey: 'search-blob-reader'
  }
}

// AI Search service MI: call AOAI embedding deployment for the embedding skill
// (Cognitive Services OpenAI User on the Foundry AIServices account).
resource foundryAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: 'aif-${prefix}-foundry'
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' existing = {
  parent: foundryAccount
  name: 'proj-aif-${prefix}'
}

// Runtime can use existing agents and raw model deployments, but cannot manage the project.
resource backendFoundryUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundryProject
  name: guid(foundryProject.id, 'app-${prefix}-backend', 'foundry-user')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '53ca6127-db72-4b80-b1b0-d745d6d5456d')
    principalId: apps.outputs.backendPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource searchOpenAIUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundryAccount
  name: guid(foundryAccount.id, 'search-svc', 'aoai-user')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: search.outputs.searchPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output backendUrl string = apps.outputs.backendUrl
output frontendUrl string = apps.outputs.frontendUrl
output keyVaultName string = kv.name
output acrLoginServer string = acr.properties.loginServer
output storageAccountName string = storage.outputs.name
output speechResourceId string = speech.outputs.id
output languageEndpoint string = language.properties.endpoint
output searchEndpoint string = search.outputs.searchEndpoint
output searchName string = search.outputs.searchName
