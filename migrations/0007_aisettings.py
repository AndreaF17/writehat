# Runtime-editable AI assistant settings (singleton model, edited via /admin-tools).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('writehat', '0006_finding_ai_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='AISettings',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('enabled', models.BooleanField(default=False)),
                ('base_url', models.CharField(blank=True, default='', max_length=500)),
                ('api_key', models.CharField(blank=True, default='', max_length=500)),
                ('model_name', models.CharField(blank=True, default='', max_length=200)),
                ('temperature', models.FloatField(default=0.2)),
                ('max_tokens', models.IntegerField(default=1200)),
                ('timeout', models.IntegerField(default=60)),
                ('verify_ssl', models.BooleanField(default=True)),
                ('system_prompt', models.TextField(blank=True, default='')),
                ('configured', models.BooleanField(default=False)),
            ],
        ),
    ]
