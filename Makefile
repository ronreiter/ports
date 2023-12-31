setup:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt
build:
	venv/bin/python setup.py py2app
	zip -r dist/Ports.zip dist/Ports.app
	rm -rf dist/Ports.app
clean:
	rm -rf build dist


