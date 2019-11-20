from server import db
from Models.Contact import Contact
from Models.Domaine import Domaine
from Models.Emploi import Emploi
from Models.Entreprise import Entreprise
from Models.Etudiant import Etudiant
from Models.Formation import Formation
from Models.Stage import Stage
from errors import ERRORS


def check_primary_ent(id_entreprise: int):
    ent: Entreprise = Entreprise.query.filter_by(id_entreprise=id_entreprise).one_or_none()

    if not ent:
        return ERRORS.BAD_REQUEST


def check_primary_cont(id_contact: int):
    cont: Contact = Contact.query.filter_by(id_contact=id_contact).one_or_none()

    if not cont:
        return ERRORS.BAD_REQUEST

def check_primary_dom(id_domaine: int):
    dom: Domaine = Domaine.query.filter_by(id_domaine=id_domaine).one_or_none()

    if not dom:
        return ERRORS.BAD_REQUEST
    
def check_primary_form(id_formation: int):
    form: Formation = Formation.query.filter_by(id_formation=id_formation).one_or_none()

    if not form:
        return ERRORS.BAD_REQUEST