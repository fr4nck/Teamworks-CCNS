from decimal import Decimal
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
IMPRESSION = ROOT / 'teamworks' / 'Dlg' / 'DLG_Impression_frais.py'
REMBOURSEMENT = ROOT / 'teamworks' / 'Dlg' / 'DLG_Saisie_remboursement.py'


def _function_source(path, name, class_name=None):
    text = path.read_text(encoding='utf-8')
    tree = ast.parse(text)
    if class_name is None:
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
    else:
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
        node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(text, node)


def _print_money_calculator():
    ns = {'Decimal': Decimal}
    helper = _function_source(IMPRESSION, '_montant_decimal')
    exec('CENTIME = Decimal("0.01")\nfrom decimal import ROUND_HALF_UP\n' + helper, ns)
    return ns['_montant_decimal']


def test_impression_uses_decimal_for_money():
    source = IMPRESSION.read_text(encoding='utf-8')
    assert 'montant = float(distance) * float(tarif_km)' not in source
    assert 'montant_total = Decimal("0.00")' in source
    assert source.count('_montant_decimal(distance, tarif_km)') >= 2


def test_print_money_rounding_examples():
    calc = _print_money_calculator()
    assert calc('123', '0.55') == Decimal('67.65')
    assert calc('3', '0.335') == Decimal('1.01')


def test_print_total_adds_cent_rounded_lines_without_binary_residue():
    calc = _print_money_calculator()
    lignes = [calc('3', '0.335'), calc('1', '0.10'), calc('2', '0.20')]
    assert lignes == [Decimal('1.01'), Decimal('0.10'), Decimal('0.40')]
    assert sum(lignes, Decimal('0.00')) == Decimal('1.51')


def test_reimbursement_linkage_uses_decimal():
    source = _function_source(REMBOURSEMENT, 'MajLabelRattachement', 'ListCtrl_deplacements')
    assert 'Decimal("0.00")' in source
    assert 'float(self.GetItem' not in source
    assert '_euros_decimal(self.montantRemboursement)' in source


def test_reimbursement_decimal_normalizes_cents():
    ns = {'Decimal': Decimal}
    helper = _function_source(REMBOURSEMENT, '_euros_decimal')
    exec('CENTIME = Decimal("0.01")\nfrom decimal import ROUND_HALF_UP\n' + helper, ns)
    euros = ns['_euros_decimal']
    assert euros('0.1') + euros('0.2') == Decimal('0.30')
    assert euros('67.65000000000001') == Decimal('67.65')


def test_reimbursement_importation_uses_same_decimal_money_engine():
    source = _function_source(REMBOURSEMENT, 'Importation', 'ListCtrl_deplacements')
    assert 'float(distance) * float(tarif_km)' not in source
    assert '_montant_deplacement_decimal(distance, tarif_km)' in source
    assert 'self.montantRattache = Decimal("0.00")' in source


def test_reimbursement_line_money_rounding_is_deterministic():
    ns = {'Decimal': Decimal}
    helper = _function_source(REMBOURSEMENT, '_montant_deplacement_decimal')
    exec('CENTIME = Decimal("0.01")\nfrom decimal import ROUND_HALF_UP\n' + helper, ns)
    calc = ns['_montant_deplacement_decimal']
    assert calc('3', '0.335') == Decimal('1.01')
    assert calc('123', '0.55') == Decimal('67.65')


def test_no_kilometric_money_path_in_reimbursement_falls_back_to_binary_float():
    source = REMBOURSEMENT.read_text(encoding='utf-8')
    assert 'float(distance) * float(tarif_km)' not in source
