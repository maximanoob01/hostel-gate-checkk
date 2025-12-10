echo "Building the project..."
python -m pip install -r requirements.txt

echo "Make Migrations..."
python manage.py makemigrations --noinput

echo "Collect Static..."
python manage.py collectstatic --noinput --clear