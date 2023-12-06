#!/bin/bash
echo "packagefix: Applying R118 specific workarounds"

# TODO(aratiu): Drop these workarounds once CL 4868824 lands
# CL 4868824 only adds for grunt/zork/hatch because the others have been added post R118
case ${BOARD} in
    hatch)
    grep -q "tpm2" src/overlays/baseboard-hatch/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/baseboard-hatch/profiles/base/make.defaults
    ;;
    zork)
    grep -q "tpm2" src/overlays/overlay-zork/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/overlay-zork/profiles/base/make.defaults
    ;;
    grunt)
    grep -q "tpm2" src/overlays/baseboard-grunt/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2 cr50_onboard"' >>src/overlays/baseboard-grunt/profiles/base/make.defaults
    ;;
    puff)
    grep -q "tpm2" src/overlays/baseboard-puff/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/baseboard-puff/profiles/base/make.defaults
    ;;
    guybrush)
    grep -q "tpm2" src/overlays/overlay-guybrush/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/overlay-guybrush/profiles/base/make.defaults
    ;;
    skyrim)
    grep -q "tpm2" src/overlays/overlay-skyrim/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2 ti50_onboard"' >>src/overlays/overlay-skyrim/profiles/base/make.defaults
    ;;
    *)
    echo "No workarounds found for this board"
    ;;
esac
