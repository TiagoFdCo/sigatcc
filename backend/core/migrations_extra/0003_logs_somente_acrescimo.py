from django.db import migrations

CRIAR = """
CREATE FUNCTION bloquear_alteracao_log() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'log e somente de acrescimo';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_auditoria_imutavel
BEFORE UPDATE OR DELETE ON log_auditoria
FOR EACH ROW EXECUTE FUNCTION bloquear_alteracao_log();

CREATE TRIGGER trg_log_acesso_imutavel
BEFORE UPDATE OR DELETE ON log_acesso
FOR EACH ROW EXECUTE FUNCTION bloquear_alteracao_log();
"""

REMOVER = """
DROP TRIGGER IF EXISTS trg_log_acesso_imutavel ON log_acesso;
DROP TRIGGER IF EXISTS trg_log_auditoria_imutavel ON log_auditoria;
DROP FUNCTION IF EXISTS bloquear_alteracao_log();
"""


class Migration(migrations.Migration):
    dependencies = [("core", "0002_seed_cursos")]
    operations = [migrations.RunSQL(CRIAR, REMOVER)]
