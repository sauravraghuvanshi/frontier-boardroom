// Foundry project hub + project resource. FoundryIQ index is created by the
// post-deploy script `infrastructure/scripts/build_foundry_iq.py` via the
// Azure AI Projects SDK once this resource exists.

param name string
param location string
param storageAccountId string

resource hub 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: '${name}-hub'
  location: location
  kind: 'Hub'
  identity: { type: 'SystemAssigned' }
  properties: {
    friendlyName: 'Frontier Boardroom Hub'
    storageAccount: storageAccountId
  }
}

resource project 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: name
  location: location
  kind: 'Project'
  identity: { type: 'SystemAssigned' }
  properties: {
    hubResourceId: hub.id
    friendlyName: 'Frontier Boardroom'
  }
}

output projectName string = project.name
output projectId string = project.id
output projectPrincipalId string = project.identity.principalId
