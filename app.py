from flask import Flask, render_template
from extensions import db 

app = Flask(__name__)

app.config['SECRET_KEY'] = 'scol_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:louuu@localhost:3306/scol'

db.init_app(app)

from models.User import User
from models.Classe import Classe
from models.Etudiant import Etudiant
from models.Matiere import Matiere
from models.Absence import Absence

from routes.UserRouter import UserRouter
from routes.ClasseRouter import ClasseRouter
from routes.MatiereRouter import MatiereRouter
from routes.EtudiantRouter import EtudiantRouter
from routes.AbsenceRouter import AbsenceRouter

app.register_blueprint(UserRouter)
app.register_blueprint(ClasseRouter)
app.register_blueprint(MatiereRouter)
app.register_blueprint(EtudiantRouter)
app.register_blueprint(AbsenceRouter)

app.app_context().push()

with app.app_context():
    db.create_all()
    
    
@app.route('/')
def index():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True)