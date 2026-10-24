from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_uploads import UploadNotAllowed
from sqlalchemy.exc import IntegrityError

from extensions import db, photos
from models.Absence import Absence
from models.Classe import Classe
from models.Etudiant import Etudiant

EtudiantRouter = Blueprint('EtudiantRouter', __name__, url_prefix='/etudiants')
PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def _validate_photo(photo_file):
    if not photo_file or not photo_file.filename:
        return

    if '.' not in photo_file.filename:
        raise UploadNotAllowed('Le fichier doit avoir une extension image autorisée.')

    extension = photo_file.filename.rsplit('.', 1)[1].lower()
    if extension not in PHOTO_EXTENSIONS or not photos.file_allowed(photo_file, photo_file.filename):
        raise UploadNotAllowed('Formats autorisés : PNG, JPG, JPEG et GIF.')


def _validate_student_form(form_data, current_nce=None):
    errors = {}
    date_nais = None

    for field, label in (
        ('nce', 'Le NCE'),
        ('nom', 'Le nom'),
        ('prenom', 'Le prénom'),
        ('dateNais', 'La date de naissance'),
        ('lieuNais', 'Le lieu de naissance'),
        ('classe_id', 'La classe'),
    ):
        if not form_data[field]:
            errors[field] = f'{label} est obligatoire.'

    if form_data['nce'] and len(form_data['nce']) > 5:
        errors['nce'] = 'Le NCE ne peut pas dépasser 5 caractères.'
    elif form_data['nce'] and form_data['nce'] != current_nce:
        if Etudiant.query.get(form_data['nce']):
            errors['nce'] = 'Ce NCE est déjà utilisé.'

    if form_data['dateNais']:
        try:
            date_nais = datetime.strptime(form_data['dateNais'], '%Y-%m-%d').date()
        except ValueError:
            errors['dateNais'] = 'La date de naissance est invalide.'

    classe = Classe.query.get(form_data['classe_id']) if form_data['classe_id'] else None
    if form_data['classe_id'] and classe is None:
        errors['classe_id'] = 'La classe sélectionnée est introuvable.'

    return errors, date_nais, classe


def _student_form_data(etudiant=None):
    if etudiant is None:
        return {'nce': '', 'nom': '', 'prenom': '', 'dateNais': '', 'lieuNais': '', 'classe_id': ''}
    return {
        'nce': etudiant.nce,
        'nom': etudiant.nom or '',
        'prenom': etudiant.prenom or '',
        'dateNais': etudiant.dateNais.isoformat() if etudiant.dateNais else '',
        'lieuNais': etudiant.lieuNais or '',
        'classe_id': etudiant.classe_id or '',
    }


@EtudiantRouter.route('/liste_etudiants', methods=['GET'])
def liste_etudiants():
    etudiants = Etudiant.query.order_by(Etudiant.nom.asc(), Etudiant.prenom.asc()).all()
    return render_template('etudiants.html', etudiants=etudiants)


@EtudiantRouter.route('/ajouter_etudiant', methods=['GET', 'POST'])
def ajouter_etudiant():
    classes = Classe.query.order_by(Classe.nomClass.asc()).all()
    form_data = _student_form_data()
    errors = {}

    if request.method == 'POST':
        photo = request.files.get('photo')
        for field in form_data:
            form_data[field] = request.form.get(field, '').strip()

        errors, date_nais, classe = _validate_student_form(form_data)

        photo_name = None
        if photo and photo.filename:
            try:
                _validate_photo(photo)
                photo_name = photos.save(photo)
            except UploadNotAllowed as exc:
                errors['photo'] = str(exc)

        if not errors:
            try:
                etudiant = Etudiant(
                    nce=form_data['nce'],
                    nom=form_data['nom'],
                    prenom=form_data['prenom'],
                    dateNais=date_nais,
                    lieuNais=form_data['lieuNais'],
                    classe_id=form_data['classe_id'],
                    photo=photo_name,
                )
                db.session.add(etudiant)
                if classe is not None:
                    classe.nbrEtudiant = (classe.nbrEtudiant or 0) + 1
                db.session.commit()
                flash('Étudiant ajouté avec succès.', 'success')
                return redirect(url_for('EtudiantRouter.liste_etudiants'))
            except Exception:
                db.session.rollback()
                flash('Une erreur est survenue lors de l’ajout de l’étudiant.', 'error')

    return render_template('new_etudiant.html', classes=classes, form_data=form_data, errors=errors)


@EtudiantRouter.route('/modifier_etudiant/<string:nce>', methods=['GET', 'POST'])
def modifier_etudiant(nce):
    etudiant = Etudiant.query.get(nce)
    if etudiant is None:
        flash('Étudiant introuvable.', 'error')
        return redirect(url_for('EtudiantRouter.liste_etudiants'))

    classes = Classe.query.order_by(Classe.nomClass.asc()).all()
    form_data = _student_form_data(etudiant)
    errors = {}

    if request.method == 'POST':
        for field in ('nom', 'prenom', 'dateNais', 'lieuNais', 'classe_id'):
            form_data[field] = request.form.get(field, '').strip()

        photo = request.files.get('photo')
        errors, date_nais, nouvelle_classe = _validate_student_form(form_data, current_nce=etudiant.nce)

        if photo and photo.filename:
            try:
                _validate_photo(photo)
            except UploadNotAllowed as exc:
                errors['photo'] = str(exc)

        if not errors:
            ancienne_classe = etudiant.classe
            try:
                if photo and photo.filename:
                    etudiant.photo = photos.save(photo)

                etudiant.nom = form_data['nom']
                etudiant.prenom = form_data['prenom']
                etudiant.dateNais = date_nais
                etudiant.lieuNais = form_data['lieuNais']
                etudiant.classe_id = form_data['classe_id']

                if ancienne_classe and ancienne_classe.codClass != form_data['classe_id']:
                    ancienne_classe.nbrEtudiant = max((ancienne_classe.nbrEtudiant or 0) - 1, 0)
                    nouvelle_classe.nbrEtudiant = (nouvelle_classe.nbrEtudiant or 0) + 1

                db.session.commit()
                flash('Étudiant modifié avec succès.', 'success')
                return redirect(url_for('EtudiantRouter.liste_etudiants'))
            except Exception:
                db.session.rollback()
                flash('Une erreur est survenue lors de la modification de l’étudiant.', 'error')

    return render_template(
        'edit_etudiant.html',
        etudiant=etudiant,
        classes=classes,
        form_data=form_data,
        errors=errors,
    )


@EtudiantRouter.route('/supprimer_etudiant/<string:nce>', methods=['POST'])
def supprimer_etudiant(nce):
    etudiant = Etudiant.query.get(nce)
    if etudiant is None:
        flash('Étudiant introuvable.', 'error')
        return redirect(url_for('EtudiantRouter.liste_etudiants'))

    if Absence.query.filter_by(nce=nce).first():
        flash('Suppression impossible : cet étudiant possède un historique d’absences.', 'error')
        return redirect(url_for('EtudiantRouter.liste_etudiants'))

    classe = etudiant.classe
    try:
        db.session.delete(etudiant)
        if classe:
            classe.nbrEtudiant = max((classe.nbrEtudiant or 0) - 1, 0)
        db.session.commit()
        flash('Étudiant supprimé avec succès.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Suppression impossible à cause d’une contrainte liée à cet étudiant.', 'error')
    except Exception:
        db.session.rollback()
        flash('Une erreur est survenue lors de la suppression de l’étudiant.', 'error')

    return redirect(url_for('EtudiantRouter.liste_etudiants'))