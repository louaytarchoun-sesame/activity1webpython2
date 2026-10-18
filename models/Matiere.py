from extensions import db

class Matiere(db.Model):
    codeMat = db.Column(db.String(10), primary_key=True)
    intMat = db.Column(db.String(20), unique=True)
    description = db.Column(db.String(40))
    