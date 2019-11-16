import requests
import hashlib
import os
import time
import subprocess
import signal
import urllib3

uuid = os.environ["UUID"]
directory = r'/usr/src/screen/videos/'
url_down = os.environ["DOWN_URL"]
api_url = os.environ["API_URL"]
uri_fileasset = 'api/v1/file_asset'
uri_asset = 'api/v1.2/assets'
url_screen = 'http://127.0.0.1:8080/'
espera = 10
remote_ssh = os.environ["HOST_SSH"] + ' -p2244'
timeout_request = 30
usr_down = os.environ["USR_DOWN"]
pass_down = os.environ["PASS_DOWN"]
usr_api = os.environ["USR_API"]
pass_api = os.environ["PASS_API"]


headers = {
        "Content-Type": "application/json"
    }

urllib3.disable_warnings()

def file_as_bytes(file):
    with file:
        return file.read()

def update_last_contact(api_url, uuid, headers):

    dataDict = {
        "uuid": uuid
    }

    response = requests.request(
        method='PUT',
        auth=(usr_api, pass_api),
        url=api_url + "device/update",
        json=dataDict,
        headers=headers,
        timeout=timeout_request,
        verify=False
    )

    return response

def print_except(e, tipo="conexion"):

    print("*******************************************************************************")
    print("*********************** Ocurrio un problema de "+ tipo + "***********************")
    print("*******************************************************************************")
    print(str(e))

