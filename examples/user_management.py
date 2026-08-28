import os
from zorveus import ZorveusServiceClient
from _env import load_env_file

def main() -> None:
    load_env_file()
    api_key = os.environ.get("ZORVEUS_SERVICE_KEY", "zrv_svc_demo")
    service = ZorveusServiceClient(api_key=api_key)

    app_id = "app_demo_123"
    external_id = "usr_sara_101"

    print("--- Upserting product user profile ---")
    user_res = service.product_users.create_or_update(
        app_id=app_id,
        external_user_id=external_id,
        display_name="Sara Connor",
        email="sara@example.com",
    )
    print("Product user created:", user_res.product_user.id)

    print("\n--- Granting credits ---")
    grant_res = service.product_users.grant_credit_by_external_id(
        app_id=app_id,
        external_user_id=external_id,
        amount="25.000000000000",
        source="promotion",
        reason="Welcome Bonus",
    )
    print("Granted:", grant_res.credit_grant.amount)
    print("Available credits:", grant_res.credit_summary.available_credits)

if __name__ == "__main__":
    main()
