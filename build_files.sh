# build_files.sh
echo "Building the project..."

# 1. Install all dependencies from requirements.txt
python3.9 -m pip install -r requirements.txt

# 2. Run collectstatic to organize CSS/JS files
python3.9 manage.py collectstatic --noinput --clear

echo "Build End"
