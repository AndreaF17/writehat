# AI assistant: per-field prompt storage (aiPrompts) on every finding table,
# and an internal-only notes field on engagement findings.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('writehat', '0005_nullable_finding_prefix'),
    ]

    operations = [
        # aiPrompts lives on BaseDatabaseFinding (abstract), so it lands on each
        # concrete finding table and on the DREAD/Proactive multi-table parents.
        migrations.AddField(
            model_name='cvssdatabasefinding',
            name='aiPrompts',
            field=models.TextField(blank=True, default='{}', null=True),
        ),
        migrations.AddField(
            model_name='cvssengagementfinding',
            name='aiPrompts',
            field=models.TextField(blank=True, default='{}', null=True),
        ),
        migrations.AddField(
            model_name='cvss4databasefinding',
            name='aiPrompts',
            field=models.TextField(blank=True, default='{}', null=True),
        ),
        migrations.AddField(
            model_name='cvss4engagementfinding',
            name='aiPrompts',
            field=models.TextField(blank=True, default='{}', null=True),
        ),
        migrations.AddField(
            model_name='dreadfinding',
            name='aiPrompts',
            field=models.TextField(blank=True, default='{}', null=True),
        ),
        migrations.AddField(
            model_name='proactivefinding',
            name='aiPrompts',
            field=models.TextField(blank=True, default='{}', null=True),
        ),
        # notes is engagement-only and internal (never rendered or exported).
        migrations.AddField(
            model_name='cvssengagementfinding',
            name='notes',
            field=models.TextField(blank=True, default=str, null=True),
        ),
        migrations.AddField(
            model_name='cvss4engagementfinding',
            name='notes',
            field=models.TextField(blank=True, default=str, null=True),
        ),
        migrations.AddField(
            model_name='dreadengagementfinding',
            name='notes',
            field=models.TextField(blank=True, default=str, null=True),
        ),
        migrations.AddField(
            model_name='proactiveengagementfinding',
            name='notes',
            field=models.TextField(blank=True, default=str, null=True),
        ),
    ]
