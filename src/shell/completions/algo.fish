# Fish completion for `algo` and its `.a` alias. Sourced by bootstrap.fish, or copy/symlink to
# ~/.config/fish/completions/algo.fish. Candidates come from `algo complete ...` (live registry).

function __algo_prev_is
    set -l t (commandline -opc)
    contains -- $t[-1] $argv
end

function __algo_run_algo_pos
    # An algorithm starts a `run` stage: right after `run`/`r` or after `then`.
    set -l t (commandline -opc)
    contains -- $t[-1] run r then
end

for c in algo .a
    complete -c $c -f

    # Subcommands (long name + alias).
    complete -c $c -n __fish_use_subcommand -a 'search s' -d 'find algorithms'
    complete -c $c -n __fish_use_subcommand -a 'problems p' -d 'find problems -> algorithms'
    complete -c $c -n __fish_use_subcommand -a 'generate g' -d 'write the algorithm library file'
    complete -c $c -n __fish_use_subcommand -a 'inputs i' -d 'write inputs.py for an algorithm'
    complete -c $c -n __fish_use_subcommand -a 'run r' -d 'run with shorthand input (chain with then)'
    complete -c $c -n __fish_use_subcommand -a 'shapes sh' -d 'show input fields per solver'
    complete -c $c -n __fish_use_subcommand -a pipe -d 'JSON in -> solver -> JSON out'
    complete -c $c -n __fish_use_subcommand -a judge -d 'check a target against its expected output'
    complete -c $c -n __fish_use_subcommand -a assert -d 'compare JSON with an expected file'
    complete -c $c -n __fish_use_subcommand -a targets -d 'list judged targets'
    complete -c $c -n __fish_use_subcommand -a check -d 'validate registry, problems, solvers, schemas'
    complete -c $c -n __fish_use_subcommand -a verify -d 'differential-test solutions vs reference + brute force'

    # search / s
    complete -c $c -n '__fish_seen_subcommand_from search s' -l id -r -d 'match identification phrases'
    complete -c $c -n '__fish_seen_subcommand_from search s' -l disqualifier -r -d 'match disqualifier phrases'
    complete -c $c -n '__fish_seen_subcommand_from search s' -l top -r -d 'max results'
    complete -c $c -n '__fish_seen_subcommand_from search s' -s p -l problems -d 'list example problems per match'
    complete -c $c -n '__fish_seen_subcommand_from search s' -l problems-top -r -d 'problems per match'
    complete -c $c -n '__fish_seen_subcommand_from search s' -s j -l json -d 'full JSON output'
    complete -c $c -n '__fish_seen_subcommand_from search s generate g' -a '(algo complete algos 2>/dev/null)'

    # problems / p
    complete -c $c -n '__fish_seen_subcommand_from problems p' -s a -l algo -x -a '(algo complete algos 2>/dev/null)' -d 'only problems using this algorithm'
    complete -c $c -n '__fish_seen_subcommand_from problems p' -l top -r -d 'max results'
    complete -c $c -n '__fish_seen_subcommand_from problems p' -s j -l json -d 'JSON output'
    complete -c $c -n '__fish_seen_subcommand_from problems p' -s u -l uses -d 'show other uses of the technique'
    complete -c $c -n '__fish_seen_subcommand_from problems p' -s l -l list -x -a 'study99' -d 'only problems on a list'

    # verify
    complete -c $c -n '__fish_seen_subcommand_from verify' -l ref -r -a '(__fish_complete_directories)' -d 'cnkyrpsgl/leetcode clone'
    complete -c $c -n '__fish_seen_subcommand_from verify' -s n -r -d 'random cases per problem'
    complete -c $c -n '__fish_seen_subcommand_from verify' -l seed -r -d 'random seed'
    complete -c $c -n '__fish_seen_subcommand_from verify' -l fetch -d 'clone the reference repo if missing'
    complete -c $c -n '__fish_seen_subcommand_from verify' -s j -l json -d 'JSON output'
    complete -c $c -n '__fish_seen_subcommand_from verify' -s v -l verbose -d 'print every failure'

    # generate / g
    complete -c $c -n '__fish_seen_subcommand_from generate g' -s o -l out-dir -r -a '(__fish_complete_directories)' -d 'output directory'

    # inputs / i  (algorithm is the last bare word, or -a)
    complete -c $c -n '__fish_seen_subcommand_from inputs i' -s a -l algo -x -a '(algo complete algos 2>/dev/null)' -d 'algorithm'
    complete -c $c -n '__fish_seen_subcommand_from inputs i' -s o -l out-dir -r -a '(__fish_complete_directories)' -d 'output directory'
    complete -c $c -n '__fish_seen_subcommand_from inputs i' -a '(algo complete algos 2>/dev/null)'

    # run / r
    complete -c $c -n '__fish_seen_subcommand_from run r' -l seed -x -d 'seed for rand: values'
    complete -c $c -n '__fish_seen_subcommand_from run r' -s v -d 'show each stage input/output'
    complete -c $c -n __algo_run_algo_pos -a '(algo complete algos 2>/dev/null)'
    complete -c $c -n '__fish_seen_subcommand_from run r; and not __algo_run_algo_pos' -a then -d 'chain the next stage'

    # pipe / judge / assert
    complete -c $c -n '__fish_seen_subcommand_from pipe' -s i -l input -r -F -d 'JSON input file'
    complete -c $c -n '__fish_seen_subcommand_from pipe' -a '(algo complete runnable 2>/dev/null)'
    complete -c $c -n '__fish_seen_subcommand_from judge' -a '(algo complete judged 2>/dev/null)'
    complete -c $c -n '__fish_seen_subcommand_from assert' -l expected -r -F -d 'expected JSON file'
    complete -c $c -n '__fish_seen_subcommand_from assert' -l actual -r -F -d 'actual JSON file'
    complete -c $c -n '__fish_seen_subcommand_from assert' -l comparator -x -a '(algo complete comparators 2>/dev/null)'
end
