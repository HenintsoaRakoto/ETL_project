from django.shortcuts import render, redirect
from .forms import UploadFileForm
from django.db import connection
import pandas as pd
import os
from django.contrib import messages


def home(request):
    return render(request, 'etl/home.html')


def map_dtype_to_sql(dtype):
    """ Mappe les types de données pandas aux types SQL correspondants """
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    elif pd.api.types.is_float_dtype(dtype):
        return "REAL"
    elif pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    else:  # Par défaut, considérer comme TEXT
        return "TEXT"

def sanitize_table_name(filename):
    return os.path.splitext(filename)[0].replace(" ", "_").replace("-", "_")

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            separator = form.cleaned_data['separator'] or ','

            try:
                df = pd.read_csv(file, sep=separator)
            except Exception as e:
                return render(request, 'etl/upload.html', {'form': form, 'error': str(e)})

            table_name = sanitize_table_name(file.name)

            # Vérifier si la colonne 'id' existe, sinon l'ajouter
            if 'id' not in df.columns:
                df.insert(0, 'id', range(1, len(df) + 1))

            # Générer les types de colonnes dynamiquement
            columns_definitions = ', '.join([f'"{col}" {map_dtype_to_sql(df[col])}' for col in df.columns])

            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                cursor.execute(f"CREATE TABLE {table_name} ({columns_definitions})")

                for _, row in df.iterrows():
                    values = ', '.join(["'{}'".format(str(val).replace("'", "''")) if not pd.isna(val) else "NULL" for val in row])

                    cursor.execute(f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({values})")

            messages.success(request, f"Table '{table_name}' créée et remplie avec succès.")
            return redirect('etl:tables')

    else:
        form = UploadFileForm()

    return render(request, 'etl/upload.html', {'form': form})



def list_tables(request):
    tables_info = []

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%' 
            AND name NOT LIKE 'django_%' 
            AND name NOT LIKE 'auth_%';
        """)
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            # Récupère les colonnes avec PRAGMA
            cursor.execute(f"PRAGMA table_info({table})")
            nb_columns = len(cursor.fetchall())

            # Récupère le nombre de lignes avec COUNT
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                nb_rows = cursor.fetchone()[0]
            except:
                nb_rows = "Erreur"

            tables_info.append({
                'name': table,
                'nb_columns': nb_columns,
                'nb_rows': nb_rows,
            })

    return render(request, 'etl/tables.html', {'tables_info': tables_info})


def view_table(request, table_name):
    with connection.cursor() as cursor:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
    return render(request, 'etl/display.html', {'table_name': table_name, 'columns': columns, 'rows': rows})

def execute_query(request):
    result = None
    columns = []
    tables_info = []  # Initialisation de la liste des tables

    if request.method == "POST":
        sql_query = request.POST.get("sql_query", "").strip()

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql_query)

                # Si la requête est un SELECT, récupérer les résultats et les afficher
                if sql_query.lower().startswith("select"):
                    result = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]  # Récupérer les noms des colonnes

                messages.success(request, "Requête exécutée avec succès.")

        except Exception as e:
            messages.error(request, f"Erreur d'exécution : {e}")

    # Récupération des tables après l'exécution de la requête SQL (tout comme dans la vue 'list_tables')
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%' 
            AND name NOT LIKE 'django_%' 
            AND name NOT LIKE 'auth_%';
        """)
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            # Récupère le nombre de colonnes avec PRAGMA
            cursor.execute(f"PRAGMA table_info({table})")
            nb_columns = len(cursor.fetchall())

            # Récupère le nombre de lignes avec COUNT
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                nb_rows = cursor.fetchone()[0]
            except:
                nb_rows = "Erreur"

            tables_info.append({
                'name': table,
                'nb_columns': nb_columns,
                'nb_rows': nb_rows,
            })

    # Envoi des résultats, des colonnes et de la liste des tables à la page
    return render(request, "etl/tables.html", {
        "result": result,
        "columns": columns,
        "tables_info": tables_info  # Passer la liste des tables au template
    })


def delete_table(request, table_name):
    with connection.cursor() as cursor:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            messages.success(request, f"La table '{table_name}' a été supprimée avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression de la table : {e}")
    
    return redirect('etl:tables')


    # return render(request, "etl/tables.html", {
    #     "result": result,
    #     "columns": columns
    # })

# def execute_query(request):
#     result = None
#     columns = []

#     if request.method == "POST":
#         sql_query = request.POST.get("sql_query")

#         try:
#             with connection.cursor() as cursor:
#                 cursor.execute(sql_query)
                
#                 # Si c'est un SELECT, récupérer les résultats
#                 if sql_query.strip().lower().startswith("select"):
#                     result = cursor.fetchall()
#                     columns = [desc[0] for desc in cursor.description]

#                 messages.success(request, "Requête exécutée avec succès.")
#         except Exception as e:
#             messages.error(request, f"Erreur d'exécution : {e}")

#     return redirect('etl:tables')

#     # return render(request, "etl/tables.html", {"result": result, "columns": columns})