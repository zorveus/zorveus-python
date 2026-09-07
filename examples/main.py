from zorveus.openai import ZorveusOpenAI
from openai import OpenAI as _OpenAI

API_KEY = "zrv_4g2Z0KLHY1vMJkJyuJQ4sGvIfOBpDnjcQZUnWUdk42E"
# API_KEY = "zrv_f6y6Upe1Y45SEWUUGjGuqEkrewl-h450jtn2YBlU7_8"
# MODEL = "gemini/gemini-2.5-flash-lite"
MODEL = "gemini/gemini-3.5-flash-lite"
# MODEL = "gemini/gemini-3.1-pro-preview"
BASE_URL = "http://localhost:4000/v1"
# BASE_URL = "https://api.zorveus.com/v1"

USER_1 = "user_1"
USER_2 = "user_123"
USER_3 = "user_1234"
USER_4 = "peter_123"


client = ZorveusOpenAI(
    api_key=API_KEY,
    gateway_url=BASE_URL,
    external_user_id=USER_4,
)  # An OpenAI client that uses the Zorveus API to communicate with the Gemini model.
# openai_client = _OpenAI(
#     api_key=API_KEY,
#     base_url=BASE_URL,
# )  # An OpenAI client that uses the Zorveus API to communicate with the Gemini model.

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        # {"role": "user", "content": "GIve me a very long ass poem"},
        {"role": "user", "content": "What is the capital of France?"},
    ],
    # max_tokens=1000,
)


print(response.choices[0].message.content)
