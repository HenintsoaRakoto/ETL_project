from django.contrib import admin
from django.db import connection, models

class DynamicModelAdmin(admin.ModelAdmin):
    pass  # Pas besoin de personnalisation

def create_dynamic_model(table_name):
    attrs = {
        '__module__': 'etl.models',
        
        'Meta': type('Meta', (), {'db_table': table_name}),
    }
    return type(table_name.capitalize(), (models.Model,), attrs)



with connection.cursor() as cursor:
    cursor.execute("""
        SELECT name 
        FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%' 
        AND name NOT LIKE 'django_%' 
        AND name NOT LIKE 'auth_%';
    """)
    tables = cursor.fetchall()

for (table_name,) in tables:
    model = create_dynamic_model(table_name)
    try:
        admin.site.register(model, DynamicModelAdmin)
    except admin.sites.AlreadyRegistered:
        pass
