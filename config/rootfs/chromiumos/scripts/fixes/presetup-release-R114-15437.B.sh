#!/bin/bash
echo "Applying R114 specific early workarounds"
# if board trogdor we need to revert patch early, here
if [ "${BOARD}" == "trogdor" ]; then
  # issue/284169814 revert caf6c399cb013fb44b767d32853a7ba181a59c23 in chromiumos/overlays/board-overlays
  echo "Reverting issue/284169814 commit caf6c399cb013fb44b767d32853a7ba181a59c23 for trogdor"
  cd src/overlays
  git revert caf6c399cb013fb44b767d32853a7ba181a59c23
  cd -
fi
# grunt/StoneyRidge kernel 4.14 broken, so switch to 5.10
sed -i 's/kernel-4_14/kernel-5_10/g' src/overlays/chipset-stnyridge/profiles/base/make.defaults
