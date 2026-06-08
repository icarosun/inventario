from django.db import migrations, models


def build_acronym(name, used):
    words = [word for word in name.replace("-", " ").split() if word]
    acronym = "".join(word[0] for word in words).upper()[:20]
    if not acronym:
        acronym = "DEP"

    candidate = acronym
    suffix = 2
    while candidate in used:
        suffix_text = str(suffix)
        candidate = f"{acronym[:20 - len(suffix_text)]}{suffix_text}"
        suffix += 1

    used.add(candidate)
    return candidate


def populate_acronyms(apps, schema_editor):
    Department = apps.get_model("inventory", "Department")
    used = set()

    for department in Department.objects.order_by("name", "pk"):
        department.acronym = build_acronym(department.name, used)
        department.save(update_fields=["acronym"])


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0004_department_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="department",
            name="acronym",
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name="sigla"),
        ),
        migrations.RunPython(populate_acronyms, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="department",
            name="acronym",
            field=models.CharField(max_length=20, unique=True, verbose_name="sigla"),
        ),
    ]
