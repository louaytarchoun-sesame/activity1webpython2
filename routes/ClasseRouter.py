from flask import Blueprint, flash, redirect, render_template, request, url_for
from models.Classe import Classe
from extensions import db

ClasseRouter = Blueprint("ClasseRouter", __name__, url_prefix="/classes")

@ClasseRouter.route('/liste_classes', methods=["GET"])
def liste_classes():
    classes = Classe.query.order_by(Classe.codClass.asc()).all()
    return render_template('classes.html', classes=classes)

@ClasseRouter.route('/ajouter_classe', methods=['GET', 'POST'])
def ajouter_classe():
    form_data = {
        'codClass': '',
        'nomClass': '',
        'nbrEtudiant': ''
    }
    errors = {}

    if request.method == 'POST':
        cod_class = request.form.get('codClass', '').strip()
        nom_class = request.form.get('nomClass', '').strip()
        nbr_etudiant = request.form.get('nbrEtudiant', '').strip()

        form_data['codClass'] = cod_class
        form_data['nomClass'] = nom_class
        form_data['nbrEtudiant'] = nbr_etudiant

        if not cod_class:
            errors['codClass'] = 'Le code de la classe est obligatoire.'
        if not nom_class:
            errors['nomClass'] = 'Le nom de la classe est obligatoire.'

        if nbr_etudiant == '':
            nbr_etudiant = 0
        try:
            nbr_etudiant = int(nbr_etudiant)
        except ValueError:
            errors['nbrEtudiant'] = 'Le nombre d\'étudiants doit être un entier.'

        if not errors:
            if Classe.query.get(cod_class):
                errors['codClass'] = 'Cette classe existe déjà.'
            elif Classe.query.filter_by(nomClass=nom_class).first():
                errors['nomClass'] = 'Ce nom de classe existe déjà.'

        if not errors:
            classe = Classe(codClass=cod_class, nomClass=nom_class, nbrEtudiant=nbr_etudiant)
            db.session.add(classe)
            try:
                db.session.commit()
                flash('Classe créée avec succès.', 'success')
                return redirect(url_for('ClasseRouter.liste_classes'))
            except Exception:
                db.session.rollback()
                flash('Une erreur est survenue lors de la création de la classe.', 'error')

    return render_template('new_classe.html', form_data=form_data, errors=errors)
