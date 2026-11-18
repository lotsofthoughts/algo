# Bash completion for `algo` and its `.a` alias. Source it (bootstrap.sh does this when interactive).
# Compatible with bash 3.2+ (macOS default); needs no bash-completion package.
# Candidates for algorithm names come from `algo complete ...`, so they track the registry.

_algo_cands() { algo complete "$1" 2>/dev/null | cut -f1; }

_algo_complete() {
  local cur prev sub i word npos=0 words
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  COMPREPLY=()

  # First argument: the subcommand.
  if [ "$COMP_CWORD" -eq 1 ]; then
    words="search s problems p generate g inputs i run r shapes sh uses u pipe judge assert targets check verify -h --help"
    COMPREPLY=( $(compgen -W "$words" -- "$cur") )
    return 0
  fi

  sub="${COMP_WORDS[1]}"

  # Values for options that take one.
  case "$prev" in
    -a|--algo)                   COMPREPLY=( $(compgen -W "$(_algo_cands algos)" -- "$cur") ); return 0 ;;
    -o|--out-dir)                COMPREPLY=( $(compgen -d -- "$cur") ); return 0 ;;
    -i|--input|--expected|--actual) COMPREPLY=( $(compgen -f -- "$cur") ); return 0 ;;
    --comparator)                COMPREPLY=( $(compgen -W "$(_algo_cands comparators)" -- "$cur") ); return 0 ;;
    -l|--list)                   COMPREPLY=( $(compgen -W "study99" -- "$cur") ); return 0 ;;
    --ref)                       COMPREPLY=( $(compgen -d -- "$cur") ); return 0 ;;
    --seed|--top|--problems-top|--id|--disqualifier|-n) return 0 ;;   # free-form values
  esac

  # Flags for the current subcommand.
  if [[ "$cur" == -* ]]; then
    case "$sub" in
      search|s)    words="--id --disqualifier --top -p --problems --problems-top -j --json -h" ;;
      problems|p)  words="-a --algo --top -u --uses -l --list -j --json -h" ;;
      verify)      words="--ref -n --seed -j --json -v --verbose --fetch" ;;
      generate|g)  words="-o --out-dir -h" ;;
      inputs|i)    words="-a --algo -o --out-dir" ;;
      run|r)       words="--seed -v" ;;
      pipe)        words="-i --input -h" ;;
      assert)      words="--expected --actual --comparator -h" ;;
      *)           words="-h" ;;
    esac
    COMPREPLY=( $(compgen -W "$words" -- "$cur") )
    return 0
  fi

  # Count positional words already typed after the subcommand (skipping option values).
  for (( i = 2; i < COMP_CWORD; i++ )); do
    word="${COMP_WORDS[i]}"
    case "$word" in
      -a|--algo|-o|--out-dir|-i|--input|--expected|--actual|--comparator|--seed|--top|--problems-top|--id|--disqualifier|-l|--list|--ref|-n) i=$((i+1)) ;;
      -*) ;;
      *) npos=$((npos+1)) ;;
    esac
  done

  # Positional arguments.
  case "$sub" in
    search|s|generate|g|inputs|i) COMPREPLY=( $(compgen -W "$(_algo_cands algos)" -- "$cur") ) ;;
    pipe)                         COMPREPLY=( $(compgen -W "$(_algo_cands runnable)" -- "$cur") ) ;;
    shapes|sh)                    COMPREPLY=( $(compgen -W "$(_algo_cands runnable)" -- "$cur") ) ;;
    uses|u)                       COMPREPLY=( $(compgen -W "--top -p -j --json" -- "$cur") ) ;;
    judge)                        COMPREPLY=( $(compgen -W "$(_algo_cands judged)" -- "$cur") ) ;;
    run|r)
      # An algorithm starts the first stage and follows every `then`; otherwise offer `then`.
      if [ "$npos" -eq 0 ] || [ "$prev" = "then" ]; then
        COMPREPLY=( $(compgen -W "$(_algo_cands algos)" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "then" -- "$cur") )
      fi ;;
  esac
  return 0
}

complete -F _algo_complete algo
complete -F _algo_complete .a
