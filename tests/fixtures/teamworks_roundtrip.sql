CREATE TABLE personnes (
    IDpersonne INTEGER PRIMARY KEY AUTOINCREMENT,
    civilite VARCHAR(5), nom VARCHAR(100), nom_jfille VARCHAR(100), prenom VARCHAR(100),
    date_naiss DATE, cp_naiss INTEGER, ville_naiss VARCHAR(100), pays_naiss INTEGER,
    nationalite INTEGER, num_secu VARCHAR(21), adresse_resid VARCHAR(200), cp_resid INTEGER,
    ville_resid VARCHAR(100), memo VARCHAR(800), IDsituation INTEGER,
    cadre_photo VARCHAR(200), texte_photo VARCHAR(300)
);
CREATE TABLE coordonnees (
    IDcoord INTEGER PRIMARY KEY AUTOINCREMENT,
    IDpersonne INTEGER, categorie VARCHAR(100), texte VARCHAR(50), intitule VARCHAR(300)
);
CREATE TABLE valeurs_point (
    IDvaleur_point INTEGER PRIMARY KEY AUTOINCREMENT,
    valeur REAL, date_debut DATE
);
CREATE TABLE contrats (
    IDcontrat INTEGER PRIMARY KEY AUTOINCREMENT,
    IDpersonne INTEGER, IDclassification INTEGER, IDtype INTEGER, valeur_point INTEGER,
    date_debut DATE, date_fin DATE, date_rupture DATE, essai INTEGER,
    signature VARCHAR(3), due VARCHAR(3)
);
CREATE TABLE presences (
    IDpresence INTEGER PRIMARY KEY AUTOINCREMENT,
    IDpersonne INTEGER, date DATE, heure_debut DATE, heure_fin DATE,
    IDcategorie INTEGER, intitule VARCHAR(200)
);

INSERT INTO personnes VALUES
(1, 'Mme', 'D''ÉTÉ', '', 'Élodie', '1990-02-03', 35000, 'Rennes', NULL, 1, NULL,
 '12 rue de l''Été', 30000, 'Nîmes', 'ASCII + accents + 漢字', NULL, '', NULL),
(2, 'M', 'MARTIN', NULL, 'Noé', '1985-11-19', NULL, '', NULL, NULL, '',
 NULL, NULL, 'Brest', '', 2, NULL, 'Texte Unicode Ω');

INSERT INTO coordonnees VALUES
(10, 1, 'email', 'elodie@example.invalid', 'Courriel principal'),
(11, 1, 'téléphone', '', 'Mobile'),
(12, 2, 'note', NULL, 'Coordonnée sans valeur');

INSERT INTO valeurs_point VALUES
(20, 6.37, '2026-01-01'),
(21, 7.125, '2026-07-01');

INSERT INTO contrats VALUES
(30, 1, 4, 2, 20, '2026-01-15', '2026-12-31', NULL, 14, 'oui', ''),
(31, 2, 5, 3, 21, '2026-02-01', NULL, NULL, 0, 'non', NULL);

INSERT INTO presences VALUES
(40, 1, '2026-03-04', '08:30:00', '12:15:00', 7, 'Réunion d''équipe'),
(41, 2, '2026-03-05', '13:00:00', '17:45:30', 8, 'Accueil – été');
