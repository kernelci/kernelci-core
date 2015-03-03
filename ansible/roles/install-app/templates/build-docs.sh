BASE_PATH="{{ install_base }}"
CHECKOUT_DIR="$BASE_PATH/{{ hostname }}"
DOC_DIR="$CHECKOUT_DIR/doc"
BUILD_DIR="$DOC_DIR/build/html"
SCHEMA_DIR="$DOC_DIR/schema"
VENV_DIR="$BASE_PATH/.venv/{{ hostname }}"

. "$VENV_DIR/bin/activate"
cd $DOC_DIR && make html > /dev/null
deactivate

cp -ax $BUILD_DIR/* {{ web_root }}/{{ hostname }}
cp -ax $SCHEMA_DIR {{ web_root }}/{{ hostname }}

chown -R {{ web_user}}:{{ web_user }} {{ web_root }}/{{ hostname }}

exit 0
