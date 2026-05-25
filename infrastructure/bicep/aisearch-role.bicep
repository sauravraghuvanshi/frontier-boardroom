// Tiny sub-module for assigning Search Index Data Reader on an EXISTING
// search service. Used by main.bicep to break the apps↔search cycle
// (apps consumes searchEndpoint; backend MI principalId comes from apps).

param searchName string
param principalId string
param roleDefinitionId string
param roleKey string

resource search 'Microsoft.Search/searchServices@2024-06-01-preview' existing = {
  name: searchName
}

resource ra 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: search
  name: guid(search.id, principalId, roleKey)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}
