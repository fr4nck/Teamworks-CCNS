#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
import wx
import GestionDB
import FonctionsPerso
import datetime
from Utils import UTILS_Dates


NOMS_EDITION = {
    "personne" : "NOM_PRENOM*1",
    "contrat" : "NOM_PRENOM*1_DATEDEBUT_DATEFIN",
    "candidat" : "NOM_PRENOM*1",
    "candidature" : "NOM_PRENOM*1_DATEDEPOT",
    }


def _format_postal_code(value):
    """Formate un code postal sans masquer les valeurs non numériques."""
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    try:
        return "%05d" % int(text)
    except (TypeError, ValueError):
        return text


def _choice_label(values, index, default=""):
    try:
        index = int(index)
    except (TypeError, ValueError):
        return default
    if 0 <= index < len(values):
        return values[index]
    return default


def _get_country_value(country_id, field):
    if field not in ("nom", "nationalite"):
        raise ValueError("Champ pays non autorisé : %s" % field)
    if country_id in (None, "", 0):
        return ""
    try:
        country_id = int(country_id)
    except (TypeError, ValueError):
        return ""

    DB = GestionDB.DB()
    try:
        DB.ExecuterReq("SELECT %s FROM pays WHERE IDpays=%d;" % (field, country_id))
        rows = DB.ResultatReq()
    finally:
        DB.Close()
    if not rows:
        return ""
    return rows[0][0] or ""


def GetDictDonnees(categorie=None, listeID=None):
    if listeID is None:
        listeID = []
    dict_donnees = {}
    dict_donnees["CATEGORIE"] = categorie
    dict_donnees["NBREDOCUMENTS"] = len(listeID)
    dict_donnees["NOMEDITION"] = NOMS_EDITION[categorie]
    listeMotscles = []

    numDoc = 1
    for ID in listeID :
        listeMotsclesDocument, dictDonneesDocument = GetDonneesDocument(categorie, ID)
        if listeMotsclesDocument:
            listeMotscles = listeMotsclesDocument
        dict_donnees[numDoc] = dictDonneesDocument
        numDoc += 1

    listeMotsclesTemp = []
    for motcle in listeMotscles :
        listeMotsclesTemp.append( (motcle, "base") )
    dict_donnees["MOTSCLES"] = listeMotsclesTemp

    return dict_donnees


def GetDonneesDocument(categorie=None, ID=None):
    """ categorie = candidat, candidature, personne... """
    if categorie == "personne" :
        listeMotscles, dictDonnees = Importation_personne(IDpersonne=ID)
        return listeMotscles, dictDonnees

    if categorie == "contrat" :
        listeMotsclesContrat, dictDonneesContrat = Importation_contrat(IDcontrat=ID)
        if not dictDonneesContrat:
            return [], {}
        IDpersonne = dictDonneesContrat["_IDPERSONNE"]
        listeMotsclesPersonne, dictDonneesPersonne = Importation_personne(IDpersonne=IDpersonne)

        listeMotscles = []
        for motcle in listeMotsclesPersonne :
            if not motcle.startswith("_") :
                listeMotscles.append(motcle)
        for motcle in listeMotsclesContrat :
            if not motcle.startswith("_") :
                listeMotscles.append(motcle)

        dictDonnees = {}
        for motcle, valeur in dictDonneesPersonne.items() :
            if not motcle.startswith("_") :
                dictDonnees[motcle] = valeur
        for motcle, valeur in dictDonneesContrat.items() :
            if not motcle.startswith("_") :
                dictDonnees[motcle] = valeur

        return listeMotscles, dictDonnees

    if categorie == "candidat" :
        listeMotscles, dictDonnees = Importation_candidat(IDcandidat=ID)
        return listeMotscles, dictDonnees

    if categorie == "candidature" :
        listeMotsclesCandidature, dictDonneesCandidature = Importation_candidature(IDcandidature=ID)
        if not dictDonneesCandidature:
            return [], {}
        IDpersonne = dictDonneesCandidature["_IDPERSONNE"]
        IDcandidat = dictDonneesCandidature["_IDCANDIDAT"]
        if IDpersonne == 0 or IDpersonne == None :
            listeMotsclesPersonne, dictDonneesPersonne = Importation_candidat(IDcandidat=IDcandidat)
        else:
            listeMotsclesPersonne, dictDonneesPersonne = Importation_personne(IDpersonne=IDpersonne)

        listeMotscles = []
        for motcle in listeMotsclesPersonne :
            if not motcle.startswith("_") :
                listeMotscles.append(motcle)
        for motcle in listeMotsclesCandidature :
            if not motcle.startswith("_") :
                listeMotscles.append(motcle)

        dictDonnees = {}
        for motcle, valeur in dictDonneesPersonne.items() :
            if not motcle.startswith("_") :
                dictDonnees[motcle] = valeur
        for motcle, valeur in dictDonneesCandidature.items() :
            if not motcle.startswith("_") :
                dictDonnees[motcle] = valeur

        return listeMotscles, dictDonnees


