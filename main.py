import json
import re
import time
import requests
import base64
import hashlib
import logging
from urllib.parse import quote

with open('settings.json', 'r') as file:
    settings = json.load(file)

debug = settings['debug']

if debug['enable_logging']:
    logging.basicConfig(filename='moonraker_bark_notifier.log', level=logging.WARNING)


def barking(content):
    retries = 0
    bark = settings['bark']
    max_retries = bark['max_retries']
    while retries < max_retries:
        res = requests.get(f"{bark['url']}/{content}")
        if res.ok:
            return True
        else:
            if debug['enable_logging']:
                logging.error(f"Barking failed: {res.reason}. Retrying for the {retries + 1} time.")
            time.sleep(5)
            retries += 1
    print(f"Barking failed. Too many retries.")
    logging.error(f"Barking failed. Too many retries.")
    exit(1)


def moonraker_login():
    moonraker = settings['moonraker']
    res = requests.post(f"http://{moonraker['url']}:{moonraker['port']}/access/login",
                        json={"username": moonraker['username'], "password": moonraker['passwd']})
    if res.ok:
        return res.json()['result']['token']
    else:
        if settings['enable_logging']:
            logging.error(f"Moonraker login failed: {res.reason}")
        print(f"Moonraker login failed: {res.reason}")
        exit(1)


class BarkingController:

    def __init__(self):
        self.is_printing: bool = False
        self.start_of_print: bool = True
        self.notified_percentage: list = list()
        self.refresh_counter = 1

    def get_machine_states(self):
        moonraker = settings['moonraker']
        webcam = settings['webcam']
        backblaze = settings['backblaze']
        bark = settings['bark']

        if self.refresh_counter % 80 != 0:
            token = moonraker_login()
            header = {'Authorization': f"Bearer {token}"}
        else:
            self.refresh_counter = 1
            header = ''

        res = requests.get(
            f"http://{moonraker['url']}:{moonraker['port']}/printer/objects/query?print_stats&display_status",
            headers=header)

        if 'result' not in res.json():
            time.sleep(30)

        else:
            self.refresh_counter += 1
            print_stats = res.json()['result']['status']['print_stats']
            display_status = res.json()['result']['status']['display_status']
            progress = round(display_status['progress'] * 100, 2)
            state = print_stats['state']
            project_name = re.sub(r'.gcode', "", print_stats['filename'])

            if state == "printing":
                self.is_printing = True

            if self.is_printing and self.start_of_print:
                barking(f"Printing Started/Start listening to project {quote(project_name)}!?icon={bark['icon_url']}")
                self.start_of_print = False

            if state == "complete":
                if not self.is_printing:
                    return

                if webcam['has_camera']:
                    b2 = B2Upload()
                    upload_file_name = b2.upload()
                    barking(
                        f"Printing COMPLETED!/Project {quote(project_name)} is finished. Click"
                        f" to see the photo.?level=timeSensitive&url={backblaze['url']}/{upload_file_name}"
                        f"&icon={bark['icon_url']}")
                else:
                    barking(
                        f"Printing COMPLETED!/Project {quote(project_name)} is finished.?level"
                        f"=timeSensitive&icon={bark['url']}&icon={bark['icon_url']}")
                self.is_printing = False

            if state == 'paused':
                if not self.is_printing:
                    return

                barking(
                    f"Printing Paused!/Project {quote(project_name)} has been paused."
                    f"?icon={bark['icon_url']}")
                self.is_printing = False

            if state == 'error':
                if not self.is_printing:
                    return

                if webcam['has_camera']:
                    b2 = B2Upload()
                    upload_file_name = b2.upload()
                    barking(
                        f"Printing ERROR!/Project {quote(project_name)} is failed. Hope next time is a success! Click"
                        f" to see the photo.?level=timeSensitive&icon={bark['icon_url']}"
                        f"&url={backblaze['url']}/{upload_file_name}")
                else:
                    barking(
                        f"Printing ERROR!/Project {quote(project_name)} is failed. Hope next time is a success!?level"
                        f"=timeSensitive&icon={bark['icon_url']}")

                self.is_printing = False

            else:
                if not self.is_printing:
                    return

                for key in settings['notification_while_percentage']:
                    if int(progress) in self.notified_percentage:
                        break

                    if key == int(progress):
                        self.notified_percentage.append(int(progress))
                        if webcam['has_camera']:
                            b2 = B2Upload()
                            upload_file_name = b2.upload()
                            barking(
                                f"Printing Status Notification/Project {quote(project_name)} is {progress}%25 done! Click to "
                                f"see the photo.?url={backblaze['url']}/{upload_file_name}"
                                f"&icon={bark['icon_url']}")
                        else:
                            barking(
                                f"Printing Status Notification/Project {quote(project_name)} is {progress}%25 done!"
                                f"?icon={bark['icon_url']}")


