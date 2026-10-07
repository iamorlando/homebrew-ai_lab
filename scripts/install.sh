#!/bin/sh
# Homebrew's formula hooks cannot prompt. This optional wrapper offers model
# weights after install/upgrade; the website never downloads models silently.
set -eu
action=${1:-install}
if [ "$#" -gt 0 ]; then shift; fi
case "$action" in
  install) brew_action=install ;;
  update) brew_action=upgrade ;;
  *) printf '%s\n' 'Usage: install.sh [install|update] [--yes|--no-models]' >&2; exit 2 ;;
esac
model_option=${1:-}
if [ "$#" -gt 1 ]; then
  printf '%s\n' 'Supply at most one model option: --yes or --no-models.' >&2
  exit 2
fi
case "$model_option" in
  ''|--yes|--no-models) ;;
  *) printf '%s\n' 'Unknown model option. Choose --yes or --no-models.' >&2; exit 2 ;;
esac
if [ "$action" = update ]; then brew update; fi
brew "$brew_action" iamorlando/ai_lab/ai_lab
case "$model_option" in
  --no-models) ;;
  --yes) ai-lab setup install deepseek qwen clm --yes ;;
  '') ai-lab setup ;;
esac
