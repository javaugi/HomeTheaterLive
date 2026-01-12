$env:PYTHONPATH="."
python -c "from app.dev_seed import create_test_user; create_test_user()"