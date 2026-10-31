from django.db import migrations


def assign_single_center(apps, schema_editor):
    """Link legacy evacuees to a center when the association is unambiguous.

    Before this migration, evacuees were associated to a center only through
    their creator (``Info.user`` -> ``EvacuationCenter.user``). A creator that
    manages exactly one center can therefore be migrated automatically. When a
    creator manages several centers the record stays unassigned (NULL) and is
    fixed by staff from the Evacuees Management screen, because guessing would
    silently move people to the wrong shelter.
    """
    Info = apps.get_model('info', 'Info')
    EvacuationCenter = apps.get_model('evacuation', 'EvacuationCenter')

    for info in Info.objects.filter(evacuation_center__isnull=True, user__isnull=False):
        center_ids = list(
            EvacuationCenter.objects.filter(user_id=info.user_id)
            .values_list('id', flat=True)[:2]
        )
        if len(center_ids) == 1:
            info.evacuation_center_id = center_ids[0]
            info.save(update_fields=['evacuation_center'])


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0004_info_evacuation_center'),
    ]

    operations = [
        migrations.RunPython(assign_single_center, migrations.RunPython.noop),
    ]
