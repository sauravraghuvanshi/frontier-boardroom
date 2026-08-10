param prefix string
param location string
param backendId string
param privateEndpointSubnetId string
param vnetId string

resource appServicePrivateDns 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.azurewebsites.net'
  location: 'global'
}

resource appServicePrivateDnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: appServicePrivateDns
  name: '${prefix}-appservice-link'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetId
    }
  }
}

resource backendPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: 'pe-${prefix}-backend'
  location: location
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'backend'
        properties: {
          privateLinkServiceId: backendId
          groupIds: [
            'sites'
          ]
        }
      }
    ]
  }
}

resource backendPrivateDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: backendPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'appservice'
        properties: {
          privateDnsZoneId: appServicePrivateDns.id
        }
      }
    ]
  }
}
