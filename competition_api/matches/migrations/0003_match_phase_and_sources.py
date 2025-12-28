from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('matches', '0002_remove_match_matches_mat_event_i_e2e3d5_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='phase',
            field=models.CharField(choices=[('MAIN', 'Main'), ('REPECHAGE', 'Repechage'), ('BRONZE', 'Bronze'), ('FINAL', 'Final')], default='MAIN', max_length=20),
        ),
        migrations.AddField(
            model_name='match',
            name='source_blue_match_id',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='match',
            name='source_white_match_id',
            field=models.UUIDField(blank=True, null=True),
        ),
    ]

