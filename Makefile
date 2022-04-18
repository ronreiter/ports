setup:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt
build:
	rm -rf build dist
	venv/bin/python setup.py py2app

