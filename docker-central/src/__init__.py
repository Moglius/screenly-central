from flask import Flask, g, jsonify, request, make_response
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_admin import Admin, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
from pytz import timezone
import os

from .utils import *

host = os.environ['MYSQL_HOST']
database = os.environ['MYSQL_DB']
user = os.environ['MYSQL_USER']
password = os.environ['MYSQL_PASSWORD']

DATABASE_CONNECTION_URI = f'mysql://{user}:{password}@127.0.0.1:33306/{database}'

# Inicializo FLASK, SQLAlchemy, RestFul, Admin y Marshmallow
app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_CONNECTION_URI
app.config['SECRET_KEY'] = 'mysecret'
db = SQLAlchemy(app)
api = Api(app)
ma = Marshmallow(app)
admin = Admin(app, template_mode='bootstrap3')

tz = timezone('America/Argentina/Buenos_Aires')

'''
    Defino el modelo de datos de la app
'''

subscribers = db.Table('subscribers',
                    db.Column('device_id', db.Integer, db.ForeignKey('device.id')),
                    db.Column('file_id', db.Integer, db.ForeignKey('file.id'))
                    )

devicesubs = db.Table('devicesubs',
                    db.Column('device_id', db.Integer, db.ForeignKey('device.id')),
                    db.Column('asset_id', db.Integer, db.ForeignKey('asset.id'))
                    )

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36))
    asset_id = db.Column(db.String(36))
    job = db.Column(db.String(20))
    status = db.Column(db.String(36))

class TaskSchema(ma.ModelSchema):
    class Meta:
        model = Task

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    md5 = db.Column(db.String(32), unique=True, nullable=False)

    def __str__(self):
        return self.name

class FileSchema(ma.ModelSchema):
    class Meta:
        model = File

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(32), nullable=False)
    asset_name = db.Column(db.String(120), nullable=False)
    status = db.Column(db.Boolean)

class AssetSchema(ma.ModelSchema):
    class Meta:
        model = Asset

# Defino el modelo de la base de datos y los Schema Marshmallow
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    ident = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.now(tz))
    last_contact = db.Column(db.DateTime, default=datetime.now(tz))
    remote_state = db.Column(db.Boolean, default=False)
    remote_addr = db.Column(db.String(30), default="0.0.0.0")
    videos = db.relationship('File', secondary=subscribers, backref=db.backref('subcribers'))
    assets = db.relationship('Asset', secondary=devicesubs,
                             backref=db.backref('devicesubs'))

    def __str__(self):
        return self.name

class DeviceSchema(ma.ModelSchema):
    class Meta:
        model = Device


# Creo las tablas de la base
db.create_all()

'''
    Defino las vistas del modelo
'''

class DeviceView(ModelView):
    column_editable_list = ['name']
    form_columns = ['name', 'videos']
    column_list = ['name', 'ident', 'last_contact', 'remote_addr', 'videos']
    can_view_details = True
    can_export = True
    column_hide_backrefs = False
    column_searchable_list = ['name']
    column_filters = ['name']
    column_labels = dict(remote_addr='IP', ident='UUID')

    # Funcion para realizar el borrado de videos y dejar lista la tarea
    # para que los screenly la tomen y borren o agreguen los videos
    def update_model(self, form, model):

        # Obtengo el device segun el nombre del modelo
        device = Device.query.filter(Device.name == model.name).first()

        # detecto si existen videos borrados
        if ('videos' in form) and (device != None):

            videos_borrados = []

            # si se borraron videos
            if len(form['videos'].data) < len(device.videos):
                videos_borrados = [item for item in device.videos if item not in form['videos'].data]

            device.videos = form['videos'].data
            db.session.commit()

        # Genero la lista de tareas de borrado de assets del screenly
        if device != None:

            asset_list = []

            for asset in device.assets:

                for video in videos_borrados:

                    if video.name == asset.asset_name:
                        asset_list.append(asset)
                        break

            for asset in asset_list:
                # Genero tareas para el device si es que se borro algun video
                task = Task(
                    uuid=device.ident,
                    asset_id=asset.asset_id,
                    job='DELETE',
                    status='OPEN'
                )

                db.session.add(task)
                db.session.commit()

        if form['name'].data != device.name:
            device.name = form['name'].data
            db.session.commit()

        return True


