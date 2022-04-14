setup:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt
build:
	venv/bin/python setup.py py2app

