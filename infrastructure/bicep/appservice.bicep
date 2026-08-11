param prefix string
param location string
param acrLoginServer string
param keyVaultName string
param appInsightsConnectionString string
param storageAccountName string
param speechRegion string
param speechResourceId string
param languageEndpoint string
param searchEndpoint string = ''
param searchIndexName string = 'boardroom-knowledge-idx'
param foundryKbName string = 'boardroom-iq'
param backendSubnetId string
param containerImageTag string
param enableEntraAuth bool
param entraClientId string
param entraTenantId string
param entraClientSecretName string

var frontendUrl = 'https://app-${prefix}-frontend.azurewebsites.net'
var frontendAuthSecretSetting = enableEntraAuth
  ? [
      {
        name: 'MICROSOFT_PROVIDER_AUTHENTICATION_SECRET'
        value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=${entraClientSecretName})'
      }
    ]
  : []

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: 'plan-${prefix}'
  location: location
  sku: { name: 'S1', tier: 'Standard' }
  kind: 'linux'
  properties: { reserved: true }
}

resource backend 'Microsoft.Web/sites@2023-12-01' = {
  name: 'app-${prefix}-backend'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    publicNetworkAccess: enableEntraAuth ? 'Disabled' : 'Enabled'
    virtualNetworkSubnetId: backendSubnetId
    siteConfig: {
      linuxFxVersion: 'DOCKER|${acrLoginServer}/frontier-backend:${containerImageTag}'
      acrUseManagedIdentityCreds: true
      vnetRouteAllEnabled: true
      alwaysOn: true
      ftpsState: 'Disabled'
      http20Enabled: true
      minTlsVersion: '1.2'
      scmMinTlsVersion: '1.2'
      webSocketsEnabled: true
      appSettings: [
          { name: 'WEBSITES_PORT', value: '8000' }
          { name: 'APPINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
          { name: 'AZURE_STORAGE_ACCOUNT', value: storageAccountName }
          { name: 'AZURE_BLOB_CONTAINER', value: 'boardroom-knowledge' }
          { name: 'AZURE_SPEECH_REGION', value: speechRegion }
          { name: 'KEYVAULT_NAME', value: keyVaultName }
          { name: 'CORS_ORIGINS', value: '${frontendUrl},http://localhost:5173' }
          // Foundry now uses managed identity + agent_reference API (local-auth disabled on corp sub).
          { name: 'AZURE_FOUNDRY_PROJECT_ENDPOINT', value: 'https://aif-frontier-prod-foundry.services.ai.azure.com/api/projects/proj-aif-frontier-prod' }
          { name: 'AZURE_FOUNDRY_IQ_INDEX_NAME', value: 'boardroom-iq' }
          { name: 'AZURE_FOUNDRY_KB_NAME', value: foundryKbName }
          { name: 'AZURE_SEARCH_ENDPOINT', value: searchEndpoint }
          { name: 'AZURE_SEARCH_INDEX', value: searchIndexName }
          { name: 'DATABRICKS_HOST', value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=databricks-host)' }
          { name: 'DATABRICKS_TOKEN', value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=databricks-token)' }
          { name: 'DATABRICKS_ENDPOINT_CLAUDE_SONNET', value: 'databricks-claude-sonnet-4-6' }
          { name: 'DATABRICKS_ENDPOINT_CLAUDE_OPUS', value: 'databricks-claude-opus-4-6' }
          { name: 'MODEL_CEO', value: 'foundry:CEO@2' }
          { name: 'MODEL_CFO', value: 'databricks:databricks-claude-sonnet-4-6' }
          { name: 'MODEL_CMO', value: 'foundry:CMO@1' }
          { name: 'MODEL_CTO', value: 'foundry:CTO@1' }
          { name: 'MODEL_LEGAL', value: 'databricks:databricks-claude-opus-4-6' }
          { name: 'PUBLIC_DEMO_LIMITS_ENABLED', value: 'true' }
          { name: 'PUBLIC_SESSIONS_PER_CLIENT_HOUR', value: '10' }
          { name: 'PUBLIC_SESSIONS_GLOBAL_HOUR', value: '100' }
          { name: 'PUBLIC_DEBATES_PER_CLIENT_HOUR', value: '3' }
          { name: 'PUBLIC_DEBATES_GLOBAL_HOUR', value: '20' }
          { name: 'PUBLIC_PREP_TURNS_PER_CLIENT_HOUR', value: '12' }
          { name: 'PUBLIC_PREP_TURNS_GLOBAL_HOUR', value: '60' }
          { name: 'PUBLIC_ACTIVE_RUNS_PER_CLIENT', value: '1' }
          { name: 'PUBLIC_ACTIVE_RUNS_GLOBAL', value: '2' }
          { name: 'TRUST_FORWARDED_CLIENT_IP', value: 'false' }
          { name: 'ENTRA_AUTH_REQUIRED', value: string(enableEntraAuth) }
          { name: 'AZURE_SPEECH_RESOURCE_ID', value: speechResourceId }
          { name: 'AZURE_LANGUAGE_ENDPOINT', value: languageEndpoint }
        ]
    }
  }
}

