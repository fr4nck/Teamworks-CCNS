"""A saved action remains saved when refreshing its UI projection fails."""
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize('filename', ['DLG_Demarches_rh.py', 'DLG_Demarches_rh_pieces.py'])
def test_saved_refresh_failure_is_truthful_and_blocks_stale_actions(filename):
    path=Path('teamworks/Dlg')/filename
    tree=ast.parse(path.read_text(encoding='utf-8'))
    dialog=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='Dialog')
    method=next(node for node in dialog.body if isinstance(node,ast.FunctionDef) and node.name=='_refresh_after_saved')
    notifications=[]
    namespace={'_':lambda text:text,'UTILS_Interface':SimpleNamespace(GetToken=lambda key:key),'wx':SimpleNamespace(OK=1,ICON_WARNING=2,MessageBox=lambda text,*args:notifications.append(text))}
    exec(compile(ast.Module(body=[method],type_ignores=[]),str(path),'exec'),namespace)
    state={'rows':0,'button':True,'feedback':''}
    def fail(**kwargs): raise RuntimeError('projection unavailable after commit')
    def update(): state['rows']=len(owner._rows)
    owner=SimpleNamespace(RefreshData=fail,_rows=[object()],list=SimpleNamespace(DeleteAllItems=lambda:None),new_case=SimpleNamespace(Enable=lambda value:state.update(button=value)),_update_action_state=update,feedback=SimpleNamespace(SetForegroundColour=lambda colour:None,SetLabel=lambda text:state.update(feedback=text)),Layout=lambda:None)
    assert namespace['_refresh_after_saved'](owner,'identifier') is False
    assert owner._rows==[] and state['rows']==0
    assert 'Action enregistrée' in state['feedback']
    assert len(notifications)==1 and 'a été enregistrée' in notifications[0]
    assert 'pas été enregistrée' not in notifications[0]
    if filename=='DLG_Demarches_rh.py': assert state['button'] is False
