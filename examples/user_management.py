import os
import uuid
from zorveus import ZorveusServiceClient
from _env import load_env_file


def main() -> None:
    load_env_file()

    api_key = os.environ.get("ZORVEUS_SERVICE_KEY")
    base_url = os.environ.get("ZORVEUS_BASE_URL", "http://localhost:8000")
    app_id = os.environ.get("ZORVEUS_APP_ID", "app_6b541d674ddc40df99485589985b22a9")

    if not api_key:
        print("Error: ZORVEUS_SERVICE_KEY is required.")
        return

    service = ZorveusServiceClient(api_key=api_key, base_url=base_url)
    external_id = f"demo_user_{uuid.uuid4().hex[:6]}"

    print(f"=== 1. Upserting Product User ({external_id}) ===")
    upsert_res = service.product_users.create_or_update(
        app_id=app_id,
        external_user_id=external_id,
        display_name="Demo End User",
        email="demo@example.com",
    )
    user = upsert_res.product_user
    print(f"Product End User ID: {user.product_end_user_id}")
    print(f"Display Name:        {user.display_name}")
    print(f"Created flag:        {upsert_res.created}")

    print("\n=== 2. Fetching Product User Profile ===")
    profile = service.product_users.get_by_external_id(
        app_id=app_id,
        external_user_id=external_id,
    )
    print(f"Status:              {profile.status}")
    print(f"External User ID:    {profile.external_user_id}")

    print("\n=== 3. Querying Credit Summary (Before Grant) ===")
    initial_summary = service.product_users.get_credit_summary_by_external_id(
        app_id=app_id,
        external_user_id=external_id,
    )
    print(f"Available credits:   ${initial_summary.available_credits}")
    print(f"Active grants count: {initial_summary.active_grant_count}")

    print("\n=== 4. Granting Promotional Credits ===")
    grant_res = service.product_users.grant_credit_by_external_id(
        app_id=app_id,
        external_user_id=external_id,
        amount="5.000000000000",
        source="promotion",
        reason="Welcome bonus",
    )
    print(f"Granted:             ${grant_res.credit_grant.amount}")
    print(f"Grant ID:            {grant_res.credit_grant.credit_grant_id}")
    print(f"New available:       ${grant_res.credit_summary.available_credits}")

    print("\n=== 5. Listing Credit Grants ===")
    grants_list = service.product_users.list_credit_grants_by_external_id(
        app_id=app_id,
        external_user_id=external_id,
        status="active",
    )
    print(f"Total grants found:  {len(grants_list.credit_grants)}")
    for grant in grants_list.credit_grants:
        print(f"  - {grant.credit_grant_id}: ${grant.remaining_amount} remaining ({grant.status})")

    service.close()
    print("\n✓ User management workflow complete.")


if __name__ == "__main__":
    main()
