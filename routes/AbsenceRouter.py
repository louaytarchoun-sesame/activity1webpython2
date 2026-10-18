from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from extensions import db
from models.Absence import Absence
from models.Classe import Classe
from models.Etudiant import Etudiant
from models.Matiere import Matiere

AbsenceRouter = Blueprint('AbsenceRouter', __name__, url_prefix='/absences')


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


@AbsenceRouter.route('/matiere/<codeMat>', methods=['GET', 'POST'])
def absence_matiere(codeMat):
    matiere = Matiere.query.get(codeMat)
    if not matiere:
        flash('Matière introuvable.', 'error')
        return redirect(url_for('MatiereRouter.liste_matieres'))

    classes = Classe.query.order_by(Classe.nomClass.asc()).all()
    selected_class_id = request.form.get('classe_id', '') or request.args.get('classe_id', '')
    selected_date = request.form.get('dateA', '') or request.args.get('dateA', '')
    nha_value = request.form.get('nha', '') or request.args.get('nha', '')
    students = []

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'show_students':
            errors = []
            if not selected_class_id:
                errors.append('Veuillez sélectionner une classe.')
            if not selected_date:
                errors.append('La date d\'absence est obligatoire.')
            if not nha_value:
                errors.append('Le nombre d\'heures est obligatoire.')

            if not errors:
                selected_class = Classe.query.get(selected_class_id)
                if not selected_class:
                    errors.append('La classe sélectionnée est introuvable.')
                else:
                    parsed_date = _parse_date(selected_date)
                    if parsed_date is None:
                        errors.append('La date est invalide.')
                    else:
                        try:
                            nha = float(nha_value)
                        except ValueError:
                            errors.append('Le nombre d\'heures doit être un nombre valide.')
                        else:
                            if nha < 0:
                                errors.append('Le nombre d\'heures doit être positif.')
                            else:
                                students = Etudiant.query.filter_by(classe_id=selected_class_id).order_by(Etudiant.nom.asc(), Etudiant.prenom.asc()).all()
                                if not students:
                                    flash('Aucun étudiant n\'est inscrit dans cette classe.', 'warning')

                                return render_template(
                                    'absence_matiere.html',
                                    matiere=matiere,
                                    classes=classes,
                                    selected_class_id=selected_class_id,
                                    selected_date=selected_date,
                                    nha=nha_value,
                                    students=students,
                                    subject_date=parsed_date,
                                    subject_hours=nha,
                                )

            for error in errors:
                flash(error, 'error')

        elif action == 'save_absences':
            errors = []
            if not selected_class_id:
                errors.append('Veuillez sélectionner une classe.')
            if not selected_date:
                errors.append('La date d\'absence est obligatoire.')
            if not nha_value:
                errors.append('Le nombre d\'heures est obligatoire.')

            selected_class = None
            if selected_class_id:
                selected_class = Classe.query.get(selected_class_id)
                if not selected_class:
                    errors.append('La classe sélectionnée est introuvable.')

            parsed_date = _parse_date(selected_date) if selected_date else None
            if selected_date and parsed_date is None:
                errors.append('La date est invalide.')

            try:
                nha = float(nha_value) if nha_value else 0.0
            except ValueError:
                errors.append('Le nombre d\'heures doit être un nombre valide.')
                nha = 0.0

            if nha < 0:
                errors.append('Le nombre d\'heures doit être positif.')

            selected_student_ids = request.form.getlist('absent_students')
            valid_student_ids = []
            if selected_student_ids:
                for student_id in selected_student_ids:
                    student = Etudiant.query.get(student_id)
                    if student is None:
                        errors.append('Un étudiant sélectionné est introuvable.')
                        continue
                    if student.classe_id != selected_class_id:
                        errors.append('Un étudiant sélectionné n\'appartient pas à la classe choisie.')
                        continue
                    valid_student_ids.append(student_id)
            else:
                errors.append('Aucun étudiant absent n\'a été sélectionné.')

            if errors:
                for error in errors:
                    flash(error, 'error')
                students = Etudiant.query.filter_by(classe_id=selected_class_id).order_by(Etudiant.nom.asc(), Etudiant.prenom.asc()).all() if selected_class_id else []
                return render_template(
                    'absence_matiere.html',
                    matiere=matiere,
                    classes=classes,
                    selected_class_id=selected_class_id,
                    selected_date=selected_date,
                    nha=nha_value,
                    students=students,
                    subject_date=parsed_date,
                    subject_hours=nha,
                )

            created = 0
            skipped_duplicates = 0
            for student_id in valid_student_ids:
                existing = Absence.query.filter_by(codeMat=codeMat, nce=student_id, dateA=parsed_date).first()
                if existing is not None:
                    skipped_duplicates += 1
                    continue
                absence = Absence(codeMat=codeMat, nce=student_id, dateA=parsed_date, nha=nha)
                db.session.add(absence)
                created += 1

            if created == 0:
                flash('Aucun enregistrement d\'absence n\'a été créé. Les étudiants sélectionnés sont déjà enregistrés pour cette matière et cette date.', 'warning')
                return redirect(url_for('MatiereRouter.liste_matieres'))

            try:
                db.session.commit()
                flash(f'{created} absence(s) enregistrée(s) avec succès.', 'success')
                return redirect(url_for('MatiereRouter.liste_matieres'))
            except Exception:
                db.session.rollback()
                flash('Une erreur est survenue lors de l\'enregistrement des absences.', 'error')

    return render_template(
        'absence_matiere.html',
        matiere=matiere,
        classes=classes,
        selected_class_id=selected_class_id,
        selected_date=selected_date,
        nha=nha_value,
        students=students,
    )


