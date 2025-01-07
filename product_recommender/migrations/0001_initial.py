# Generated by Django 5.1.4 on 2025-01-07 19:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('product_id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('image_url', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('recommended_product_id', models.IntegerField(primary_key=True, serialize=False)),
                ('good_recommendation', models.BooleanField()),
                ('created_at_unix', models.IntegerField(blank=True, null=True)),
                ('initial_product_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product_recommender.product')),
            ],
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('review_id', models.IntegerField()),
                ('review_title', models.TextField(null=True)),
                ('review_score', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
                ('review_text', models.TextField(null=True)),
                ('created_at_unix', models.IntegerField(blank=True, null=True)),
                ('product_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product_recommender.product')),
            ],
        ),
        migrations.CreateModel(
            name='Summary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('positive_sentiment', models.TextField(null=True)),
                ('negative_sentiment', models.TextField(null=True)),
                ('product_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product_recommender.product')),
            ],
        ),
    ]
