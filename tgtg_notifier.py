import requests
import time
from os import environ
from pushbullet import Pushbullet
from tgtg import TgtgClient

tgtg_email = environ.get('TGTG_EMAIL', None)
tgtg_password = environ.get('TGTG_PASSWORD', None)

tgtg_user_id = environ.get('TGTG_USER_ID', None)
tgtg_access_token = environ.get('TGTG_ACCESS_TOKEN', None)

pb_api_key = environ.get('PB_API_KEY', None)


def watch_tgtg():
    if tgtg_email is not None and tgtg_password is not None:
        tgtg_client = TgtgClient(email=tgtg_email, password=tgtg_password)
    elif tgtg_user_id is not None and tgtg_access_token is not None:
        tgtg_client = TgtgClient(user_id=tgtg_user_id, access_token=tgtg_access_token)
    else:
        print("Neither email and password nor user id and access token for TGTG were specified. Aborting...")

    pb_client = None
    if pb_api_key is not None:
        pb_client = Pushbullet(pb_api_key)

    while True:
        items = tgtg_client.get_items(favorites_only=True, latitude=49.017508, longitude=12.092244, radius=5000)

        for item in items:
            if item['items_available'] > 0:
                info_string = f"Found available store: {item['display_name']} "
                print(info_string)
                if pb_client is not None:
                    pb_client.
            pass

        time.sleep(int(environ.get('SLEEP_INTERVAL', '60')))


if __name__ == '__main__':
    watch_tgtg()
