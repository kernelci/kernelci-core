#!/bin/bash
echo "Applying R114 specific late workarounds for packages"

case ${BOARD} in
    coral)
    sed ':a;N;$!ba;s/DEPEND="\n\tchromeos-base\/fibocom-firmware\n"/# DEPEND="\n\t# chromeos-base\/fibocom-firmware\n# "/g' -i src/overlays/overlay-coral/chromeos-base/modemfwd-helpers/modemfwd-helpers-0.0.1.ebuild
    sed -i s,'media-libs/apl-hotword-support','# media-libs/apl-hotword-support', src/overlays/overlay-coral/media-libs/lpe-support-topology/lpe-support-topology-0.0.1.ebuild
    sed -i s,'USE="${USE} cros_ec"','# USE="${USE} cros_ec"', src/overlays/baseboard-coral/profiles/base/make.defaults
    ;;
    dedede)
    grep -q "tpm2" src/overlays/baseboard-dedede/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2 cr50_onboard"' >>src/overlays/baseboard-dedede/profiles/base/make.defaults
    ;;
    hatch)
    sed -i 's/EC_BOARDS=()/EC_BOARDS=(hatch)/' src/third_party/chromiumos-overlay/eclass/cros-ec-board.eclass
    grep -q "tpm2" src/overlays/baseboard-hatch/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/baseboard-hatch/profiles/base/make.defaults
    ;;
    nami)
    grep -q "tpm2" src/overlays/baseboard-nami/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/baseboard-nami/profiles/base/make.defaults
    ;;
    octopus)
    sed -i s,'use fuzzer || die',"#use fuzzer || die", src/third_party/chromiumos-overlay/eclass/cros-ec-board.eclass
    # Workaround b/244460939 T38487 - octopus missing proper tpm USE flags
    grep -q "tpm2" src/overlays/baseboard-octopus/profiles/base/make.defaults || echo 'USE="${USE} -tpm tpm2"' >>src/overlays/baseboard-octopus/profiles/base/make.defaults
    ;;
    sarien)
    sed ':a;N;$!ba;s/DEPEND="\n\tchromeos-base\/fibocom-firmware\n"/# DEPEND="\n\t# chromeos-base\/fibocom-firmware\n# "/g' -i src/overlays/overlay-sarien/chromeos-base/modemfwd-helpers/modemfwd-helpers-0.0.1.ebuild
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
    *)
    echo "No issues found for this board"
    ;;
esac
