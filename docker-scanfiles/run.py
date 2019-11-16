import hashlib
import os
import requests
import time

api_url = 'http://localhost:3005/api/v1/file'
directory = r'/var/www/html/videos'
scan_time = int(os.environ["SCANTIME"])

headers = {
        "Content-Type": "application/json"
    }

def file_as_bytes(file):
    with file:
        return file.read()

while True:

    try:
        response = requests.request(
            method='GET',
            url=api_url,
            headers=headers
        )
    except Exception as e:
        print(e)

    if response.status_code == 200:
        data = response.json()
    else:
        raise Exception('Problemas de conexion con la API: ' + api_url)

    for (k, v) in data.items():
        if (k == 'files'):
            files = v

    # Por cada uno de los archivos en el directorio
    for filename in os.listdir(directory):

            exist = False

            # Chequeo si existe en
            for file in files:

                if filename == file['name']:
                    exist = True
                    break

            if not exist:

                print("Se detecto un arhivo nuevo: " + filename)

                try:
                    md5 = hashlib.md5(file_as_bytes(
                        open(os.path.join(directory, filename), 'rb'))).hexdigest()
                except Exception as e:
                    print(e)
                    break

                try:
                    response2 = requests.request(
                        method='POST',
                        url=api_url,
                        json={
                                "name": filename,
                                "md5": md5
                        },
                        headers=headers
                    )
                except Exception as e:
                    print(e)

                if response2.status_code == 200:
                    print('El archivo ha sido cargado: '+filename)
                else:
                    raise Exception('Problemas de conexion con la API: ' + api_url)

    time.sleep(scan_time)


