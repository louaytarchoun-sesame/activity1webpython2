from extensions import db

class Classe(db.Model):
    codClass = db.Column(db.String(10), primary_key=True)
    nomClass = db.Column(db.String(20), unique=True)
    nbrEtudiant = db.Column(db.Integer, default=0)
    
    etudiants = db.relationship("Etudiant", back_populates="classe")
    