def check_task():

    try:
        # Primero pido lista de archivos que tengo en la nube
        response = requests.request(
            method='GET',
            url=api_url + 'task/' + uuid,
            headers=headers,
            auth=(usr_api, pass_api),
            timeout = timeout_request,
            verify=False
        )
    except Exception as e:
        print(e)

    if response.status_code == 200:
        data = response.json()
    else:
        raise Exception('Problemas de conexion con la API: ' + api_url + "task/" + uuid)

    for (k, v) in data.items():
        if (k == 'tasks'):
            tasks = v

    for task in tasks:

        ok = False

        if task['job'] == 'DELETE':

            print("DELETE TASK: Se procede a borrar el arrhivo")

            # Borro el asset del Screenly
            try:
                response = requests.request(
                    method='DELETE',
                    url=url_screen + uri_asset + '/' + task['asset_id'],
                    headers=headers,
                    timeout=timeout_request,
                    verify=False
                )
            except Exception as e:
                print(e)

            if response.status_code == 204:

                print("DELETE TASK: Archivo Borrado del screenly")

                # Si se pudo borrar, borro lo mismo en la nube
                json = {
                    'asset_id': task['asset_id'],
                    'uuid': task['uuid']
                }

                try:
                    response = requests.request(
                        method='DELETE',
                        url=api_url + 'asset',
                        json=json,
                        auth=(usr_api, pass_api),
                        headers=headers,
                        timeout=timeout_request,
                        verify=False
                    )
                except Exception as e:
                    print(e)

                if response.status_code == 200:
                    ok = True
                    print("DELETE TASK: Se procede a borrar "
                          "el archivo en la nube")

        elif task['job'] == 'ACTIVATE':
            #print("Activo el asset")
            # primero hago un get del asset para tener el json

            print("ACTIVATE TASK: Se pide info del aseet al screenly")

            # pido datos del asset screenly
            try:
                response = requests.request(
                    method='GET',
                    url=url_screen + uri_asset + '/' + task['asset_id'],
                    headers=headers,
                    timeout=timeout_request,
                    verify=False
                )
            except Exception as e:
                print(e)

            if response.status_code == 200:
                #print(response.json())

                data = response.json()

                # luego creo un json con los cmabios de activacion

                json = {
                  "is_enabled": 1,
                  "mimetype": data['mimetype'],
                  "end_date": data['end_date'],
                  "is_active": 1,
                  "duration": data['duration'],
                  "is_processing": 0,
                  "asset_id": data["asset_id"],
                  "name": data['name'],
                  "nocache": 0,
                  "uri": data['uri'],
                  "skip_asset_check": 0,
                  "play_order": 0,
                  "start_date": data['start_date']
                }

                print("ACTIVATE TASK: Se envia el asset activado al screenly")

                # envio el nuevo json al screenly

                try:
                    response = requests.request(
                        method='PUT',
                        url=url_screen + uri_asset + '/' + task['asset_id'],
                        json=json,
                        headers=headers,
                        timeout=timeout_request,
                        verify=False
                    )
                except Exception as e:
                    print(e)

                # paso la variable ok a True

                if response.status_code == 200:
                    ok = True
                    print("ACTIVATE TASK: Asset Activado")
        elif task['job'] == 'DEACTIVATE':

            print("DEACTIVATE TASK: Se pide info del aseet al screenly")

            # pido datos del asset screenly
            try:
                response = requests.request(
                    method='GET',
                    url=url_screen + uri_asset + '/' + task['asset_id'],
                    headers=headers,
                    timeout=timeout_request,
                    verify=False
                )
            except Exception as e:
                print(e)

            if response.status_code == 200:
                # print(response.json())

                data = response.json()

                # luego creo un json con los cmabios de activacion

                json = {
                    "is_enabled": 0,
                    "mimetype": data['mimetype'],
                    "end_date": data['end_date'],
                    "is_active": 0,
                    "duration": data['duration'],
                    "is_processing": 0,
                    "asset_id": data["asset_id"],
                    "name": data['name'],
                    "nocache": 0,
                    "uri": data['uri'],
                    "skip_asset_check": 0,
                    "play_order": 0,
                    "start_date": data['start_date']
                }

                # envio el nuevo json al screenly

                print("DEACTIVATE TASK: Se envia el asset "
                      "desactivado al screenly")

                try:
                    response = requests.request(
                        method='PUT',
                        url=url_screen + uri_asset + '/' + task['asset_id'],
                        json=json,
                        headers=headers,
                        timeout=timeout_request,
                        verify=False
                    )
                except Exception as e:
                    print(e)

                # paso la variable ok a True

                if response.status_code == 200:
                    ok = True
                    print("DEACTIVATE TASK: Asset desactivado")

        else:

            try:

                full_ssh_command = 'ssh -o "StrictHostKeyChecking=no" ' \
                                   '-i id_rsa.pem -N ' \
                                   '-R 5000:localhost:22 ' + remote_ssh
                ssh_output = subprocess.Popen(full_ssh_command, shell=True)

                full_web_command = 'ssh -o "StrictHostKeyChecking=no" ' \
                                   '-i id_rsa.pem -N ' \
                                   '-R 5050:localhost:8080 ' + remote_ssh
                web_output = subprocess.Popen(full_web_command, shell=True)


                ssh_output_pid = ssh_output.pid
                web_output_pid = web_output.pid

                if  task['job'] == 'REMOTE-DEACTIVATE':

                    try:
                        os.killpg(os.getpgid(ssh_output_pid), signal.SIGTERM)
                        os.killpg(os.getpgid(web_output_pid), signal.SIGTERM)
                    except Exception as e:
                        print("Failed. No existe Remoto Activo")
                        print(e)

                    print("Se desactivo el acceso Remoto")

                else:
                    print("Se activo el acceso Remoto")

                ok = True

            except subprocess.CalledProcessError as e:
                print("Failed. Please check your config file.")


        # Paso a CLOSED la tarea
        if ok:

            json = {
                "id": task['id']
            }

            try:
                response = requests.request(
                    method='PUT',
                    url=api_url + 'task',
                    json=json,
                    auth=(usr_api, pass_api),
                    headers=headers,
                    timeout=timeout_request,
                    verify=False
                )
            except Exception as e:
                print(e)

            if response.status_code == 200:
                print("TASK CLOSED")

def push_assets(url_screen, uri_asset, uuid, api_url, headers):

    try:
        response = requests.request(
            method='GET',
            url=url_screen + uri_asset,
            timeout=timeout_request,
            verify=False
        )
    except Exception as e:
        print(e)
        raise Exception("Problemas para conectarse al screenly WS")

    data = {
        'uuid': uuid,
        'assets': response.json()
    }

    try:
        response = requests.request(
            method='POST',
            url=api_url + 'asset',
            json=data,
            auth=(usr_api, pass_api),
            headers=headers,
            timeout=timeout_request,
            verify=False
        )
    except Exception as e:
        print(e)