##########################
# photo upload functions #
#   using backblaze b2   #


def get_upload_photo():
    webcam = settings['webcam']
    f = requests.get(webcam['url'])
    if f.ok:
        return f.content
    else:
        if settings['debug_settings']['enable_logging']:
            logging.warning(f"Error communicating with {webcam['url']}, reason: {f.reason}")
        return None


class B2Upload:
    def __init__(self):
        self.account_token = ''
        self.upload_token = ''
        self.api_url = ''
        self.upload_url = ''

    def get_b2_token(self):
        backblaze = settings['backblaze']

        id_and_key = f"{backblaze['keyID']}:{backblaze['applicationKey']}"
        basic_auth_string = 'Basic ' + \
                            base64.b64encode(id_and_key.encode('utf-8')).decode('utf-8')
        headers = {'Authorization': basic_auth_string}
        res = requests.get(
            'https://api.backblazeb2.com/b2api/v2/b2_authorize_account', headers=headers)
        if res.ok:
            self.api_url = res.json()['apiUrl']
            self.account_token = res.json()['authorizationToken']
            return True
        else:
            if settings['debug_settings']['enable_logging']:
                logging.warning(f"Fetch token failed: {res.reason}")
            return False

    def b2_get_upload_url(self):
        backblaze = settings['backblaze']

        if not self.get_b2_token():
            return False

        headers = {'Authorization': self.account_token}
        res = requests.post(
            f'{self.api_url}/b2api/v2/b2_get_upload_url', data=json.dumps({'bucketId': backblaze['bucketID']}),
            headers=headers)
        if res.ok:
            self.upload_url = res.json()['uploadUrl']
            self.upload_token = res.json()['authorizationToken']
            return True
        else:
            if settings['debug_settings']['enable_logging']:
                logging.warning(f"Fetch upload url failed: {res.reason}")
            return False

    def upload(self):
        f = get_upload_photo()

        if f is None:
            if settings['debug_settings']['enable_logging']:
                logging.warning("No photo to upload, reasons above")
            return None

        file_name = f'{hashlib.md5(f).hexdigest()}.jpg'
        sha1_of_file_data = hashlib.sha1(f).hexdigest()

        if not self.b2_get_upload_url():
            return None

        headers = {
            'Authorization': self.upload_token, 'X-Bz-File-Name': file_name, 'Content-Type': 'image/jpeg',
            'X-Bz-Content-Sha1': sha1_of_file_data}
        res = requests.post(self.upload_url, data=f, headers=headers)
        if res.ok:
            return res.json()['fileName']
        else:
            if settings['debug_settings']['enable_logging']:
                logging.warning(f"Photo upload failed: {res.reason}")
            return None


##########################

barkingController = BarkingController()
while True:
    barkingController.get_machine_states()
    if not barkingController.is_printing:
        time.sleep(30)
        barkingController.notified_percentage = list()
        barkingController.start_of_print = True
    time.sleep(settings['query_interval'])