def Importation_candidat(IDcandidat=None):
    dictDonnees = {}

    DB = GestionDB.DB()
    req = """SELECT IDcandidat, civilite, nom, prenom, date_naiss, age, adresse_resid, cp_resid, ville_resid, memo
    FROM candidats WHERE IDcandidat=%d; """ % IDcandidat
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    if len(listeDonnees) == 0 : return [], {}

    IDcandidat, civilite, nom, prenom, date_naiss, age, adresse_resid, cp_resid, ville_resid, memo = listeDonnees[0]

    dictDonnees["_IDCANDIDAT"] = IDcandidat
    dictDonnees["CIVILITE"] = civilite
    dictDonnees["NOM"] = nom
    dictDonnees["PRENOM"] = prenom
    dictDonnees["ADRESSERESID"] = adresse_resid
    dictDonnees["VILLERESID"] = ville_resid
    dictDonnees["MEMO"] = memo
    dictDonnees["CPRESID"] = _format_postal_code(cp_resid)

    dictDonnees["DATENAISS"] = ""
    temp = date_naiss
    if temp == "  /  /    " or temp == '' or temp == None:
        temp = ""
    else:
        temp = FonctionsPerso.DateEngFr(temp)
    dictDonnees["DATENAISS"] = temp

    dictDonnees["AGE"] = ""
    if age != "" and age != None and age != 0 :
        dictDonnees["AGE"] = str(age)
    else:
        if dictDonnees["DATENAISS"] != "" :
            datenaissanceTmp = dictDonnees["DATENAISS"]
            jour = int(datenaissanceTmp[:2])
            mois = int(datenaissanceTmp[3:5])
            annee = int(datenaissanceTmp[6:10])
            bday = datetime.date(annee, mois, jour)
            datedujour = datetime.date.today()
            age = (datedujour.year - bday.year) - int((datedujour.month, datedujour.day) < (bday.month, bday.day))
            dictDonnees["AGE"] = str(age)

    dictDonnees["QUALIFICATIONS"] = ""
    DB = GestionDB.DB()
    req = """
    SELECT types_diplomes.nom_diplome, types_diplomes.IDtype_diplome
    FROM types_diplomes LEFT JOIN diplomes_candidats ON types_diplomes.IDtype_diplome = diplomes_candidats.IDtype_diplome
    WHERE diplomes_candidats.IDcandidat=%d
    """ % IDcandidat
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    if len(listeDonnees) > 0 :
        texteTemp = ""
        for nom_diplome, IDtype_diplome in listeDonnees :
            texteTemp += nom_diplome + "; "
        dictDonnees["QUALIFICATIONS"] = texteTemp[:-2]

    dictDonnees["TELEPHONES"] = ""
    dictDonnees["FAX"] = ""
    dictDonnees["EMAILS"] = ""
    DB = GestionDB.DB()
    req = """SELECT IDcoord, categorie, texte, intitule
    FROM coords_candidats
    WHERE IDcandidat=%d; """ % IDcandidat
    DB.ExecuterReq(req)
    listeCoords = DB.ResultatReq()
    DB.Close()
    texteTel = ""
    texteFax = ""
    texteEmails = ""
    nbreTel = 0
    nbreFax = 0
    nbreEmails = 0
    if len(listeCoords) > 0 :
        for IDcoord, categorie, texte, intitule in listeCoords :
            if categorie == "Fixe" or categorie == "Mobile" :
                texteTel += texte + ", "
                nbreTel += 1
            if categorie == "Email" :
                texteEmails += texte + ", "
                nbreEmails += 1
            if categorie == "Fax" :
                texteFax += texte + ", "
                nbreFax += 1
        if nbreTel > 0 : dictDonnees["TELEPHONES"] = texteTel[:-2]
        if nbreEmails > 0 : dictDonnees["EMAILS"] = texteEmails[:-2]
        if nbreFax > 0 : dictDonnees["FAX"] = texteFax[:-2]

    listeMotscles = [ "CIVILITE", "NOM", "PRENOM", "DATENAISS", "AGE", "ADRESSERESID", "CPRESID", "VILLERESID", "QUALIFICATIONS", "TELEPHONES", "FAX", "EMAILS", "MEMO"]

    return listeMotscles, dictDonnees