def download_files(espera, headers, api_url, uuid, url_screen, uri_asset, url_down, directory, uri_fileasset):

    try:
        # Primero pido lista de archivos que tengo en la nube
        response = requests.request(
            method='GET',
            auth=(usr_api, pass_api),
            url=api_url + 'device/' +uuid + '/videos',
            headers=headers,
            timeout=timeout_request,
            verify=False
        )
    except Exception as e:
        print_except(e)
        time.sleep(espera)

    if response.status_code == 200:
        data = response.json()
    else:
        raise Exception('Problemas de conexion con la API: ' + api_url + "device/" + uuid + "/videos")

    for (k, v) in data.items():
        if (k == 'videos'):
            videos = v

    # Chequeo si existe en la screenly local
    for video in videos:

        # Por cada uno de los archivos en el directorio
        exist = False
        try:
            response = requests.request(
                method='GET',
                url=url_screen + uri_asset,
                timeout=timeout_request,
                verify=False
            )
        except Exception as e:
            print_except(e)
            time.sleep(espera)
            # La idea es que esto no falle nunca, ya que es local
            # ver posibilidad de enviar telegram en estos casos
            # Es un caso raro
            break

        for screenly_video in response.json():

            if screenly_video['name'] == video['name']:
                exist = True
                break

        # si no encontro uno de los videos en la screenly, lo descargo de internet
        if not exist:

            print("Se detecto un nuevo video, se procede a descarga: " + video['name'])

            try:
                response = requests.request(
                    method='GET',
                    url=url_down + video['name'],
                    auth=(usr_down, pass_down),
                    stream=False,
                    timeout=timeout_request,
                    verify=False
                )
            except Exception as e:
                print_except(e)
                break

            print("Se procede a realizar la comprobacion md5")

            try:
                open(directory + video['name'], 'wb').write(
                    response.content)

                md5 = hashlib.md5(file_as_bytes(
                    open(os.path.join(directory, video['name']),
                         'rb'))).hexdigest()
            except Exception as e:
                print_except(e, "archivos")
                # La idea es que esto no falle nunca, ya que es local
                # ver posibilidad de enviar telegram en estos casos
                # Es un caso raro
                break

            if md5 == video['md5']:

                print("Se compararon los MD5 de forma satisfactoria: " + md5)

                try:

                    file = open(os.path.join(directory, video['name']), 'rb')

                except Exception as e:
                    print_except(e, "archivos")
                    # La idea es que esto no falle nunca, ya que es local
                    # ver posibilidad de enviar telegram en estos casos
                    # Es un caso raro
                    break

                print("Se procede a subir el archivo al screenly")
                try:
                    #response = requests.post(url_screen + uri_fileasset,
                    #                         files=(('filename', video['name']),
                    #                                ('file_upload', file)))
                    response = requests.request(
                        method='POST',
                        url=url_screen + uri_fileasset,
                        files=(('filename', video['name']), ('file_upload', file)),
                        timeout=1700,
                        verify=False
                    )

                except Exception as e:
                    print_except(e)
                    # La idea es que esto no falle nunca, ya que es local
                    # ver posibilidad de enviar telegram en estos casos
                    # Es un caso raro
                    break

                if response.status_code == 200:

                    dataDict = {
                        "mimetype": "video",
                        "is_enabled": 1,
                        "name": video['name'],
                        "end_date": "9999-10-28T22:42:53.942Z",
                        "play_order": 0,
                        "duration": 0,
                        "nocache": 0,
                        "uri": response.json(),
                        "skip_asset_check": 0,
                        "start_date": "2019-10-28T22:42:53.942Z"
                    }

                    try:
                        #r = requests.post(url_screen + uri_asset, json=dataDict, headers=headers)

                        response = requests.request(
                            method='POST',
                            url=url_screen + uri_asset,
                            headers=headers,
                            json=dataDict,
                            timeout=timeout_request,
                            verify=False
                        )

                    except Exception as e:
                        print_except(e)
                        # La idea es que esto no falle nunca, ya que es local
                        # ver posibilidad de enviar telegram en estos casos
                        # Es un caso raro
                        break

                    if response.status_code == 201:
                        print("El archivo fue subido al screenly: " + video['name'])
                    else:
                        print("Problemas al subir el archivo al screenly")
                        raise Exception("Error al subier archivo")
                else:
                    print("No se pudo subir el asset al screenly")
                    raise Exception("Error al subir el Asset al screenly")
            else:
                print('MD5 fail: remoto(' + video['md5'] + ') - local(' + md5 + ')')

            try:
                os.remove(os.path.join(directory, video['name']))
            except Exception as e:
                print_except(e, "Archivo")
                # La idea es que esto no falle nunca, ya que es local
                # ver posibilidad de enviar telegram en estos casos
                # Es un caso raro
                break


