-- SORTIE-003 : garde-fous en base des tables en ajout seul (après termination_v2.sql).
--
-- Déclencheurs à instruction unique (SIGNAL, MySQL 5.5+ / MariaDB), sans
-- DELIMITER. Sur un serveur dont le binlog est actif, CREATE TRIGGER exige le
-- privilège SUPER (ou log_bin_trust_function_creators = 1) : ce fichier est
-- donc séparé pour être appliqué par un compte d'administration. Sans lui,
-- l'application ne modifie toujours aucun snapshot et vérifie le hash de
-- chaque snapshot relu ; il ajoute la défense contre les écritures directes.

CREATE TRIGGER trg_tw_termination_snapshot_no_update BEFORE UPDATE ON tw_termination_transmission_snapshot
    FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'tw_termination_transmission_snapshot is append-only';

CREATE TRIGGER trg_tw_termination_snapshot_no_delete BEFORE DELETE ON tw_termination_transmission_snapshot
    FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'tw_termination_transmission_snapshot is append-only';

CREATE TRIGGER trg_tw_termination_command_no_update BEFORE UPDATE ON tw_termination_command
    FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'tw_termination_command is append-only';

CREATE TRIGGER trg_tw_termination_command_no_delete BEFORE DELETE ON tw_termination_command
    FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'tw_termination_command is append-only'
