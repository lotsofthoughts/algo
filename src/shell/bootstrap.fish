# Fish counterpart of bootstrap.sh: defines `algo` and `.a`, honours ALGO_HOME / ALGO_LANG,
# and loads tab completion. ALGO_HOME defaults to this file's parent's parent (the src/ tree).
set -q ALGO_HOME; or set -gx ALGO_HOME (dirname (dirname (status --current-filename)))
function algo
  set -l root $ALGO_HOME
  set -l lang py3
  if set -q ALGO_LANG
    set lang $ALGO_LANG
  end
  switch $lang
    case go
      pushd $root/go >/dev/null; go run ./cmd/algo $argv; set -l code $status; popd >/dev/null; return $code
    case py3 python python3
      env PYTHONPATH=$root/py3 python3 $root/py3/algo/cli/main.py $argv
    case '*'
      echo "Unsupported ALGO_LANG=$lang" >&2; return 2
  end
end
function .a; algo $argv; end
if status is-interactive; and test -f $ALGO_HOME/shell/completions/algo.fish
  source $ALGO_HOME/shell/completions/algo.fish
end