def check_local_delete():

    try:
        # Primero pido lista de archivos que tengo en la nube
        response = requests.request(
            method='GET',
            auth=(usr_api, pass_api),
            url=api_url + 'device/' + uuid + '/videos',
            headers=headers,
            timeout=timeout_request,
            verify = False
        )
    except Exception as e:
        print_except(e)
        time.sleep(espera)

    if response.status_code == 200:
        data = response.json()
    else:
        raise Exception('Problemas de conexion con la API: ' + api_url + "device/" + uuid + "/videos")

    for (k, v) in data.items():
        if (k == 'videos'):
            videos = v

    try:
        # Primero pido lista de assets que tengo en la nube
        response = requests.request(
            method='GET',
            auth=(usr_api, pass_api),
            url=api_url + 'asset/' + uuid + '/assets',
            headers=headers,
            timeout=timeout_request,
            verify=False
        )
    except Exception as e:
        print_except(e)
        time.sleep(espera)

    if response.status_code == 200:
        data = response.json()
    else:
        raise Exception('Problemas de conexion con la API: ' + api_url + "device/" + uuid)

    for (k, v) in data.items():
        if (k == 'assets'):
            assets = v

    cloud_assets = []

    for asset in assets:

        exist = False

        for video in videos:

            if video['name'] == asset['asset_name']:
                exist = True
                break

        if not exist:
            cloud_assets.append(asset)

    try:
        response = requests.request(
            method='GET',
            url=url_screen + uri_asset,
            timeout=timeout_request,
            verify=False
        )
    except Exception as e:
        print(e)

    if response.status_code == 200:
        data = response.json()
    else:
        raise Exception('Problemas de conexion con la Screenly')

    remove_assets = []

    for cloud_asset in cloud_assets:

        exist = False

        for local_asset in data:

            if cloud_asset['asset_name'] == local_asset['name']:
                exist = True
                break

        if not exist:
            remove_assets.append(cloud_asset)

    for remove_asset in remove_assets:

        print("Se Borro un Asset Local y se borrará de la nube: "
              + remove_asset['asset_name'])

        data = {
            'uuid': uuid,
            'asset_id': remove_asset['asset_id']
        }

        try:
            response = requests.request(
                method='DELETE',
                url=api_url + 'asset',
                json=data,
                auth=(usr_api, pass_api),
                headers=headers,
                timeout=timeout_request,
                verify=False
            )
        except Exception as e:
            print(e)

        if response.status_code == 200:
            print("El Asset fue borrado de la nube")


def remove_files(folder):

    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            # elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)


while True:

    remove_files(directory)

    # Contacto a la api para hacer update de last_contact
    try:
        response = update_last_contact(api_url, uuid, headers)
    except Exception as e:
        print_except(e)
        time.sleep(espera)
        continue

    # Si la respuesta fue favorable
    if response.status_code == 200:

        # Funcion que detecta si tenemos algun archivo para descargar en base
        # a los archivos seleccionados en device de flask admin
        try:
            download_files(espera, headers, api_url, uuid, url_screen, uri_asset, url_down, directory, uri_fileasset)
        except Exception as e:
            print_except(e)
            time.sleep(espera)
            continue

        # funcion que sube los assets que poseemos en la screenly a la nube
        try:
            push_assets(url_screen, uri_asset, uuid, api_url, headers)
        except Exception as e:
            print_except(e)
            time.sleep(espera)

        # funcion que chequea tareas en la nube, delete, deactivate o activate
        try:
            check_task()
        except Exception as e:
            print_except(e)
            time.sleep(espera)
            continue

        # funcion que chequea los assets y los compara con los assets
        # en la nube y borra aquellos que han sido borrados localmente
        # esto solo pasa con las cargas locales

        try:
            check_local_delete()
        except Exception as e:
            print_except(e)
            time.sleep(espera)
            continue

    else:
        # ver tema de enviar por telegram si tenemos internet pero esto fallo
        # de todas formas avisar 3 veces, luego cortar envio para no volver loco
        # si se detecta q anduvo ok nuevamente, ahi avisar.
        print("Se produjo un error en la consulta de last_contact")

    time.sleep(espera)
