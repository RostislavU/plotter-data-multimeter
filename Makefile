update:
	pip install -r requirements.txt

install_matplotlib:
	python -m pip install -U matplotlib

pep:
	yapf --style=PEP8 -i plotter.py