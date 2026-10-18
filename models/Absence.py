from extensions import db

class Absence(db.Model):
    codeMat = db.Column(db.String(10), db.ForeignKey('matiere.codeMat', onupdate="CASCADE", ondelete="CASCADE"), nullable=False, primary_key=True)
    nce = db.Column(db.String(5), db.ForeignKey('etudiant.nce', onupdate="CASCADE", ondelete="CASCADE"), nullable=False, primary_key=True)
    dateA = db.Column(db.Date(), nullable=False, primary_key=True)
    nha = db.Column(db.Float, nullable=False)
