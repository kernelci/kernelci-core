#!/bin/bash
echo "packagefix: Applying R116 specific workarounds"

case ${BOARD} in
    dedede)
    grep -q "tpm2" src/overlays/baseboard-dedede/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2 cr50_onboard"' >>src/overlays/baseboard-dedede/profiles/base/make.defaults
    ;;
    hatch)
    grep -q "tpm2" src/overlays/baseboard-hatch/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/baseboard-hatch/profiles/base/make.defaults
    ;;
    volteer)
    grep -q "tpm2" src/overlays/baseboard-volteer/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/baseboard-volteer/profiles/base/make.defaults
    ;;
    zork)
    grep -q "tpm2" src/overlays/overlay-zork/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/overlay-zork/profiles/base/make.defaults
    ;;
    grunt)
    grep -q "tpm2" src/overlays/baseboard-grunt/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/baseboard-grunt/profiles/base/make.defaults
    ;;
    puff)
    grep -q "tpm2" src/overlays/baseboard-puff/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/baseboard-puff/profiles/base/make.defaults
    ;;
    guybrush)
    grep -q "tpm2" src/overlays/overlay-guybrush/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/overlay-guybrush/profiles/base/make.defaults
    ;;
    *)
    echo "No workarounds found for this board"
    ;;
esac
