from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dataportal", "0003_annotation_run"),
    ]

    operations = [
        migrations.DeleteModel(
            name="AnnotationRun",
        ),
    ]
