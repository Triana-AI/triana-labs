targetScope = 'resourceGroup'

@minLength(3)
param prefix string
param location string = resourceGroup().location
param adminUsername string = 'tauoperator'
param vmSize string
param sshPublicKey string
param operatorObjectId string
@allowed(['User', 'ServicePrincipal'])
param operatorPrincipalType string

var storageName = take(toLower(replace('${prefix}${uniqueString(resourceGroup().id)}', '-', '')), 24)
var vaultName = take(toLower('${prefix}-${uniqueString(resourceGroup().id)}'), 24)
var vmName = '${prefix}-vm'

resource vnet 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: '${prefix}-vnet'
  location: location
  properties: {
    addressSpace: { addressPrefixes: ['10.42.0.0/16'] }
    subnets: [{
      name: 'worker'
      properties: {
        addressPrefix: '10.42.1.0/24'
        networkSecurityGroup: { id: nsg.id }
        natGateway: { id: nat.id }
      }
    }]
  }
}

resource natIp 'Microsoft.Network/publicIPAddresses@2024-05-01' = {
  name: '${prefix}-nat-ip'
  location: location
  sku: { name: 'Standard' }
  properties: { publicIPAllocationMethod: 'Static' }
}

resource nat 'Microsoft.Network/natGateways@2024-05-01' = {
  name: '${prefix}-nat'
  location: location
  sku: { name: 'Standard' }
  properties: {
    idleTimeoutInMinutes: 4
    publicIpAddresses: [{ id: natIp.id }]
  }
}

resource nsg 'Microsoft.Network/networkSecurityGroups@2024-05-01' = { name: '${prefix}-nsg', location: location, properties: { securityRules: [] } }

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
      virtualNetworkRules: []
    }
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    deleteRetentionPolicy: { enabled: true, days: 7 }
    isVersioningEnabled: true
  }
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = { parent: blobService, name: 'tau2-smoke', properties: { publicAccess: 'None' } }

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: vaultName
  location: location
  properties: {
    tenantId: tenant().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: false
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
      virtualNetworkRules: []
    }
    accessPolicies: [
      {
        tenantId: tenant().tenantId
        objectId: operatorObjectId
        permissions: { secrets: ['get', 'list', 'set'] }
      }
      {
        tenantId: tenant().tenantId
        objectId: vm.identity.principalId
        permissions: { secrets: ['get', 'list'] }
      }
    ]
  }
}

resource nic 'Microsoft.Network/networkInterfaces@2024-05-01' = {
  name: '${prefix}-nic'
  location: location
  properties: {
    ipConfigurations: [{
      name: 'private'
      properties: {
        privateIPAllocationMethod: 'Dynamic'
        subnet: { id: vnet.properties.subnets[0].id }
      }
    }]
  }
}

resource vm 'Microsoft.Compute/virtualMachines@2024-07-01' = {
  name: vmName
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    hardwareProfile: { vmSize: vmSize }
    networkProfile: { networkInterfaces: [{ id: nic.id }] }
    osProfile: {
      computerName: 'tau2-smoke'
      adminUsername: adminUsername
      linuxConfiguration: {
        disablePasswordAuthentication: true
        ssh: { publicKeys: [{ path: '/home/${adminUsername}/.ssh/authorized_keys', keyData: sshPublicKey }] }
      }
    }
    storageProfile: {
      imageReference: { publisher: 'Canonical', offer: '0001-com-ubuntu-server-jammy', sku: '22_04-lts-gen2', version: 'latest' }
      osDisk: { createOption: 'FromImage', managedDisk: { storageAccountType: 'Standard_LRS' } }
    }
  }
}

output vmName string = vm.name
output vmSize string = vmSize
output storageAccount string = storage.name
output vaultName string = vault.name
output containerName string = container.name
output blobEndpoint string = storage.properties.primaryEndpoints.blob
output vaultUri string = vault.properties.vaultUri
output natGatewayName string = nat.name
output natEgressIp string = natIp.properties.ipAddress
output operatorPrincipalType string = operatorPrincipalType
