import os
import sys
from zorveus import ZorveusServiceClient, ZorveusError
from _env import load_env_file

load_env_file()

service_key = os.getenv("ZORVEUS_SERVICE_KEY")
base_url = os.getenv("ZORVEUS_BASE_URL", "http://localhost:8000")
provider_key = os.getenv("TEST_PROVIDER_API_KEY")

if not service_key:
    print("Error: ZORVEUS_SERVICE_KEY environment variable is required.")
    sys.exit(1)

client = ZorveusServiceClient(service_key=service_key, base_url=base_url)


def run_full_lifecycle(api_key: str) -> None:
    print("Creating new programmatic provider credential...")
    created = client.provider_credentials.create(
        provider="openai",
        credential_name="Demo Script Key",
        api_key=api_key,
        routing_priority=100,
    )
    credential_id = created.id
    print(f"Created credential: {credential_id} (provider={created.provider})")

    print("Updating routing priority to 50...")
    updated = client.provider_credentials.update_routing_priority(
        provider_credential_id=credential_id,
        routing_priority=50,
    )
    print(f"Updated priority: {updated.provider_credential.routing_priority}")

    print("Rotating credential secret key...")
    rotated = client.provider_credentials.rotate(
        provider_credential_id=credential_id,
        api_key=api_key,
    )
    print(f"Rotated key. Status: {rotated.status}")

    print("Deleting test credential...")
    deleted = client.provider_credentials.delete(
        provider_credential_id=credential_id,
    )
    print(f"Deleted credential. Status: {deleted.status}")


def run_read_and_update_demo() -> None:
    credentials_list = client.provider_credentials.list()
    credentials = credentials_list.credentials
    print(f"Found {len(credentials)} registered provider credentials.")

    if not credentials:
        print("No existing credentials available to test routing priority update.")
        return

    target = credentials[0]
    original_priority = target.routing_priority or 100
    temp_priority = 90 if original_priority == 100 else 100

    print(f"Testing priority update on credential {target.id} ({target.provider})...")
    res1 = client.provider_credentials.update_routing_priority(
        provider_credential_id=target.id,
        routing_priority=temp_priority,
    )
    print(f"Updated priority from {original_priority} to {res1.provider_credential.routing_priority}")

    res2 = client.provider_credentials.update_routing_priority(
        provider_credential_id=target.id,
        routing_priority=original_priority,
    )
    print(f"Restored priority back to {res2.provider_credential.routing_priority}")

    print("\nDemonstrating create() validation guardrail with mock key...")
    try:
        client.provider_credentials.create(
            provider="openai",
            credential_name="Mock Validation Test",
            api_key="sk-mock-key-unvalidated",
        )
    except ZorveusError as err:
        print(f"Caught expected provider validation error: {err.message}")


def main() -> None:
    if provider_key:
        print("Live provider API key detected. Running full lifecycle...")
        run_full_lifecycle(provider_key)
        return

    print("No TEST_PROVIDER_API_KEY found. Running credential list, update, and validation checks...")
    run_read_and_update_demo()


if __name__ == "__main__":
    main()
