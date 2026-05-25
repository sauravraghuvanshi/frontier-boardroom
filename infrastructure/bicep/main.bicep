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

// Grant both apps Key Vault Secrets User
resource kvBackendUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: kv
  name: guid(kv.id, 'app-${prefix}-backend', 'kv-secrets-user')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: apps.outputs.backendPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Grant backend Storage Blob Data Reader
resource storageBackendReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: resourceGroup()
  name: guid(resourceGroup().id, storageName, 'app-${prefix}-backend', 'storage-blob-reader')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
    principalId: apps.outputs.backendPrincipalId
    principalType: 'ServicePrincipal'
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

// AI Search service MI: read blob source for indexer
resource searchBlobReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: resourceGroup()
  name: guid(resourceGroup().id, 'search-svc', 'storage-blob-reader')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
    principalId: search.outputs.searchPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// AI Search service MI: call AOAI embedding deployment for the embedding skill
// (Cognitive Services OpenAI User on the Foundry AIServices account).
resource foundryAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: 'aif-${prefix}-foundry'
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
