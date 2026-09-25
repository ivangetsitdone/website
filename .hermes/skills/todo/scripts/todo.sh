#!/usr/bin/env bash
# The website to-do list, kept as this repository's GitHub issues.
#
#   todo.sh                            list open items
#   todo.sh add "<title>" "<details>"  add one; a (dev) title is labelled for the developer
#   todo.sh edit <n> "<title>" "<details>"
#   todo.sh note <n> "<text>"
#   todo.sh done <n>
set -euo pipefail
cd "$(dirname "$0")/../../../.."

action=${1:-list}

case "$action" in
  list)
    gh issue list --state open --limit 40 \
      --json number,title,labels \
      --jq '.[] | "#\(.number)  \(.title)\(if (.labels | map(.name) | index("dev")) then "   [developer]" else "" end)"'
    ;;
  add)
    title=${2:?a title is required}
    body=${3:-}
    [ ${#title} -le 90 ] || { echo "the title is ${#title} characters; keep it under 90 and put the rest in the details" >&2; exit 2; }
    label=()
    case "$title" in '(dev)'*) label=(--label dev) ;; esac
    gh issue create --title "$title" --body "$body" "${label[@]}"
    ;;
  edit)
    number=${2:?an item number is required}
    title=${3-}
    body=${4-}
    # An item already marked for the developer stays that way.
    existing=$(gh issue view "$number" --json title --jq .title)
    case "$existing" in '(dev)'*) case "$title" in ''|'(dev)'*) ;; *) title="(dev) $title" ;; esac ;; esac
    args=()
    [ -n "$title" ] && args+=(--title "$title")
    [ -n "$body" ] && args+=(--body "$body")
    [ ${#args[@]} -gt 0 ] || { echo "nothing to change: give a title, details, or both" >&2; exit 2; }
    gh issue edit "$number" "${args[@]}"
    ;;
  note)
    gh issue comment "${2:?an item number is required}" --body "${3:?some text is required}"
    ;;
  done)
    gh issue close "${2:?an item number is required}"
    ;;
  *)
    echo "unknown action: $action (expected list, add, edit, note or done)" >&2
    exit 2
    ;;
esac
