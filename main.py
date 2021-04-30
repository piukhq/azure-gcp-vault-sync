import logging

import google.api_core.exceptions
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from google.cloud.secretmanager import SecretManagerServiceClient
import sentry_sdk

sentry_sdk.init(
    dsn='https://71931c5b3d9b4c8ab52619fdc1d4e6c4@o503751.ingest.sentry.io/5740941',
    traces_sample_rate=0
)

logging.basicConfig(level=logging.INFO)
logging.getLogger("azure").setLevel(logging.ERROR)

akv_uri = "https://bink-uksouth-prod-com.vault.azure.net"
akv_client = SecretClient(vault_url=akv_uri, credential=DefaultAzureCredential(
    exclude_environment_credential=True,
    exclude_shared_token_cache_credential=True,
    exclude_visual_studio_code_credential=True,
    exclude_interactive_browser_credential=True,
))

with open("/tmp/auth.json", "w+") as f:
    f.write(akv_client.get_secret("azure-gcp-vault-sync").value)

gcp_client = SecretManagerServiceClient.from_service_account_json("/tmp/auth.json")


def list_azure_secrets():
    return [i.name for i in akv_client.list_properties_of_secrets()]


def get_azure_secret(name):
    return akv_client.get_secret(name).value


def get_gcp_secret(name):
    return gcp_client.access_secret_version(
        name=f"projects/azure-gcp-vault-sync/secrets/{name}/versions/latest"
    ).payload.data.decode("UTF-8")


def create_gcp_secret(name, data):
    try:
        gcp_client.create_secret(
            request={
                "parent": "projects/azure-gcp-vault-sync",
                "secret_id": name,
                "secret": {"replication": {"automatic": {}}},
            }
        )
        logging.info(f"Secret: '{name}' was created")
    except google.api_core.exceptions.AlreadyExists:
        logging.info(f"Secret: '{name}' already exists, checking data")
        if get_gcp_secret(name) == data:
            logging.info(f"Secret: '{name}' already up to date")
            return None
        pass

    logging.info(f"Secret: '{name}' contains new data, creating new version")
    gcp_client.add_secret_version(
        request={"parent": f"projects/azure-gcp-vault-sync/secrets/{name}", "payload": {"data": str.encode(data)}}
    )


def syncronise_vaults():
    logging.info("Beginning Azure KeyVault -> Google Cloud Sync")
    for i in list_azure_secrets():
        data = get_azure_secret(i)
        create_gcp_secret(name=i, data=data)


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(syncronise_vaults, trigger=CronTrigger.from_crontab("0 * * * *"))
    scheduler.start()
