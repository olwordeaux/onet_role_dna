import time

from OnetWebService import OnetWebService

API_KEY = "jD5Xi-hGSyq-gVapp-QiCbI"
client = OnetWebService(API_KEY)

soc_codes = ["13-2072.00", "11-3031.00", "11-1021.00", "15-2031.00", "41-3091.00"]

for code in soc_codes:
    try:
        data = client.call(f"online/occupations/{code}/")
    except Exception:  # noqa: BLE001
        pass
    time.sleep(0.2)
