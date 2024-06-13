export PROJECTNAME=$(shell basename "$(PWD)")

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean: clean-pyc ## Clean package
	rm -rf build dist

setup: ## Re-initiates virtualenv
	make clean 
	rm -rf venv
	python3.12 -m venv venv
	./venv/bin/python3 -m pip install -r requirements/dev.txt

deps: ## Reinstalls dependencies
	./venv/bin/python3 -m pip install -r requirements/dev.txt

ui: ## Converts ui files in resources/views to python
	./venv/bin/pyside6-uic --from-imports resources/views/MsiImportDialog.ui -o app/generated/MsiImportDialog_ui.py
	./venv/bin/pyside6-uic --from-imports resources/views/MsiMainWindow.ui -o app/generated/MsiMainWindow_ui.py

res: ## Generates and compresses resource listed in resources/resources.qrc
	./venv/bin/pyside6-rcc -compress 9 -o app/generated/resources_rc.py resources/resources.qrc

run: ## Runs the application
	export PYTHONPATH=$(PWD) && ./venv/bin/python3 app

build: ## Builds the application
	./venv/bin/pyinstaller msi-quant.spec

installer-spec:
	pyi-makespec --onedir --additional-hooks-dir="pyinstaller/" --name="Msi-Quant" --windowed app/__main__.py

coverage: ## Coverage report of the unit testing
	coverage run -m pytest
	coverage report
	coverage html