# Screenly-central
Screenly Central Management (Python FLASK app)

![alt text](https://blacklist.noname-it.com.ar/central.png)

## Features:

- `Central Administration`
- `Admin WebGUI (Flask Admin module)`
- `REST API for the connection (IOT-like) of screenly devices`
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

![alt text](https://blacklist.noname-it.com.ar/webssh.jpg)
###
![alt text](https://blacklist.noname-it.com.ar/reverse_webshell.jpg)

### - Task List

![alt text](https://blacklist.noname-it.com.ar/tasks.jpeg)

##
## Limitations & considerations:

- `Only videos can upload from the central web gui`
- `The app not implement the upload, only scan a directory in the host`
- `Reverse SSH/GUI shell use a public key infra to generate the tunnel`
- `All Request use basic Auth from nginx/apache config, the application itself not implement any kind of authentication`
- `All Connection are genereted from the IoT devices to the central manament app`

##
## Reverse Web SSH Shell:

The reverse SSH shell use a docker from docker hub:

https://hub.docker.com/r/snsyzb/webssh

All rights reserved to the developer.


