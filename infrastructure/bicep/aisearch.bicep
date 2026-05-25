// Azure AI Search — backing index for Foundry IQ Knowledge Base (boardroom-iq).
// SKU 'standard' (S1) — supports semantic ranker. AAD-only (corp sub policy).
// The index + indexer are created post-deploy by
// `infrastructure/scripts/build_aisearch_index.py` once this resource exists.
//
// Role assignments scoped to the search service are declared here (not in
// main.bicep) so we can use a direct symbolic reference instead of an
// `existing` lookup that would fail BCP120 at compile time.

param name string
param location string

@description('Foundry project MI — needs read + manage on the index for KB attach')
param foundryPrincipalId string = ''

resource search 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: name
  location: location
  sku: { name: 'standard' }
  identity: { type: 'SystemAssigned' }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    semanticSearch: 'standard'
    disableLocalAuth: true
    authOptions: null
  }
}

resource foundryReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(foundryPrincipalId)) {
  scope: search
  name: guid(search.id, foundryPrincipalId, 'search-index-data-reader')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '1407120a-92aa-4202-b7e9-c0e197c71c8f')
    principalId: foundryPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource foundryContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(foundryPrincipalId)) {
  scope: search
  name: guid(search.id, foundryPrincipalId, 'search-service-contributor')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
    principalId: foundryPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output searchName string = search.name
output searchResourceId string = search.id
output searchEndpoint string = 'https://${search.name}.search.windows.net'
output searchPrincipalId string = search.identity.principalId
