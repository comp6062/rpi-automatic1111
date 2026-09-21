#!/bin/bash
# Keep Pi-Apps API shell options separate from the strict standalone installer.
action=$1
DIRECTORY=$2
shift 2
app='Stable Diffusion'
script_input=${SD_PIAPPS_INPUT:-}
export DIRECTORY app script_input
# shellcheck source=/dev/null
source "$DIRECTORY/api" || exit 1
case "$action" in
  install) install_packages "$@" ;;
  purge) purge_packages ;;
  *) exit 1 ;;
esac
