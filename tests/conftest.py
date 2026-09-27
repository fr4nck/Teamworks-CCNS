"""Infrastructure de test commune DPAE."""
from __future__ import annotations
import os,subprocess,time
from pathlib import Path
import pytest
_CONTAINER="teamworks-dpae-mariadb-ci"; _IMAGE="mariadb:10.11.14"; _CI_ENV={"DPAE_MYSQL_HOST":"127.0.0.1","DPAE_MYSQL_PORT":"33306","DPAE_MYSQL_USER":"teamworks","DPAE_MYSQL_PASSWORD":"teamworks-ci-only","DPAE_MYSQL_DATABASE":"teamworks_dpae_ci"}; _started=False

def _run(*args:str,check:bool=True)->subprocess.CompletedProcess: return subprocess.run(args,check=check,text=True,capture_output=True)
def _connect():
 import mysql.connector; return mysql.connector.connect(host=os.environ["DPAE_MYSQL_HOST"],port=int(os.environ["DPAE_MYSQL_PORT"]),user=os.environ["DPAE_MYSQL_USER"],password=os.environ["DPAE_MYSQL_PASSWORD"],database=os.environ["DPAE_MYSQL_DATABASE"],use_pure=True,autocommit=False)
def _wait_ready(timeout:float=60.0)->None:
 deadline=time.monotonic()+timeout
 while time.monotonic()<deadline:
  if _run("docker","exec",_CONTAINER,"mariadb-admin","ping","-h","127.0.0.1","-uteamworks","-pteamworks-ci-only","--silent",check=False).returncode==0:return
  time.sleep(1)
 logs=_run("docker","logs",_CONTAINER,check=False); raise RuntimeError("MariaDB DPAE CI non prêt:\n"+logs.stdout+logs.stderr)
def _apply_schema()->None:
 conn=_connect()
 try:
  cur=conn.cursor(); sql=Path("infrastructure/persistence/sql/mysql/dpae_v1.sql").read_text(encoding="utf-8")
  for statement in sql.split(";"):
   statement=statement.strip()
   if statement: cur.execute(statement)
  conn.commit(); cur.close()
 finally: conn.close()
def pytest_configure(config)->None:
 # Les variables doivent exister avant l'import des modules DPAE, dont certains
 # décident au niveau module s'ils peuvent être collectés. Le conteneur, lui,
 # est démarré paresseusement par clean_tables uniquement lorsqu'un test SQL
 # DPAE en dépend réellement.
 if os.getenv("GITHUB_ACTIONS")!="true": return
 for key,value in _CI_ENV.items(): os.environ[key]=value
def _ensure_ci_database()->None:
 global _started
 if _started or os.getenv("GITHUB_ACTIONS")!="true": return
 _run("docker","rm","-f",_CONTAINER,check=False)
 try:
  _run("docker","run","-d","--name",_CONTAINER,"-p","33306:3306","-e","MARIADB_ROOT_PASSWORD=root-ci-only","-e","MARIADB_DATABASE=teamworks_dpae_ci","-e","MARIADB_USER=teamworks","-e","MARIADB_PASSWORD=teamworks-ci-only","--health-cmd=healthcheck.sh --connect --innodb_initialized","--health-interval=2s","--health-timeout=3s","--health-retries=30",_IMAGE)
 except subprocess.CalledProcessError as exc:
  raise RuntimeError("Impossible de démarrer MariaDB DPAE CI:\n"+(exc.stdout or "")+(exc.stderr or "")) from exc
 _started=True; _wait_ready(); _apply_schema()
@pytest.fixture
def clean_tables():
 _ensure_ci_database()
 if not all(os.getenv(k) for k in ("DPAE_MYSQL_HOST","DPAE_MYSQL_USER","DPAE_MYSQL_DATABASE")): pytest.skip("base MySQL DPAE non configurée")
 conn=_connect()
 try:
  cur=conn.cursor(); cur.execute("SET FOREIGN_KEY_CHECKS=0")
  for table in ("tw_dpae_return_effect","tw_dpae_current_correlation","tw_dpae_correlation_decision","tw_dpae_return","tw_dpae_case_submission_lock","tw_dpae_submission","tw_dpae_command_audit","tw_dpae_case_event","tw_dpae_snapshot","tw_dpae_case"): cur.execute("DELETE FROM "+table)
  cur.execute("SET FOREIGN_KEY_CHECKS=1"); conn.commit(); cur.close()
 finally: conn.close()
def _write_innodb_diagnostics()->None:
 out=Path("mariadb-dpae-diagnostics.txt"); parts=[]
 try:
  conn=_connect(); cur=conn.cursor()
  try:
   for label,sql in (("INNODB STATUS","SHOW ENGINE INNODB STATUS"),("PROCESSLIST","SHOW FULL PROCESSLIST")):
    parts.append("===== "+label+" ====="); cur.execute(sql)
    for row in cur.fetchall(): parts.append("\t".join("" if value is None else str(value) for value in row))
  finally: cur.close(); conn.close()
 except Exception as exc: parts.append("Diagnostic SQL indisponible: "+repr(exc))
 logs=_run("docker","logs",_CONTAINER,check=False); parts.extend(("===== DOCKER LOGS =====",logs.stdout,logs.stderr)); out.write_text("\n".join(parts),encoding="utf-8"); print("\n===== Diagnostics MariaDB DPAE =====\n"+"\n".join(parts))
def pytest_sessionfinish(session,exitstatus)->None:
 if not _started:return
 if exitstatus!=0:_write_innodb_diagnostics()
 _run("docker","rm","-f",_CONTAINER,check=False)