@AbsenceRouter.route('/classe/<codClass>', methods=['GET', 'POST'])
def absence_classe(codClass):
    classe = Classe.query.get(codClass)
    if not classe:
        flash('Classe introuvable.', 'error')
        return redirect(url_for('ClasseRouter.liste_classes'))

    matieres = Matiere.query.order_by(Matiere.intMat.asc()).all()
    selected_mat = request.form.get('codeMat', '') or request.args.get('codeMat', '')
    selected_date = request.form.get('dateA', '') or request.args.get('dateA', '')
    nha_value = request.form.get('nha', '') or request.args.get('nha', '')
    students = Etudiant.query.filter_by(classe_id=codClass).order_by(Etudiant.nom.asc(), Etudiant.prenom.asc()).all()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'show_students':
            errors = []
            if not selected_mat:
                errors.append('Veuillez sélectionner une matière.')
            if not selected_date:
                errors.append('La date d\'absence est obligatoire.')
            if not nha_value:
                errors.append('Le nombre d\'heures est obligatoire.')

            if not errors:
                matiere = Matiere.query.get(selected_mat)
                if not matiere:
                    errors.append('La matière sélectionnée est introuvable.')
                else:
                    parsed_date = _parse_date(selected_date)
                    if parsed_date is None:
                        errors.append('La date est invalide.')
                    else:
                        try:
                            nha = float(nha_value)
                        except ValueError:
                            errors.append('Le nombre d\'heures doit être un nombre valide.')
                        else:
                            if nha < 0:
                                errors.append('Le nombre d\'heures doit être positif.')
                            else:
                                students = Etudiant.query.filter_by(classe_id=codClass).order_by(Etudiant.nom.asc(), Etudiant.prenom.asc()).all()
                                if not students:
                                    flash('Aucun étudiant n\'est inscrit dans cette classe.', 'warning')
                                return render_template(
                                    'absence_classe.html',
                                    classe=classe,
                                    matieres=matieres,
                                    selected_mat=selected_mat,
                                    selected_date=selected_date,
                                    nha=nha_value,
                                    students=students,
                                    subject_date=parsed_date,
                                    subject_hours=nha,
                                )

            for error in errors:
                flash(error, 'error')

        elif action == 'save_absences':
            errors = []
            if not selected_mat:
                errors.append('Veuillez sélectionner une matière.')
            if not selected_date:
                errors.append('La date d\'absence est obligatoire.')
            if not nha_value:
                errors.append('Le nombre d\'heures est obligatoire.')

            matiere = Matiere.query.get(selected_mat) if selected_mat else None
            if selected_mat and not matiere:
                errors.append('La matière sélectionnée est introuvable.')

            parsed_date = _parse_date(selected_date) if selected_date else None
            if selected_date and parsed_date is None:
                errors.append('La date est invalide.')

            try:
                nha = float(nha_value) if nha_value else 0.0
            except ValueError:
                errors.append('Le nombre d\'heures doit être un nombre valide.')
                nha = 0.0

            if nha < 0:
                errors.append('Le nombre d\'heures doit être positif.')

            selected_student_ids = request.form.getlist('absent_students')
            valid_student_ids = []
            if selected_student_ids:
                for student_id in selected_student_ids:
                    student = Etudiant.query.get(student_id)
                    if student is None:
                        errors.append('Un étudiant sélectionné est introuvable.')
                        continue
                    if student.classe_id != codClass:
                        errors.append('Un étudiant sélectionné n\'appartient pas à la classe choisie.')
                        continue
                    valid_student_ids.append(student_id)
            else:
                errors.append('Aucun étudiant absent n\'a été sélectionné.')

            if errors:
                for error in errors:
                    flash(error, 'error')
                students = Etudiant.query.filter_by(classe_id=codClass).order_by(Etudiant.nom.asc(), Etudiant.prenom.asc()).all() if codClass else []
                return render_template(
                    'absence_classe.html',
                    classe=classe,
                    matieres=matieres,
                    selected_mat=selected_mat,
                    selected_date=selected_date,
                    nha=nha_value,
                    students=students,
                    subject_date=parsed_date,
                    subject_hours=nha,
                )

            created = 0
            for student_id in valid_student_ids:
                existing = Absence.query.filter_by(codeMat=selected_mat, nce=student_id, dateA=parsed_date).first()
                if existing is not None:
                    continue
                db.session.add(Absence(codeMat=selected_mat, nce=student_id, dateA=parsed_date, nha=nha))
                created += 1

            if created == 0:
                flash('Aucun enregistrement d\'absence n\'a été créé. Les étudiants sélectionnés sont déjà enregistrés pour cette matière et cette date.', 'warning')
                return redirect(url_for('ClasseRouter.liste_classes'))

            try:
                db.session.commit()
                flash(f'{created} absence(s) enregistrée(s) avec succès.', 'success')
                return redirect(url_for('ClasseRouter.liste_classes'))
            except Exception:
                db.session.rollback()
                flash('Une erreur est survenue lors de l\'enregistrement des absences.', 'error')

    return render_template(
        'absence_classe.html',
        classe=classe,
        matieres=matieres,
        selected_mat=selected_mat,
        selected_date=selected_date,
        nha=nha_value,
        students=students,
    )


@AbsenceRouter.route('/etudiant/<nce>', methods=['GET'])
def absence_etudiant(nce):
    etudiant = Etudiant.query.get(nce)
    if not etudiant:
        abort(404)

    absences = Absence.query.filter_by(nce=nce).order_by(Absence.dateA.desc()).all()
    return render_template('absence_etudiant.html', etudiant=etudiant, absences=absences)