class TaskView(ModelView):
    #column_editable_list = ['uuid', 'description']
    list_columns = ['id', 'uuid', 'asset_id', 'job', 'status']
    column_default_sort = ('id', True)
    form_columns = ['id', 'uuid', 'asset_id', 'job', 'status']
    can_export = True
    can_create = False
    can_edit = False
    can_delete = True
    column_searchable_list = ['id', 'uuid', 'asset_id', 'job', 'status']
    column_filters = ['uuid', 'asset_id', 'job', 'status']

class FileView(ModelView):
    can_create = False
    can_edit = False
    can_export = True
    column_searchable_list = ['name', 'md5']
    column_filters = ['name', 'md5']
    column_list = ['name', 'md5', 'subcribers']
    can_view_details = True
    can_export = True
    column_hide_backrefs = False

class ScreenView(BaseView):
    @expose('/')


    def index(self):
        devices = Device.query.all()

        return self.render('screen_index.html', devices=devices)

admin.add_view(ScreenView(name='Screens', endpoint='screens'))


class RemoteView(BaseView):
    @expose('/')


    def index(self):
        devices = Device.query.all()

        return self.render('remote_index.html', devices=devices)

admin.add_view(RemoteView(name='Remote', endpoint='remotes'))



# Defino las vistas del modelo
admin.add_view(DeviceView(Device, db.session))
admin.add_view(TaskView(Task, db.session))
admin.add_view(FileView(File, db.session))



'''
    Comienzo con el REST API
'''

'''
    Permite obtener la lista de Devices y crear nuevos
'''
class DeviceListResource(Resource):

    # List all devices
    def get(self):
        devices = Device.query.all()
        device_schema = DeviceSchema()

        data = {
            'message': 'Devices List',
            'devices': device_schema.dump(devices, many=True)
        }

        return make_response(jsonify(data), 200)

    # Create a new device
    def post(self):
        parser = reqparse.RequestParser()

        # Campo requerido del tipo string
        parser.add_argument('name', required=True, type=str)

        # Parse the arguments into an object
        args = parser.parse_args()

        device = Device(name=args['name'])
        db.session.add(device)
        db.session.commit()

        data = {
            'message': 'Device Added'
        }

        return make_response(jsonify(data), 200)

'''
    Permite listar, updatear y borrar un dispositivo
'''
class DeviceResource(Resource):

    # Get all fields of device
    def get(self, device_id):

        device = Device.query.filter(Device.id == device_id).first()
        device_schema = DeviceSchema()

        data = {
            'message': 'Device Found',
            'device': device_schema.dump(device)
        }

        return make_response(jsonify(data), 200)

    # Update name of device
    def put(self, device_id):
        parser = reqparse.RequestParser()

        # Campo requerido del tipo string
        parser.add_argument('name', required=True, type=str)

        # Parse the arguments into an object
        args = parser.parse_args()

        device = Device.query.filter(Device.id == device_id).first()
        device.name = args['name']

        db.session.commit()

        device_schema = DeviceSchema()

        data = {
            'message': 'Device Updated',
            'device': device_schema.dump(device)
        }

        return make_response(jsonify(data), 200)

    # update field last_contact
    def post(self, device_id):

        device = Device.query.filter(Device.id == device_id).first()
        device.last_contact = datetime.now(tz)

        db.session.commit()

        device_schema = DeviceSchema()

        data = {
            'message': 'Device Updated',
            'device': device_schema.dump(device)
        }

        return make_response(jsonify(data), 200)

    # Delete row by device_id
    def delete(self, device_id):

        Device.query.filter(Device.id == device_id).delete()
        db.session.commit()

        data = {
            'message': 'Device Deleted'
        }

        return make_response(jsonify(data), 200)

'''
    Permite listar, updatear y borrar un dispositivo
'''
class DeviceUuidResource(Resource):

    # Get all fields of device
    def get(self, uuid):

        device = Device.query.filter(Device.ident == uuid).first()
        file_schema = FileSchema()

        data = {
            'message': 'Videos Found',
            'videos': file_schema.dump(device.videos, many=True)
        }

        return make_response(jsonify(data), 200)

