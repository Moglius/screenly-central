# Screenly-central
Screenly Central Management (Python FLASK app)

![alt text](https://blacklist.noname-it.com.ar/central.png)

## Features:

- `Central Administration`
- `Activate/deactivate Assets`
- `Upload videos`
- `Connection like Cloud/IoT (not VPN)`
- `Reverse web SSH shell`
- `Reverse web GUI shell`

## Screenshots:

### - Devices:

![alt text](https://blacklist.noname-it.com.ar/devices.jpeg)

### - Screens:

![alt text](https://blacklist.noname-it.com.ar/Screenly_selected.jpeg)

### - Files:

![alt text](https://blacklist.noname-it.com.ar/files.jpeg)

### - Remote Admin:

![alt text](https://blacklist.noname-it.com.ar/remote_admin.jpeg)

### - Web GUI reverse:

![alt text](https://blacklist.noname-it.com.ar/reverse_webgui.png)

### - Web SSH GUI:

![alt text](https://blacklist.noname-it.com.ar/reverse_webshell.jpg)

### - Task List

![alt text](https://blacklist.noname-it.com.ar/tasks.jpeg)

##
## Limitations & considerations:

- `Only videos can upload from the central web gui`
- `Reverse SSH/GUI shell use a public key infra to generate the tunnel`
- `Request Auth use basic Auth from nginx/apache config, the application not implement authentication`
- `All Connection are genereted from the IoT devices to the central manament app`

##
## Reverse Web SSH Shell:

The reverse SSH shell use a docker from docker hub:

https://hub.docker.com/r/snsyzb/webssh

All rights reserved to the developer.

