import pprint
from zorveus import ZorveusServiceClient

KEY = "zrv_svc_zcnd86ESYeX0NRjitOkEUx2bA_40Aqodb75D9ZoSBxw"
BASE_URL = "http://localhost:8000"
APP_ID = "app_6b541d674ddc40df99485589985b22a9"

client = ZorveusServiceClient(
    api_key=KEY,
    base_url=BASE_URL,
)  # A Zorveus service client that uses the Zorveus API to


USER_ID = "peter_123"

product_user = client.product_users.get_by_external_id(
    external_user_id=USER_ID,
    app_id=APP_ID,
)

print("Product user details:")
pprint.pprint(product_user.model_dump())
