from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brackets', '0002_alter_bracket_unique_together_bracket_belt_group_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='bracket',
            index=models.Index(fields=['event_id', 'category_code', 'class_code', 'sex', 'belt_group'], name='brackets_evt_cat_cls_sex_belt_idx'),
        ),
        migrations.AddIndex(
            model_name='bracket',
            index=models.Index(fields=['event_id', 'category_code'], name='brackets_evt_cat_idx'),
        ),
    ]

