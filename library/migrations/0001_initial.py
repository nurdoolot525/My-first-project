import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('bio', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300)),
                ('isbn', models.CharField(max_length=20, unique=True)),
                ('total_copies', models.PositiveIntegerField(default=1)),
                ('available_copies', models.PositiveIntegerField(default=1)),
                ('authors', models.ManyToManyField(related_name='books', to='library.author')),
            ],
        ),
        migrations.CreateModel(
            name='Loan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issued_at', models.DateTimeField(auto_now_add=True)),
                ('due_date', models.DateField(verbose_name='срок возврата')),
                ('returned_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('issued', 'Issued'), ('returned', 'Returned')], default='issued', max_length=20)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='loans', to='library.book')),
                ('reader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loans', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-issued_at'],
            },
        ),
    ]
