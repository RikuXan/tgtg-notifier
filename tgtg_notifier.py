from datetime import datetime
import time
from os import environ
from pushbullet import Pushbullet
from pushbullet.channel import Channel
from tgtg import TgtgClient
from uuid import uuid4


# monkey-patch channel to add channel iden to variables and pushb
def channel_init(self, account, channel_info):
    self._account = account
    self.channel_tag = channel_info.get("tag")

    for attr in ("name", "description", "created", "modified", "iden"):
        setattr(self, attr, channel_info.get(attr))


def pushbullet_push_link(self, title, url, body=None, device=None, chat=None, email=None, channel=None, guid=None):
    data = {"type": "link", "title": title, "url": url, "body": body, "guid": guid}

    data.update(Pushbullet._recipient(device, chat, email, channel))

    return self._push(data)


Channel.__init__ = channel_init
Pushbullet.push_link = pushbullet_push_link

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

    if bool(environ.get('PB_CLEAR_CHANNEL', False)):
        for push in pb_client.get_pushes():
            if 'channel_iden' in push and push['channel_iden'] == pb_client.get_channel(pb_notification_channel).iden:
                pb_client.delete_push(push['iden'])

    available_items = {}
    while True:
        for available_item in available_items.values():
            available_item['still_available'] = False

        items = tgtg_client.get_items(favorites_only=True,
                                      latitude=tgtg_search_lat,
                                      longitude=tgtg_search_lon,
                                      radius=tgtg_search_range)

        print(f"Found {len(items)} favourited stores of which {len([_ for _ in items if _['items_available'] > 0])} have available items...")
        for item in items:
            if item['items_available'] > 0:
                if item['item']['item_id'] in available_items:
                    available_items[item['item']['item_id']]['still_available'] = True
                else:
                    print(f"Found newly available product: {item['display_name']} since {datetime.now().strftime('%H:%M:%S (%d.%m.%Y)')}")
                    if pb_client is not None:
                        push_guid = uuid4().hex
                        pb_client.push_link(f"New TGTG product available",
                                            f"https://share.toogoodtogo.com/item/{item['item']['item_id']}",
                                            f"{item['display_name']} since {datetime.now().strftime('%H:%M:%S (%d.%m.%Y)')}",
                                            channel=pb_client.get_channel(pb_notification_channel),
                                            guid=push_guid)
                    available_items[item['item']['item_id']] = {'item': item, 'still_available': True, 'push_guid': push_guid}

        keys_to_delete = []
        for available_item_id, available_item in available_items.items():
            if not available_item['still_available']:
                print(f"Product is no longer available: {available_item['item']['display_name']} since {datetime.now().strftime('%H:%M:%S (%d.%m.%Y)')}")
                if pb_client is not None:
                    push_to_delete = next((push for push in pb_client.get_pushes() if 'guid' in push and push['guid'] == available_item['push_guid']), None)
                    if push_to_delete is not None:
                        pb_client.delete_push(push_to_delete['iden'])

                keys_to_delete.append(available_item_id)

        for key_to_delete in keys_to_delete:
            del available_items[key_to_delete]

        print(f"All favourited stores were processed. Sleeping {environ.get('SLEEP_INTERVAL', '60')} seconds...")
        time.sleep(int(environ.get('SLEEP_INTERVAL', '60')))


if __name__ == '__main__':
    watch_tgtg()
