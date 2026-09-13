#!/usr/bin/env zsh
# iPhone-Ian CAD helpers.
# Enable once by adding this line to ~/.zshrc, then open a new terminal:
#   source /Users/cheddar/Documents/CODE/iPhone-Ian/parts/aliases.zsh
# Commands work from ANY directory — no venv activation, no cd needed.

export IPHONE_IAN="/Users/cheddar/Documents/CODE/iPhone-Ian"
IPHONE_IAN_PY="$IPHONE_IAN/.venv/bin/python"

# internal: resolve the single part file whose name starts with "<n>_"
_123_find() {
  local matches=("$IPHONE_IAN"/parts/${1}_*.py(N))
  if (( ${#matches} == 0 )); then
    echo "123: no part named ${1}_* in parts/" >&2
    return 1
  fi
  print -r -- "${matches[1]}"
}

# 123_part <n>  -> render part n, export STL + STEP into parts/
123_part() {
  local f; f=$(_123_find "$1") || return 1
  ( cd "$IPHONE_IAN/parts" && "$IPHONE_IAN_PY" "${f:t}" )
}

# 123_show <n>  -> render part n AND push it to the live viewer (start it with 123_viewer)
123_show() {
  local f; f=$(_123_find "$1") || return 1
  ( cd "$IPHONE_IAN/parts" && SHOW=1 OCP_PORT=3939 "$IPHONE_IAN_PY" "${f:t}" )
}

# 123_viewer -> open the 3D viewer in your browser (leave running while you iterate)
123_viewer() { "$IPHONE_IAN_PY" -m ocp_vscode --port 3939 }

# numbered conveniences
123_part1() { 123_part 1 }
123_show1() { 123_show 1 }
