export PROJECTNAME=$(shell basename "$(PWD)")

# --- macOS signing/notarization config ---
APP_NAME        ?= LipidQMap
MAC_SPEC        ?= mac-app.spec
DIST_DIR        ?= dist
APP_BUNDLE      ?= $(DIST_DIR)/$(APP_NAME).app
ENTITLEMENTS    ?= entitlements.plist

# --- DMG packaging config ---
DMG_NAME        ?= $(APP_NAME)-macOS.dmg
DMG_PATH        ?= $(DIST_DIR)/$(DMG_NAME)
DMG_VOLNAME     ?= $(APP_NAME)
DMG_FORMAT      ?= UDZO
DMG_WINDOW_W    ?= 700
DMG_WINDOW_H    ?= 400
DMG_ICON_X      ?= 160
DMG_ICON_Y      ?= 200
DMG_DROP_X      ?= 520
DMG_DROP_Y      ?= 200

# Set to exact Developer ID cert CN (as shown by `security find-identity -v -p codesigning`)
CODESIGN_IDENTITY ?= $(shell security find-identity -v -p codesigning 2>/dev/null | \
	grep 'Developer ID Application' | head -n1 | sed -E 's/.*"(.+)".*/\1/')

# Notarytool keychain profile name you created with `notarytool store-credentials`
NOTARY_PROFILE ?= AC_NOTARY

# -------------------------------
# Development / maintenance tasks
# -------------------------------

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
	./venv/bin/pyside6-uic --from-imports resources/views/MsiStandardCalculatorDialog.ui -o app/generated/MsiStandardCalculator_ui.py
	
res: ## Generates and compresses resource listed in resources/resources.qrc
	./venv/bin/pyside6-rcc -compress 9 -o app/generated/resources_rc.py resources/resources.qrc

run: ## Runs the application
	export PYTHONPATH=$(PWD) && ./venv/bin/python3 app

coverage: ## Coverage report of the unit testing
	coverage run -m pytest
	coverage report
	coverage html

# -------------------------------
# macOS packaging / release tasks
# -------------------------------

.PHONY: mac-build mac-sign mac-verify mac-dmg mac-notarize mac-staple mac-release mac-all mac-unquarantine \
        mac-staple-app mac-staple-dmg

mac-build: ## Builds the application, removes onedir built, keep .app
	make clean
	./venv/bin/pyinstaller $(MAC_SPEC)
	rm -rf "$(DIST_DIR)/$(APP_NAME)"

mac-sign:
	@test -d "$(APP_BUNDLE)" || (echo "Missing $(APP_BUNDLE). Run 'make mac-build' first." && exit 1)
	# sign nested binaries first (more reliable than a single --deep)
	@/usr/bin/find "$(APP_BUNDLE)" -type f \( -perm -111 -or -name '*.dylib' -or -name '*.so' \) -print0 | \
	  xargs -0 -I {} codesign --force --options runtime --entitlements "$(ENTITLEMENTS)" --sign "$(CODESIGN_IDENTITY)" "{}"
	# then sign the top-level app
	codesign --force --options runtime --entitlements "$(ENTITLEMENTS)" --sign "$(CODESIGN_IDENTITY)" "$(APP_BUNDLE)"


mac-dmg: ## needs: brew install create-dmg
	@test -d "$(APP_BUNDLE)" || (echo "Missing $(APP_BUNDLE). Build/sign first." && exit 1)
	@rm -f "$(DMG_PATH)"
	create-dmg \
	  --format "$(DMG_FORMAT)" \
	  --volname "$(DMG_VOLNAME)" \
	  --window-size $(DMG_WINDOW_W) $(DMG_WINDOW_H) \
	  --icon "$(APP_NAME).app" $(DMG_ICON_X) $(DMG_ICON_Y) \
	  --app-drop-link $(DMG_DROP_X) $(DMG_DROP_Y) \
	  "$(DMG_PATH)" "$(DIST_DIR)"

mac-notarize: ## Submit DMG to Apple notarization (waits)
	@test -f "$(DMG_PATH)" || (echo "Missing $(DMG_PATH). Run 'make mac-dmg' first." && exit 1)
	xcrun notarytool submit "$(DMG_PATH)" --keychain-profile "$(NOTARY_PROFILE)" --wait

mac-staple-app:
	@test -d "$(APP_BUNDLE)" || (echo "Missing $(APP_BUNDLE)." && exit 1)
	xcrun stapler staple "$(APP_BUNDLE)"

mac-staple-dmg:
	@test -f "$(DMG_PATH)" || (echo "Missing $(DMG_PATH)." && exit 1)
	xcrun stapler staple "$(DMG_PATH)"

mac-staple: ## Staple notarization tickets to both the .app and the .dmg
	make mac-staple-app
	make mac-staple-dmg

mac-verify: ## Verify code signature locally (and Gatekeeper assessment)
	@echo "== codesign verify =="
	codesign -d --entitlements :- "$(APP_BUNDLE)" | grep -E 'allow-jit|allow-unsigned-executable-memory'
	codesign --verify --deep --strict --verbose=2 "$(APP_BUNDLE)"
	@echo "== spctl assessment =="
	spctl -a -vvv --type execute "$(APP_BUNDLE)" || true

mac-release: ## Final release artifact: DMG + checksum
	@test -f "$(DMG_PATH)" || (echo "Missing $(DMG_PATH). Build/sign/dmg/notarize/staple first." && exit 1)
	@rm -f "$(DMG_PATH).sha256"
	shasum -a 256 "$(DMG_PATH)" > "$(DMG_PATH).sha256"
	@echo "Release artifacts ready:"
	@echo "  - $(DMG_PATH)"
	@echo "  - $(DMG_PATH).sha256"

mac-all: ## Build → sign → DMG → notarize → staple (app & dmg) → verify → release
	make mac-build
	make mac-sign
	make mac-dmg
	make mac-notarize
	make mac-staple
	make mac-verify
	make mac-release

# Helper: remove quarantine locally if you downloaded your own build for testing
mac-unquarantine: ## Clear com.apple.quarantine on the built app (local testing)
	xattr -dr com.apple.quarantine "$(APP_BUNDLE)" || true
