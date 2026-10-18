from flask import Blueprint, flash, redirect, render_template, request, url_for
from extensions import db
from models.Matiere import Matiere

MatiereRouter = Blueprint('MatiereRouter', __name__, url_prefix='/matieres')


@MatiereRouter.route('/liste_matieres', methods=['GET'])
def liste_matieres():
    matieres = Matiere.query.order_by(Matiere.intMat.asc()).all()
    return render_template('matieres.html', matieres=matieres)


@MatiereRouter.route('/ajouter_matiere', methods=['GET', 'POST'])
def ajouter_matiere():
    form_data = {
        'codeMat': '',
        'intMat': '',
        'description': ''
    }
    errors = {}

    if request.method == 'POST':
        code_mat = request.form.get('codeMat', '').strip()
        int_mat = request.form.get('intMat', '').strip()
        description = request.form.get('description', '').strip()

        form_data['codeMat'] = code_mat
        form_data['intMat'] = int_mat
        form_data['description'] = description

        if not code_mat:
            errors['codeMat'] = 'Le code de la matière est obligatoire.'
        if not int_mat:
            errors['intMat'] = 'Le nom de la matière est obligatoire.'

        if not errors:
            if Matiere.query.get(code_mat):
                errors['codeMat'] = 'Cette matière existe déjà.'
            elif Matiere.query.filter_by(intMat=int_mat).first():
                errors['intMat'] = 'Cette matière existe déjà.'

        if not errors:
            matiere = Matiere(codeMat=code_mat, intMat=int_mat, description=description or None)
            db.session.add(matiere)
            try:
                db.session.commit()
                flash('Matière créée avec succès.', 'success')
                return redirect(url_for('MatiereRouter.liste_matieres'))
            except Exception:
                db.session.rollback()
                flash('Une erreur est survenue lors de la création de la matière.', 'error')

    return render_template('new_matiere.html', form_data=form_data, errors=errors)
