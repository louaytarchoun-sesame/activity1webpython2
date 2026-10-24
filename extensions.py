from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, IMAGES

photos = UploadSet("photos", IMAGES)
db = SQLAlchemy()