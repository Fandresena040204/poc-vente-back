from django.db import connection


def generate_reference(sequence_name, prefix, padding=5):
    with connection.cursor() as cursor:
        cursor.execute("SELECT nextval(%s)", [sequence_name])
        next_value = cursor.fetchone()[0]
    return f'{prefix}{next_value:0{padding}d}'
