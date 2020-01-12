set -o noglob

# Print the name of the fastest known suitable installed Python interpreter.
fastest_python() {(
    if can_use_pypy; then
        echo 'pypy3'
    else
        echo 'python3'
    fi
)}

# Return 0 (success) if a suitable version of PyPy is installed.
can_use_pypy() {(
    set -o nounset
    if ! type pypy3 >/dev/null 2>&1; then
        return 1
    fi

    i=0
    for word in $(pypy3 --version); do
        if [ $i = 1 ]; then
            break
        fi
        if [ "$word" != 'Python' ]; then
            return 1
        fi
        i=1
    done

    IFS="."
    i=0
    for part in ${word-}; do
        if [ $i = 1 ]; then
            break
        fi
        if [ "$part" -ne 3 ] 2>/dev/null; then
            return 1
        fi
        i=1
    done

    [ "${part-}" -ge 6 ] 2>/dev/null
)}
