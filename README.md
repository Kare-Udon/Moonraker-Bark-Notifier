# Moonraker Bark Notifier

Moonraker-Bark-Notifier is a Python 3 script that connects to your 
[Moonraker API server](https://github.com/Arksine/moonraker) and 
notifies you through [Bark](https://github.com/Finb/Bark) when the printing process
reaches the percentage you set and when the printing status changes.

If you have a webcam, the script can upload the photo to Backblaze B2 
Bucket and send the link of the photo to your phone. By just a click
and you can see the photo.

### Settings

File `settings-example.json` contains the example of settings for the script.

Please crate your own settings file and rename it to `settings.json`.

Here are the settings you can change:

#### Moonraker Setting

| Setting  | Description                         |
|----------|-------------------------------------|
| username | username of your moonraker account  |
| passwd   | password of your moonraker account  |
| url      | ip address of your moonraker API    |
| port     | port of your moonraker API          |

#### Webcam Settings

| Setting    | Description                                                            |
|------------|------------------------------------------------------------------------|
| has_camera | if you have a webcam, set true                                         |
| url        | url of your webcam (at the settings page of web console for moonraker) |

#### Bark Settings

| Setting     | Description                                    |
|-------------|------------------------------------------------|
| url         | bark server url and your bark key              |
| icon_url    | icon that will be shown in the notification    |
| max_retries | max number of retries to send the notification |

#### BackBlaze Settings

| Setting        | Description                       |
|----------------|-----------------------------------|
| url            | url to your Backblaze B2 Bucket   |
| keyID          | your Backblaze B2 key ID          |
| applicationKey | your Backblaze B2 application key |
| bucketID       | your Backblaze B2 bucket ID       |

#### Debug Settings

| Setting        | Description                                                                                                   |
|----------------|---------------------------------------------------------------------------------------------------------------|
| enable_logging | The log contains some information about the project you have printed. If you don't like it, just turn it off. |

#### Other Settings

| Setting                       | Description                                                         |
|-------------------------------|---------------------------------------------------------------------|
| notification_while_percentage | percentage of the printing process that will trigger a notification |
| query_interval                | interval in seconds that the script will query the printing status  |

P.S. I discovered that some machines ended at y_max so when the project finished, the photo sucks. 
So I suggest you to add a 99(%) to get a good-looking photo.

### Usage

#### with screen

```shell
git clone https://github.com/Lao-Liu233/Moonraker-Bark-Notifier.git
cd moonraker-bark-notifier
screen -S moonraker-bark-notifier
python3 main.py
# then you can detach the screen by typing: CTRL+A+D
```

#### with systemctl (not fully tested)

```shell
git clone https://github.com/Lao-Liu233/Moonraker-Bark-Notifier.git
sudo mv -r moonraker-bark-notifier /usr/local/bin/
cd /usr/local/bin/moonraker-bark-notifier
sudo mv moonraker-bark-notifier.service /etc/systemd/system/
sudo chmod 754 /etc/systemd/system/moonraker-bark-notifier.service
sudo systemctl daemon-reload
# start with system
sudo systemctl enable moonraker-bark-notifier.service
# start the service
sudo systemctl start moonraker-bark-notifier.service
# see the status
sudo systemctl status moonraker-bark-notifier.service
```

### Screen Shots

![Notification without photo](https://p.itxe.net/images/2022/02/04/21299C5D-68E2-4902-A10F-F887F30007BB.jpg)
Notification without photo

![Notification with photo](https://p.itxe.net/images/2022/02/04/9A982493-A08E-4225-B930-298892E5BD3A.jpg)
Notification with photo

![Photo in APP](https://p.itxe.net/images/2022/02/04/66610A92-35B1-4792-9D3B-D0DBFA33DF1E.jpg)
Photo in APP

### Special Thanks

Bark, a great iOS APP for customizing notifications.
https://github.com/Finb/Bark

Moonraker, excellent API for klipper.
https://github.com/Arksine/moonraker

Project inspired by moonraker-telegram-bot
https://github.com/nlef/moonraker-telegram-bot

Image hosting from itxe.net
https://p.itxe.net/