def Importation_candidature(IDcandidature=None):
    dictDonnees = {}

    DB = GestionDB.DB()
    req = """SELECT IDcandidat, IDpersonne, date_depot, IDtype, acte_remarques, IDemploi, periodes_remarques, poste_remarques,
    IDdecision, decision_remarques, reponse_obligatoire, reponse, date_reponse, IDtype_reponse
    FROM candidatures WHERE IDcandidature=%d; """ % IDcandidature
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    if len(listeDonnees) == 0 : return [], {}
    IDcandidat, IDpersonne, date_depot, IDtype, acte_remarques, IDemploi, periodes_remarques, poste_remarques, IDdecision, decision_remarques, reponse_obligatoire, reponse, date_reponse, IDtype_reponse = listeDonnees[0]

    dictDonnees["_IDCANDIDAT"] = IDcandidat
    dictDonnees["_IDPERSONNE"] = IDpersonne
    dictDonnees["DATEDEPOT"] = FonctionsPerso.DateEngFr(date_depot)

    listeTypes = [_(u"De vive voix"), _(u"Courrier"), _(u"Téléphone"), _(u"Main à main"), _(u"Email"), _(u"Pôle Emploi"), _(u"Organisateur"), _(u"Fédération"), _(u"Autre")]
    dictDonnees["TYPEDEPOT"] = _choice_label(listeTypes, IDtype)

    dictDonnees["OFFREDEMPLOI"] = ""
    if IDemploi in (0, None, "") :
        dictDonnees["OFFREDEMPLOI"] = _(u"Candidature spontanée")
    else:
        listeMotsclesEmmplois, dictDonneesEmplois = Importation_offre_emploi(IDemploi=IDemploi)
        dictDonnees["OFFREDEMPLOI"] = dictDonneesEmplois.get("OFFRE_INTITULE", "")

    dictDonnees["DISPONIBILITES"] = ""
    DB = GestionDB.DB()
    req = """SELECT IDdisponibilite, date_debut, date_fin
    FROM disponibilites WHERE IDcandidature=%d ORDER BY date_debut; """ % IDcandidature
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    if len(listeDonnees) > 0 :
        texteTemp = ""
        for IDdisponibilite, date_debut, date_fin in listeDonnees :
            texteTemp += _(u"du %s au %s") % (FonctionsPerso.DateEngFr(date_debut), FonctionsPerso.DateEngFr(date_fin)) + "; "
        dictDonnees["DISPONIBILITES"] = texteTemp[:-2]

    dictDonnees["FONCTIONS"] = ""
    DB = GestionDB.DB()
    req = """
    SELECT fonctions.IDfonction, fonctions.fonction
    FROM fonctions LEFT JOIN cand_fonctions ON fonctions.IDfonction = cand_fonctions.IDfonction
    WHERE cand_fonctions.IDcandidature=%d
    """ % IDcandidature
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    if len(listeDonnees) > 0 :
        texteTemp = ""
        for IDfonction, nomFonction in listeDonnees :
            texteTemp += nomFonction + "; "
        dictDonnees["FONCTIONS"] = texteTemp[:-2]

    dictDonnees["AFFECTATIONS"] = ""
    DB = GestionDB.DB()
    req = """
    SELECT affectations.IDaffectation, affectations.affectation
    FROM affectations LEFT JOIN cand_affectations ON affectations.IDaffectation = cand_affectations.IDaffectation
    WHERE cand_affectations.IDcandidature=%d
    """ % IDcandidature
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    if len(listeDonnees) > 0 :
        texteTemp = ""
        for IDfonction, nomAffectation in listeDonnees :
            texteTemp += nomAffectation + "; "
        dictDonnees["AFFECTATIONS"] = texteTemp[:-2]

    typesDecision = [_(u"Décision non prise"), _(u"Oui"), _(u"Non")]
    dictDonnees["DECISION"] = _choice_label(typesDecision, IDdecision)

    listeTypesReponses = [_(u"De vive voix"), _(u"Courrier"), _(u"Téléphone"), _(u"Main à main"), _(u"Email"), _(u"Autre")]
    dictDonnees["DATEREPONSE"] = ""
    dictDonnees["TYPEREPONSE"] = ""
    if reponse == 1 :
        if date_reponse not in (None, ""):
            dictDonnees["DATEREPONSE"] = FonctionsPerso.DateEngFr(date_reponse)
        dictDonnees["TYPEREPONSE"] = _choice_label(listeTypesReponses, IDtype_reponse)

    listeMotscles = [ "DATEDEPOT", "TYPEDEPOT", "OFFREDEMPLOI", "DISPONIBILITES", "FONCTIONS", "AFFECTATIONS", "DECISION", "DATEREPONSE", "TYPEREPONSE"]
    return listeMotscles, dictDonnees


