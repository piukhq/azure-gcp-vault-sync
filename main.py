from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


akv_uri = 'https://bink-uksouth-prod-com.vault.azure.net'
akv_client = SecretClient(vault_url=akv_uri, credential=DefaultAzureCredential())
# gcp_credentials = akv_client.get_secret('azure-gcp-vault-sync').value