class DeviceUpdateResource(Resource):

    # Update name of device
    def put(self):
        parser = reqparse.RequestParser()

        # Campo requerido del tipo string
        parser.add_argument('uuid', required=True, type=str)

        # Parse the arguments into an object
        args = parser.parse_args()

        device = Device.query.filter(Device.ident == args['uuid']).first()
        device.last_contact = datetime.now(tz)

        try:
            device.remote_addr = request.headers.getlist("X-Forwarded-For")[0].split(',')[0]
        except Exception as e:
            device.remote_addr = "0.0.0.0"

        db.session.commit()

        device_schema = DeviceSchema()

        data = {
            'message': 'Device Updated',
            'device': device_schema.dump(device)
        }

        return make_response(jsonify(data), 200)

'''
    Definicion de rutas para Devices
'''
api.add_resource(DeviceListResource, '/api/v1/device')
api.add_resource(DeviceResource, '/api/v1/device/<device_id>')
api.add_resource(DeviceUpdateResource, '/api/v1/device/update')
api.add_resource(DeviceUuidResource, '/api/v1/device/<uuid>/videos')

'''
    Permite obtener la lista de Files y crear nuevos
'''
class FileListResource(Resource):

    # List all Files
    def get(self):
        files = File.query.all()
        file_schema = FileSchema()

        data = {
            'message': 'Files List',
            'files': file_schema.dump(files, many=True)
        }

        return make_response(jsonify(data), 200)

    # Create a new file
    def post(self):
        parser = reqparse.RequestParser()

        # Campo requerido del tipo string
        parser.add_argument('name', required=True, type=str)
        parser.add_argument('md5', required=True, type=str)

        # Parse the arguments into an object
        args = parser.parse_args()

        file = File(name=args['name'], md5=args['md5'])
        db.session.add(file)
        db.session.commit()

        data = {
            'message': 'File Added'
        }

        return make_response(jsonify(data), 200)

class FileResource(Resource):

    # Get all fields of device
    def get(self, md5):

        file = File.query.filter(File.md5 == md5).first()
        file_schema = FileSchema()

        data = {
            'message': 'Device Found',
            'file': file_schema.dump(file)
        }

        return make_response(jsonify(data), 200)

'''
    Definicion de rutas para Files
'''
api.add_resource(FileListResource, '/api/v1/file')
api.add_resource(FileResource, '/api/v1/file/<md5>')

'''
    Permite obtener la lista de Devices y crear nuevos
'''
class AssetResource(Resource):

    # Create a new device
    def post(self):
        req = request.get_json()

        uuid = req['uuid']

        device = Device.query.filter(Device.ident == uuid).first()
        device_schema = DeviceSchema()

        iter = 0

        for asset in req['assets']:

            iter = iter + 1

            exist = False
            asset_aux = 0


            for device_asset in device.assets:

                # if device_asset.asset_id == asset['asset_id']:

                if device_asset.asset_name == asset['name']:
                    exist = True
                    asset_aux = device_asset
                    break

            # si no esta en la lista del device, agrego uno nuevo y lo agrego a su lista
            if not exist:
                new_asset = Asset()
                new_asset.asset_id = asset['asset_id']
                new_asset.asset_name = asset['name']
                new_asset.status = asset['is_active']

                db.session.add(new_asset)
                db.session.commit()

                new_asset.devicesubs.append(device)
                db.session.commit()
            else:
                # si existe chequeo si cambio el estado de activo
                asset_aux.status = asset['is_active']
                asset_aux.asset_id = asset['asset_id']
                db.session.commit()

        if iter == 0:
            print("borrar el contenido de device.assets")
            device.assets = []
            db.session.commit()

        data = {
            'message': 'Device Added'
        }

        return make_response(jsonify(data), 200)

    # Delete asset from device
    def delete(self):
        req = request.get_json()

        uuid = req['uuid']
        asset_id = req['asset_id']

        device = Device.query.filter(Device.ident == uuid).first()
        device_schema = DeviceSchema()

        for asset in device.assets:

            if asset.asset_id == asset_id:
                db.session.delete(asset)
                db.session.commit()

        data = {
            'message': 'Asset Deleted'
        }

        return make_response(jsonify(data), 200)

    # Create a new device
    def put(self):
        req = request.get_json()

        device_id = req['device_id']
        asset_id = req['asset_id']
        state = req['state']

        device = Device.query.filter(Device.id == device_id).first()
        asset_schema = AssetSchema()

        asset_return = ""

        for asset in device.assets:

            if int(asset_id) == asset.id:
                asset.status = state
                db.session.commit()
                asset_return = asset
                break

        # MDM aca tengo q hacer la movida de crear la tarea
        # usar el asset_return para crearla
        #uuid = db.Column(db.String(36))
        #asset_id = db.Column(db.String(36))
        #job = db.Column(db.String(20))
        #status = db.Column(db.String(36))

        device = Device.query.filter(Device.id == device_id).first()

        task = Task(uuid=device.ident,
                    asset_id=asset_return.asset_id,
                    status='OPEN'
                    )

        if asset_return.status:
            # Activate TASK
            task.job = 'ACTIVATE'
        else:
            # Deactivate TASK
            task.job = 'DEACTIVATE'

        db.session.add(task)
        db.session.commit()


        data = {
            'message': 'Asset updated',
            'asset': asset_schema.dump(asset_return)
        }

        return make_response(jsonify(data), 200)

