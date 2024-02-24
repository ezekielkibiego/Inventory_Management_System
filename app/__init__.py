from flask import Flask
from config import Config

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)

from app.models import db
db.init_app(app)

from flask_migrate import Migrate
migrate = Migrate(app, db)


from app import routes, models


app.config['UPLOAD_FOLDER'] = 'images'


