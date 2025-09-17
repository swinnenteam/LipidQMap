export PROJECTNAME=$(shell basename "$(PWD)")

# --- macOS signing/notarization config ---
APP_NAME        ?= LipidQMap
MAC_SPEC        ?= app.spec
DIST_DIR        ?= dist
APP_BUNDLE      ?= $(DIST_DIR)/$(APP_NAME).app
ZIP_FOR_NOTARY  ?= $(DIST_DIR)/$(APP_NAME).zip
RELEASE_ZIP     ?= $(DIST_DIR)/$(APP_NAME)-macOS.zip

# Set to exact Developer ID cert CN (as shown by `security find-identity -v -p codesigning`)
# CODESIGN_IDENTITY ?= Developer ID Application: name (code)
CODESIGN_IDENTITY ?= $(shell security find-identity -v -p codesigning 2>/dev/null | \
	grep 'Developer ID Application' | head -n1 | sed -E 's/.*"(.+)".*/\1/')

# Notarytool keychain profile name you created with `notarytool store-credentials`
NOTARY_PROFILE ?= AC_NOTARY

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
	./venv/bin/pyside6-uic --from-imports resources/views/MsiSaveDialog.ui -o app/generated/MsiSaveDialog_ui.py
	./venv/bin/pyside6-uic --from-imports resources/views/MsiMainWindow.ui -o app/generated/MsiMainWindow_ui.py
	./venv/bin/pyside6-uic --from-imports resources/views/MsiAboutDialog.ui -o app/generated/MsiAboutDialog_ui.py
	./venv/bin/pyside6-uic --from-imports resources/views/MsiSettingsDialog.ui -o app/generated/MsiSettingsDialog_ui.py
	./venv/bin/pyside6-uic --from-imports resources/views/MsiStandardCalculatorDialog.ui -o app/generated/MsiStandardCalculatorDialog_ui.py
	
res: ## Generates and compresses resource listed in resources/resources.qrc
	./venv/bin/pyside6-rcc -compress 9 -o app/generated/resources_rc.py resources/resources.qrc

run: ## Runs the application
	export PYTHONPATH=$(PWD) && ./venv/bin/python3 app

coverage: ## Coverage report of the unit testing
	coverage run -m pytest
	coverage report
	coverage html

.PHONY: mac-build mac-sign mac-verify mac-zip mac-notarize mac-staple mac-release mac-all mac-unquarantine

mac-build: ## Builds the application
	make clean
	./venv/bin/pyinstaller $(MAC_SPEC)

mac-sign: ## Codesign the .app with hardened runtime
	@test -d "$(APP_BUNDLE)" || (echo "Missing $(APP_BUNDLE). Run 'make mac-build' first." && exit 1)
	codesign --deep --force --verify --verbose \
		--options runtime \
		--sign "$(CODESIGN_IDENTITY)" "$(APP_BUNDLE)"

mac-verify: ## Verify code signature locally (and Gatekeeper assessment)
	@echo "== codesign verify =="
	codesign --verify --deep --strict --verbose=2 "$(APP_BUNDLE)"
	@echo "== spctl assessment =="
	spctl -a -vvv --type execute "$(APP_BUNDLE)" || true

mac-zip: ## Create a zip (keeping parent) for notarization
	@rm -f "$(ZIP_FOR_NOTARY)"
	ditto -c -k --keepParent "$(APP_BUNDLE)" "$(ZIP_FOR_NOTARY)"

mac-notarize: ## Submit to Apple notarization (waits)
	@test -f "$(ZIP_FOR_NOTARY)" || (echo "Missing $(ZIP_FOR_NOTARY). Run 'make mac-zip' first." && exit 1)
	xcrun notarytool submit "$(ZIP_FOR_NOTARY)" --keychain-profile "$(NOTARY_PROFILE)" --wait

mac-staple: ## Staple notarization ticket to the .app
	xcrun stapler staple "$(APP_BUNDLE)"

mac-release: ## Create the final release zip (stapled app inside) + checksum
	@test -d "$(APP_BUNDLE)" || (echo "Missing $(APP_BUNDLE). Build/sign/staple first." && exit 1)
	@rm -f "$(RELEASE_ZIP)" "$(RELEASE_ZIP).sha256"
	ditto -c -k --keepParent "$(APP_BUNDLE)" "$(RELEASE_ZIP)"
	shasum -a 256 "$(RELEASE_ZIP)" > "$(RELEASE_ZIP).sha256"
	@echo "Release artifacts ready:"
	@echo "  - $(RELEASE_ZIP)"
	@echo "  - $(RELEASE_ZIP).sha256"

mac-all: ## Build → sign → verify → zip → notarize → staple → release
	make mac-build
	make mac-sign
	make mac-verify
	make mac-zip
	make mac-notarize
	make mac-staple
	make mac-release

# Helper: remove quarantine locally if you downloaded your own build for testing
mac-unquarantine: ## Clear com.apple.quarantine on the built app (local testing)
	xattr -dr com.apple.quarantine "$(APP_BUNDLE)" || true