resource frontend 'Microsoft.Web/sites@2023-12-01' = {
  name: 'app-${prefix}-frontend'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    virtualNetworkSubnetId: backendSubnetId
    siteConfig: {
      linuxFxVersion: 'DOCKER|${acrLoginServer}/frontier-frontend:${containerImageTag}'
      acrUseManagedIdentityCreds: true
      vnetRouteAllEnabled: true
      alwaysOn: true
      ftpsState: 'Disabled'
      http20Enabled: true
      minTlsVersion: '1.2'
      scmMinTlsVersion: '1.2'
      appSettings: concat([
          { name: 'WEBSITES_PORT', value: '5173' }
          { name: 'VITE_API_BASE', value: frontendUrl }
          { name: 'VITE_WS_BASE', value: replace(frontendUrl, 'https:', 'wss:') }
          { name: 'BACKEND_PROXY_TARGET', value: 'https://app-${prefix}-backend.azurewebsites.net' }
          { name: 'WEBSITE_DNS_SERVER', value: '168.63.129.16' }
          { name: 'WEBSITE_VNET_ROUTE_ALL', value: '1' }
        ], frontendAuthSecretSetting)
    }
  }
}

resource frontendAuth 'Microsoft.Web/sites/config@2022-09-01' = if (enableEntraAuth) {
  parent: frontend
  name: 'authsettingsV2'
  properties: {
    platform: {
      enabled: true
      runtimeVersion: '~1'
    }
    globalValidation: {
      requireAuthentication: true
      unauthenticatedClientAction: 'RedirectToLoginPage'
      redirectToProvider: 'azureActiveDirectory'
      excludedPaths: [
        '/health'
      ]
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: entraClientId
          clientSecretSettingName: 'MICROSOFT_PROVIDER_AUTHENTICATION_SECRET'
          openIdIssuer: '${environment().authentication.loginEndpoint}${entraTenantId}/v2.0'
        }
        validation: {
          allowedAudiences: [
            entraClientId
            'api://${entraClientId}'
          ]
          defaultAuthorizationPolicy: {
            allowedApplications: [
              entraClientId
            ]
          }
        }
      }
    }
    login: {
      preserveUrlFragmentsForLogins: true
      tokenStore: {
        enabled: true
      }
    }
    httpSettings: {
      requireHttps: true
      forwardProxy: {
        convention: 'NoProxy'
      }
      routes: {
        apiPrefix: '/.auth'
      }
    }
  }
}

output backendUrl string = 'https://${backend.properties.defaultHostName}'
output frontendUrl string = 'https://${frontend.properties.defaultHostName}'
output backendPrincipalId string = backend.identity.principalId
output frontendPrincipalId string = frontend.identity.principalId
output backendId string = backend.id
