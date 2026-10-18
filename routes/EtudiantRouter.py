from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from extensions import db
from models.Classe import Classe
from models.Etudiant import Etudiant

EtudiantRouter = Blueprint('EtudiantRouter', __name__, url_prefix='/etudiants')


@EtudiantRouter.route('/liste_etudiants', methods=['GET'])
def liste_etudiants():
    etudiants = Etudiant.query.order_by(Etudiant.nom.asc(), Etudiant.prenom.asc()).all()
    return render_template('etudiants.html', etudiants=etudiants)


@EtudiantRouter.route('/ajouter_etudiant', methods=['GET', 'POST'])
def ajouter_etudiant():
    classes = Classe.query.order_by(Classe.nomClass.asc()).all()
    form_data = {
        'nce': '',
        'nom': '',
        'prenom': '',
        'dateNais': '',
        'lieuNais': '',
        'classe_id': ''
    }
    errors = {}

    if request.method == 'POST':
        nce = request.form.get('nce', '').strip()
        nom = request.form.get('nom', '').strip()
        prenom = request.form.get('prenom', '').strip()
        date_nais = request.form.get('dateNais', '').strip()
        lieu_nais = request.form.get('lieuNais', '').strip()
        classe_id = request.form.get('classe_id', '').strip()

        form_data.update({
            'nce': nce,
            'nom': nom,
            'prenom': prenom,
            'dateNais': date_nais,
            'lieuNais': lieu_nais,
            'classe_id': classe_id,
        })

        if not nce:
            errors['nce'] = 'Le NCE est obligatoire.'
        if not nom:
            errors['nom'] = 'Le nom est obligatoire.'
        if not prenom:
            errors['prenom'] = 'Le prénom est obligatoire.'
        if not date_nais:
            errors['dateNais'] = 'La date de naissance est obligatoire.'
        if not lieu_nais:
            errors['lieuNais'] = 'Le lieu de naissance est obligatoire.'
        if not classe_id:
            errors['classe_id'] = 'Veuillez sélectionner une classe.'

        try:
            if date_nais:
                date_nais = datetime.strptime(date_nais, '%Y-%m-%d').date().isoformat()
        except ValueError:
            errors['dateNais'] = 'La date de naissance est invalide.'

        if classe_id and not Classe.query.get(classe_id):
            errors['classe_id'] = 'La classe sélectionnée est introuvable.'

        if not errors:
            classe = Classe.query.get(classe_id)
            etudiant = Etudiant(
                nce=nce,
                nom=nom,
                prenom=prenom,
                dateNais=date_nais,
                lieuNais=lieu_nais,
                classe_id=classe_id
            )
            db.session.add(etudiant)
            try:
                if classe is not None:
                    classe.nbrEtudiant = (classe.nbrEtudiant or 0) + 1
                db.session.commit()
                flash('Étudiant ajouté avec succès.', 'success')
                return redirect(url_for('EtudiantRouter.liste_etudiants'))
            except Exception:
                db.session.rollback()
                flash('Une erreur est survenue lors de l\'ajout de l\'étudiant.', 'error')

    return render_template('new_etudiant.html', classes=classes, form_data=form_data, errors=errors)