class AssetListResource(Resource):

    # Create a new device
    def get(self, id_device):


        device = Device.query.filter(Device.id == id_device).first()
        asset_schema = AssetSchema()

        data = {
                'assets': asset_schema.dump(device.assets, many=True)
        }

        return make_response(jsonify(data), 200)

class AssetList2Resource(Resource):

    # Create a new device
    def get(self, uuid):

        device = Device.query.filter(Device.ident == uuid).first()
        asset_schema = AssetSchema()

        data = {
                'assets': asset_schema.dump(device.assets, many=True)
        }

        return make_response(jsonify(data), 200)


api.add_resource(AssetResource, '/api/v1/asset')
api.add_resource(AssetListResource, '/api/v1/asset/<id_device>')
api.add_resource(AssetList2Resource, '/api/v1/asset/<uuid>/assets')

class TaskResource(Resource):

    # Create a new device
    def get(self, uuid):

        tasks = Task.query.filter(Task.uuid == uuid).\
                filter(Task.status == "OPEN").all()
        task_schema = TaskSchema()

        data = {
                'tasks': task_schema.dump(tasks, many=True)
        }

        return make_response(jsonify(data), 200)

class TaskListResource(Resource):

    # Create a new device
    def put(self):

        parser = reqparse.RequestParser()

        # Campo requerido del tipo string
        parser.add_argument('id', required=True, type=int)

        # Parse the arguments into an object
        args = parser.parse_args()

        task = Task.query.filter(Task.id == args['id']).first()
        task_schema = TaskSchema()

        task.status = 'CLOSED'
        db.session.commit()

        print(task)

        data = {
                'message': 'Task updated',
                'task': task_schema.dump(task)
        }

        return make_response(jsonify(data), 200)

    def post(self):

        parser = reqparse.RequestParser()

        # Campo requerido del tipo string
        parser.add_argument('id', required=True, type=int)
        parser.add_argument('state', required=True)

        # Parse the arguments into an object
        args = parser.parse_args()

        device = Device.query.filter(Device.id == args['id']).first()
        task_schema = TaskSchema()

        task = Task(uuid=device.ident, asset_id='NA', status='OPEN')

        print(args['state'])

        if args['state'] == "True":
            task.job = 'REMOTE-ACTIVATE'
            device.remote_state = True
            os.system("fuser -k 5050/tcp")
            os.system("fuser -k 5000/tcp")
        else:
            task.job = 'REMOTE-DEACTIVATE'
            device.remote_state = False

        db.session.add(task)
        db.session.commit()

        data = {
                'message': 'Task Created',
                'task': task_schema.dump(task)
        }

        return make_response(jsonify(data), 200)


api.add_resource(TaskResource, '/api/v1/task/<uuid>')
api.add_resource(TaskListResource, '/api/v1/task')
