#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import datetime
import time
import six


def DateEnDateDD(value, default=None):
    """Normalise une date hétérogène en ``datetime.date`` sans lever d'exception.

    Formats historiques acceptés : objets date/datetime, ISO ``AAAA-MM-JJ``
    (mois/jour sur un ou deux chiffres), ``JJ/MM/AAAA`` et ``JJ-MM-AAAA``.
    Les valeurs absentes ou invalides retournent ``default``.
    """
    if value in (None, ""):
        return default
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value

    text = six.text_type(value).strip()
    if not text:
        return default
    if "T" in text:
        text = text.split("T", 1)[0]
    elif " " in text:
        text = text.split(" ", 1)[0]

    for separator, order in (("-", "ymd"), ("/", "dmy"), ("-", "dmy")):
        parts = text.split(separator)
        if len(parts) != 3:
            continue
        try:
            if order == "ymd" and len(parts[0]) == 4:
                year, month, day = (int(part) for part in parts)
            elif order == "dmy" and len(parts[2]) == 4:
                day, month, year = (int(part) for part in parts)
            else:
                continue
            return datetime.date(year, month, day)
        except (TypeError, ValueError):
            continue
    return default


def DateEngFr(textDate):
    date_dd = DateEnDateDD(textDate)
    if date_dd is None:
        return ""
    return "%02d/%02d/%04d" % (date_dd.day, date_dd.month, date_dd.year)


def DateDDEnFr(date):
    return DateEngFr(date)


def DateFrEng(textDate):
    date_dd = DateEnDateDD(textDate)
    if date_dd is None:
        return ""
    return "%04d-%02d-%02d" % (date_dd.year, date_dd.month, date_dd.day)


def DateComplete(dateDD):
    """Transforme une date en date complète : ex. lundi 15 janvier 2008."""
    dateDD = DateEnDateDD(dateDD)
    if dateDD is None:
        return u""
    listeJours = (_(_(u"Lundi")), _(_(u"Mardi")), _(_(u"Mercredi")), _(_(u"Jeudi")), _(_(u"Vendredi")), _(_(u"Samedi")), _(_(u"Dimanche")))
    listeMois = (_(_(u"janvier")), _(_(u"février")), _(_(u"mars")), _(_(u"avril")), _(_(u"mai")), _(_(u"juin")), _(_(u"juillet")), _(_(u"août")), _(_(u"septembre")), _(_(u"octobre")), _(_(u"novembre")), _(_(u"décembre")))
    return listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month - 1] + " " + str(dateDD.year)


def DateEngEnDateDD(dateEng):
    return DateEnDateDD(dateEng)


def PeriodeComplete(mois, annee):
    listeMois = (_(_(u"Janvier")), _(_(u"Février")), _(_(u"Mars")), _(_(u"Avril")), _(_(u"Mai")), _(_(u"Juin")), _(_(u"Juillet")), _(_(u"Août")), _(_(u"Septembre")), _(_(u"Octobre")), _(_(u"Novembre")), _(_(u"Décembre")))
    periodeComplete = u"%s %d" % (listeMois[mois-1], annee)
    return periodeComplete

def CalculeAge(dateReference=None, date_naiss=None):
    """ Calcul de l'age de la personne """
    if dateReference == None :
        dateReference = datetime.date.today()
    if date_naiss in (None, "") :
        return None
    age = (dateReference.year - date_naiss.year) - int((dateReference.month, dateReference.day) < (date_naiss.month, date_naiss.day))
    return age

def HeuresEnDecimal(texteHeure="07:00"):
    """ Transforme une heure string ou datetime.time en entier de type 2075"""
    if texteHeure == None :
        return 0
    if type(texteHeure) == datetime.time :
        heures = str(texteHeure.hour)
        minutes = int(texteHeure.minute)
    if type(texteHeure) in (str, six.text_type) :
        posTemp = texteHeure.index(":")
        heures = str(texteHeure[0:posTemp])
        minutes = int(texteHeure[posTemp+1:5])
    minutes = str(minutes * 100 //60)
    if len(minutes) == 1 : minutes = "0" + minutes
    heure = str(heures + minutes)
    return int(heure)

def SoustractionHeures(heure_max, heure_min):
    """ Effectue l'opération heure_max - heure_min. Renvoi un timedelta """
    if type(heure_max) != datetime.timedelta : heure_max = datetime.timedelta(hours=heure_max.hour, minutes=heure_max.minute)
    if type(heure_min) != datetime.timedelta : heure_min =  datetime.timedelta(hours=heure_min.hour, minutes=heure_min.minute)
    return heure_max - heure_min

def AdditionHeures(heure1, heure2):
    """ Effectue l'opération heure_max - heure_min. Renvoi un timedelta """
    if type(heure1) != datetime.timedelta : heure1 = datetime.timedelta(hours=heure1.hour, minutes=heure1.minute)
    if type(heure2) != datetime.timedelta : heure2 =  datetime.timedelta(hours=heure2.hour, minutes=heure2.minute)
    return heure1 + heure2

def DeltaEnTime(varTimedelta) :
    """ Transforme une variable TIMEDELTA en heure datetime.time """
    heureStr = time.strftime("%H:%M", time.gmtime(varTimedelta.seconds))
    heure = HeureStrEnTime(heureStr)
    return heure

def TimeEnDelta(heureTime):
    hr = heureTime.hour
    mn = heureTime.minute
    return datetime.timedelta(hours=hr, minutes=mn)

def HeureStrEnTime(heureStr):
    if heureStr == None or heureStr == "" : return datetime.time(0, 0)
    if len(heureStr.split(":")) == 2 : heures, minutes = heureStr.split(":")
    if len(heureStr.split(":")) == 3 : heures, minutes, secondes = heureStr.split(":")
    return datetime.time(int(heures), int(minutes))

def DatetimeTimeEnStr(heure, separateur="h"):
    if heure == None : 
        return None
    else :
        return u"%02d%s%02d" % (heure.hour, separateur, heure.minute)

def HorodatageEnDatetime(horodatage, separation=None):
    if separation == None :
        annee = int(horodatage[0:4])
        mois = int(horodatage[4:6])
        jour = int(horodatage[6:8])
        heures = int(horodatage[8:10])
        minutes = int(horodatage[10:12])
        secondes = int(horodatage[12:14])
        horodatage = datetime.datetime(annee, mois, jour, heures, minutes, secondes)
    else :
        annee, mois, jour, heures, minutes, secondes = horodatage.split(separation)
        horodatage = datetime.datetime(int(annee), int(mois), int(jour), int(heures), int(minutes), int(secondes))
    return horodatage



if __name__ == "__main__":
    pass

    