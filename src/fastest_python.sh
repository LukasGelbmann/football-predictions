set -o noglob

set_python() {
    PYTHON="python3"

    ! type pypy3 >/dev/null 2>&1 && return

    i=0
    for word in $(pypy3 --version); do
        [ $i = 1 ] && break
        [ "$word" != "Python" ] && return
        i=1
    done

    IFS="."
    i=0
    for part in $word; do
        [ $i = 1 ] && break
        [ "$part" -ne 3 ] && return
        i=1
    done

    [ "$part" -ge 6 ] && PYTHON="pypy3"
}
