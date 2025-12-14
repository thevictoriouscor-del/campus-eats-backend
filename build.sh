#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Instalar requerimientos
pip install -r requirements.txt

# 2. Recolectar archivos estáticos (CSS/Imágenes para la nube)
python manage.py collectstatic --noinput

# 3. Actualizar la base de datos
python manage.py migrate

# 4. TRUCO DE MAGIA: Crear Superusuario Automático si no existe
# Cambia 'admin@uniandes.edu.co' y 'admin123' por lo que quieras usar
python manage.py shell -c "from core.models import User; User.objects.create_superuser('admin@uniandes.edu.co', 'admin123', codigo_estudiante='000000000', nombre_completo='Super Admin') if not User.objects.filter(email='admin@uniandes.edu.co').exists() else print('El Admin ya existe')"