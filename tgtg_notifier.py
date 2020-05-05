from datetime import datetime
import time
from os import environ
from pushbullet import Pushbullet
from tgtg import TgtgClient

tgtg_email = environ.get('TGTG_EMAIL', None)
tgtg_password = environ.get('TGTG_PASSWORD', None)

tgtg_user_id = environ.get('TGTG_USER_ID', None)
tgtg_access_token = environ.get('TGTG_ACCESS_TOKEN', None)

pb_api_key = environ.get('PB_API_KEY', None)

tgtg_search_lat = environ.get('TGTG_SEARCH_LAT', 0.0)
tgtg_search_lon = environ.get('TGTG_SEARCH_LON', 0.0)
tgtg_search_range = environ.get('TGTG_SEARCH_RANGE', 20000)

pb_notification_channel = environ.get('PB_NOTIFICATION_CHANNEL', None)


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
        items = tgtg_client.get_items(favorites_only=True,
                                      latitude=tgtg_search_lat,
                                      longitude=tgtg_search_lon,
                                      radius=tgtg_search_range)

        print(f"Found {len(items)} favourited stores of which {len([_ for _ in _['items_available'] > 0])} have available items...")
        for item in items:
            if item['items_available'] > 0:
                print(f"Found available product: {item['display_name']} at {datetime.now().strftime('%d.%m.%Y %H:%m:%s')}")
                if pb_client is not None:
                    push_target = pb_client if pb_notification_channel is None else pb_client.get_channel(pb_notification_channel)
                    push_target.push_note(f"TGTG: {item['display_name']} at {datetime.now().strftime('%H:%m')}", f"https://share.toogoodtogo.com/item/{item['item']['item_id']}")

        print(f"All favourited stores were processed. Sleeping {environ.get('SLEEP_INTERVAL', '60')} seconds...")
        time.sleep(int(environ.get('SLEEP_INTERVAL', '60')))


if __name__ == '__main__':
    watch_tgtg()