def Importation_offre_emploi(IDemploi=None):
    dictDonnees = {}
    dictDonnees["OFFREDEMPLOI"] = ""
    DB = GestionDB.DB()
    req = """
    SELECT IDemploi, date_debut, date_fin, intitule, detail, reference_anpe
    FROM emplois
    WHERE IDemploi=%d
    """ % IDemploi
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    if len(listeDonnees) == 0 : return [], {}
    IDemploi, date_debut, date_fin, intitule, detail, reference_anpe = listeDonnees[0]

    dictDonnees["OFFRE_DATEDEBUT"] = date_debut
    dictDonnees["OFFRE_DATEFIN"] = date_fin
    dictDonnees["OFFRE_INTITULE"] = intitule
    dictDonnees["OFFRE_DETAIL"] = detail
    dictDonnees["OFFRE_REFERENCE_ANPE"] = reference_anpe

    listeMotscles = [ "OFFRE_INTITULE", "OFFRE_DETAIL", "OFFRE_DATEDEBUT", "OFFRE_DATEFIN", "OFFRE_REFERENCE_ANPE"]
    return listeMotscles, dictDonnees


def Importation_personne(IDpersonne=None):
    dictDonnees = {}

    DB = GestionDB.DB()
    req = """
    SELECT civilite, nom, nom_jfille, prenom, date_naiss, cp_naiss, ville_naiss, nationalite, num_secu, adresse_resid, cp_resid, ville_resid, IDsituation, pays_naiss
    FROM personnes WHERE IDpersonne=%d;
    """ % IDpersonne
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    if len(listeDonnees) == 0 : return [], {}

    civilite, nom, nom_jfille, prenom, date_naiss, cp_naiss, ville_naiss, nationalite, num_secu, adresse_resid, cp_resid, ville_resid, IDsituation, pays_naiss = listeDonnees[0]

    dictDonnees["CIVILITE"] = civilite
    dictDonnees["NOM"] = nom
    dictDonnees["NOMJFILLE"] = nom_jfille
    dictDonnees["PRENOM"] = prenom

    dictDonnees["DATENAISS"] = ""
    if date_naiss not in ("", None) : dictDonnees["DATENAISS"] = UTILS_Dates.DateEngFr(date_naiss)

    dictDonnees["AGE"] = ""
    if dictDonnees["DATENAISS"] != "" :
        datenaissanceTmp = dictDonnees["DATENAISS"]
        jour = int(datenaissanceTmp[:2])
        mois = int(datenaissanceTmp[3:5])
        annee = int(datenaissanceTmp[6:10])
        bday = datetime.date(annee, mois, jour)
        datedujour = datetime.date.today()
        age = (datedujour.year - bday.year) - int((datedujour.month, datedujour.day) < (bday.month, bday.day))
        dictDonnees["AGE"] = str(age)

    dictDonnees["CPNAISS"] = _format_postal_code(cp_naiss)
    dictDonnees["VILLENAISS"] = ville_naiss
    dictDonnees["NATIONALITE"] = _get_country_value(nationalite, "nationalite")
    dictDonnees["PAYSNAISS"] = _get_country_value(pays_naiss, "nom")
    dictDonnees["NUMSECU"] = num_secu
    dictDonnees["ADRESSERESID"] = adresse_resid
    dictDonnees["CPRESID"] = _format_postal_code(cp_resid)
    dictDonnees["VILLERESID"] = ville_resid

    dictDonnees["SITUATION"] = ""
    DB = GestionDB.DB()
    req = """
    SELECT situation
    FROM situations WHERE IDsituation=%d;
    """ % IDsituation
    DB.ExecuterReq(req)
    listeSituations = DB.ResultatReq()
    DB.Close()
    if len(listeSituations) > 0 :
        dictDonnees["SITUATION"] = listeSituations[0][0]

    dictDonnees["TELEPHONES"] = ""
    dictDonnees["FAX"] = ""
    dictDonnees["EMAILS"] = ""
    DB = GestionDB.DB()
    req = """SELECT IDcoord, categorie, texte, intitule
    FROM coordonnees
    WHERE IDpersonne=%d; """ % IDpersonne
    DB.ExecuterReq(req)
    listeCoords = DB.ResultatReq()
    DB.Close()
    texteTel = ""
    texteFax = ""
    texteEmails = ""
    nbreTel = 0
    nbreFax = 0
    nbreEmails = 0
    if len(listeCoords) > 0 :
        for IDcoord, categorie, texte, intitule in listeCoords :
            if categorie == "Fixe" or categorie == "Mobile" :
                texteTel += texte + ", "
                nbreTel += 1
            if categorie == "Email" :
                texteEmails += texte + ", "
                nbreEmails += 1
            if categorie == "Fax" :
                texteFax += texte + ", "
                nbreFax += 1
        if nbreTel > 0 : dictDonnees["TELEPHONES"] = texteTel[:-2]
        if nbreEmails > 0 : dictDonnees["EMAILS"] = texteEmails[:-2]
        if nbreFax > 0 : dictDonnees["FAX"] = texteFax[:-2]

    listeMotscles = [ "CIVILITE", "NOM", "NOMJFILLE", "PRENOM", "DATENAISS", "AGE", "CPNAISS", "VILLENAISS",
    "PAYSNAISS", "NATIONALITE", "NUMSECU", "ADRESSERESID", "CPRESID", "VILLERESID", "SITUATION", "TELEPHONES", "EMAILS", "FAX"]

    return listeMotscles, dictDonnees


