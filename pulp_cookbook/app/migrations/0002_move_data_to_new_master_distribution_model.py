from django.db import connection, migrations, models, transaction
import django.db.models.deletion


def migrate_data_from_old_model_to_new_model_up(apps, schema_editor):
    """ Move objects from CookbookDistribution to NewCookbookDistribution."""
    CookbookDistribution = apps.get_model('cookbook', 'CookbookDistribution')
    NewCookbookDistribution = apps.get_model('cookbook', 'NewCookbookDistribution')
    for cookbook_distribution in CookbookDistribution.objects.all():
        with transaction.atomic():
            NewCookbookDistribution(
                pulp_id=cookbook_distribution.pulp_id,
                pulp_created=cookbook_distribution.pulp_created,
                pulp_last_updated=cookbook_distribution.pulp_last_updated,
                pulp_type=cookbook_distribution.pulp_type,
                name=cookbook_distribution.name,
                base_path=cookbook_distribution.base_path,
                content_guard=cookbook_distribution.content_guard,
                remote=cookbook_distribution.remote,
                publication=cookbook_distribution.publication
            ).save()
            cookbook_distribution.delete()


def migrate_data_from_old_model_to_new_model_down(apps, schema_editor):
    """ Move objects from NewCookbookDistribution to CookbookDistribution."""
    CookbookDistribution = apps.get_model('cookbook', 'CookbookDistribution')
    NewCookbookDistribution = apps.get_model('cookbook', 'NewCookbookDistribution')
    for cookbook_distribution in NewCookbookDistribution.objects.all():
        with transaction.atomic():
            CookbookDistribution(
                pulp_id=cookbook_distribution.pulp_id,
                pulp_created=cookbook_distribution.pulp_created,
                pulp_last_updated=cookbook_distribution.pulp_last_updated,
                pulp_type=cookbook_distribution.pulp_type,
                name=cookbook_distribution.name,
                base_path=cookbook_distribution.base_path,
                content_guard=cookbook_distribution.content_guard,
                remote=cookbook_distribution.remote,
                publication=cookbook_distribution.publication
            ).save()
            cookbook_distribution.delete()


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('core', '0062_add_new_distribution_mastermodel'),
        ('cookbook', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewCookbookDistribution',
            fields=[
                ('distribution_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='cookbook_cookbookdistribution', serialize=False, to='core.Distribution')),
            ],
            options={
                'default_related_name': '%(app_label)s_%(model_name)s',
            },
            bases=('core.distribution',),
        ),
        migrations.RunPython(
            code=migrate_data_from_old_model_to_new_model_up,
            reverse_code=migrate_data_from_old_model_to_new_model_down,
        ),
        migrations.DeleteModel(
            name='CookbookDistribution',
        ),
        migrations.RenameModel(
            old_name='NewCookbookDistribution',
            new_name='CookbookDistribution',
        ),
    ]
