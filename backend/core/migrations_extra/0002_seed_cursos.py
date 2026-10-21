from django.db import migrations

CURSOS = ["ENG_COMPUTACAO", "SISTEMAS_INFORMACAO", "LICENCIATURA_COMPUTACAO"]


def criar_cursos(apps, schema_editor):
    Curso = apps.get_model("core", "Curso")
    for nome in CURSOS:
        Curso.objects.get_or_create(nome=nome)


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.RunPython(criar_cursos, migrations.RunPython.noop)]