def Importation_contrat(IDcontrat=None):
    """Importe un contrat historique ou TW-184 pour le publipostage.

    Les anciens mots-clés restent disponibles. Les nouveaux contrats ne sont
    plus obligés d'avoir une classification historique ni une valeur du point.
    """
    from decimal import Decimal
    from Utils import UTILS_Contrats_schema, UTILS_CEE_baremes
    from application.control.ccns_contract_compliance import CCNSContractCompliancePresenter
    from domain.contracts.cee_compensation import legal_cee_daily_minimum
    from domain.convention.smic import SmicTerritory, create_smic_catalog_2026

    dictDonnees = {}
    DB = GestionDB.DB()
    UTILS_Contrats_schema.EnsureContractEngineColumns(DB)
    req = """
    SELECT IDpersonne, IDclassification, IDtype, valeur_point, date_debut, date_fin, essai,
           cee_qualification, convention_code, ccns_group, weekly_hours, gross_monthly_salary
    FROM contrats WHERE IDcontrat=%d;
    """ % IDcontrat
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    if len(listeDonnees) == 0 :
        DB.Close()
        return [], {}

    (IDpersonne, IDclassification, IDtype, valeur_point, date_debut, date_fin, essai,
     cee_qualification, convention_code, ccns_group, weekly_hours, gross_monthly_salary) = listeDonnees[0]

    dictDonnees["_IDPERSONNE"] = IDpersonne
    dictDonnees["DATEDEBUT"] = FonctionsPerso.DateEngFr(date_debut) if date_debut else ""
    dictDonnees["DATEFIN"] = FonctionsPerso.DateEngFr(date_fin) if date_fin else ""
    dictDonnees["ESSAI"] = str(essai or 0)

    dictDonnees["CLASSIFICATION"] = ""
    if IDclassification not in (None, ""):
        DB.ExecuterReq("SELECT nom FROM contrats_class WHERE IDclassification=%d;" % int(IDclassification))
        rows = DB.ResultatReq()
        if rows:
            dictDonnees["CLASSIFICATION"] = rows[0][0]

    dictDonnees["TYPECONTRAT"] = ""
    type_abrege = ""
    if IDtype not in (None, ""):
        DB.ExecuterReq("SELECT nom, nom_abrege, duree_indeterminee FROM contrats_types WHERE IDtype=%d;" % int(IDtype))
        rows = DB.ResultatReq()
        if rows:
            dictDonnees["TYPECONTRAT"] = rows[0][0]
            type_abrege = (rows[0][1] or "").strip().upper()

    dictDonnees["VALEURPOINT"] = ""
    if valeur_point not in (None, ""):
        DB.ExecuterReq("SELECT valeur, date_debut FROM valeurs_point WHERE IDvaleur_point=%d;" % int(valeur_point))
        rows = DB.ResultatReq()
        if rows:
            dictDonnees["VALEURPOINT"] = u"%s €" % rows[0][0]

    qualification_labels = {
        "BAFA_HOLDER": u"BAFA titulaire",
        "BAFA_TRAINEE": u"BAFA stagiaire",
        "UNQUALIFIED": u"Non diplômé",
        "EQUIVALENT": u"Qualification équivalente",
        "BAFD_HOLDER": u"BAFD titulaire",
        "BAFD_TRAINEE": u"BAFD stagiaire",
    }
    dictDonnees["CONVENTION"] = convention_code or ""
    dictDonnees["GROUPECCNS"] = ccns_group or ""
    dictDonnees["QUALIFICATIONCEE"] = qualification_labels.get(cee_qualification, cee_qualification or "")
    dictDonnees["DUREEHEBDO"] = ""
    if weekly_hours not in (None, ""):
        dictDonnees["DUREEHEBDO"] = u"%s h" % ("%.2f" % float(weekly_hours)).rstrip("0").rstrip(".")
    dictDonnees["SALAIREBRUTMENSUEL"] = ""
    if gross_monthly_salary not in (None, ""):
        dictDonnees["SALAIREBRUTMENSUEL"] = u"%.2f €" % float(gross_monthly_salary)

    dictDonnees["MINIMUMCCNS"] = ""
    dictDonnees["MINIMUMSMIC"] = ""
    dictDonnees["MINIMUMRETENU"] = ""
    dictDonnees["CONFORMITEREMUNERATION"] = ""
    dictDonnees["BAREMECEE"] = ""
    dictDonnees["MINIMUMCEE"] = ""

    reference_date = UTILS_Dates.DateEnDateDD(date_debut)
    is_cee = type_abrege == "CEE" or "engagement educatif" in dictDonnees["TYPECONTRAT"].lower() or "engagement éducatif" in dictDonnees["TYPECONTRAT"].lower()

    if reference_date is not None and is_cee and cee_qualification:
        applicable = UTILS_CEE_baremes.GetApplicableRate(DB, cee_qualification, reference_date)
        legal_minimum = legal_cee_daily_minimum(
            smic_catalog=create_smic_catalog_2026(),
            reference_date=reference_date,
            territory=SmicTerritory.METROPOLITAN_FRANCE,
        )
        dictDonnees["MINIMUMCEE"] = u"%.2f €" % legal_minimum
        if applicable is not None:
            rate = Decimal(str(applicable["montant_journalier"]))
            dictDonnees["BAREMECEE"] = u"%.2f €" % rate
            dictDonnees["CONFORMITEREMUNERATION"] = u"Conforme" if rate >= legal_minimum else u"Non conforme"

    if reference_date is not None and convention_code == "CCNS" and ccns_group:
        presenter = CCNSContractCompliancePresenter()
        choices = presenter.group_choices(reference_date)
        choice = next((item for item in choices if item.code == str(ccns_group).strip().upper()), None)
        if choice is not None:
            dictDonnees["MINIMUMCCNS"] = u"%.2f €" % choice.minimum_amount
            if choice.periodicity.value == "annual":
                dictDonnees["MINIMUMRETENU"] = u"%.2f € annuel" % choice.minimum_amount
                dictDonnees["CONFORMITEREMUNERATION"] = u"Contrôle annuel requis"
            elif weekly_hours not in (None, "") and gross_monthly_salary not in (None, ""):
                preview = presenter.evaluate_monthly(
                    group_code=choice.code,
                    reference_date=reference_date,
                    weekly_hours=Decimal(str(weekly_hours)),
                    remuneration_amount=Decimal(str(gross_monthly_salary)),
                )
                dictDonnees["MINIMUMCCNS"] = u"%.2f €" % preview.ccns_minimum_amount
                dictDonnees["MINIMUMSMIC"] = u"%.2f €" % preview.smic_minimum_amount
                dictDonnees["MINIMUMRETENU"] = u"%.2f €" % preview.required_minimum_amount
                dictDonnees["CONFORMITEREMUNERATION"] = u"Conforme" if preview.compliant else u"Non conforme"

    listeMotscles = [
        "DATEDEBUT", "DATEFIN", "CLASSIFICATION", "TYPECONTRAT", "VALEURPOINT", "ESSAI",
        "CONVENTION", "GROUPECCNS", "QUALIFICATIONCEE", "DUREEHEBDO", "SALAIREBRUTMENSUEL",
        "MINIMUMCCNS", "MINIMUMSMIC", "MINIMUMRETENU", "CONFORMITEREMUNERATION",
        "BAREMECEE", "MINIMUMCEE",
    ]

    DB.ExecuterReq("SELECT IDchamp, mot_cle FROM contrats_champs;")
    listeChamps = DB.ResultatReq()
    dictChamps = {}
    for IDchamp, mot_cle in listeChamps :
        if not isinstance(mot_cle, str):
            continue
        mot_cle = mot_cle.strip()
        if not mot_cle:
            continue
        dictChamps[IDchamp] = mot_cle
        listeMotscles.append(mot_cle)

    DB.ExecuterReq("SELECT IDchamp, valeur FROM contrats_valchamps WHERE IDcontrat=%d AND type='contrat';" % IDcontrat)
    listeChamps = DB.ResultatReq()
    for IDchamp, valeur in listeChamps :
        mot_cle = dictChamps.get(IDchamp)
        if mot_cle:
            dictDonnees[mot_cle] = valeur

    DB.Close()
    return listeMotscles, dictDonnees


if __name__ == "__main__":
    print(GetDictDonnees(categorie="candidat", listeID=[2, 5]))
