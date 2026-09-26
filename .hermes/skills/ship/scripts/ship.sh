#!/usr/bin/env bash
# Publish what is on the development site to the live site.
#
#   bash .hermes/skills/ship/scripts/ship.sh "new home headline and phone number"
#
# Stages app/ and frontend/ by name, never everything: the tree is shared with the
# developer's assistant, which may have work in progress in it.
#
# The pull request merges with a merge commit, and local main is fast-forwarded onto the
# shipped commit before this returns. Together those keep the change on the development
# site while the tests run, and let the deploy bring the tree up to date afterwards with a
# plain fast-forward (ADR-0018).
set -euo pipefail

description=${1:-}
[ -n "$description" ] || { echo "usage: ship.sh '<what is being published>'" >&2; exit 2; }

cd "$(dirname "$0")/../../../.."

[ "$(git branch --show-current)" = main ] || {
  echo "the working copy is not on main; the developer needs to look at it" >&2; exit 1; }

git add app frontend
if git diff --cached --quiet; then
  echo "nothing to publish: app/ and frontend/ match what is already published" >&2
  exit 1
fi

echo "publishing:"
git diff --cached --stat

branch="hermes/$(date -u +%Y%m%d-%H%M%S)"
git switch -q -c "$branch"
git commit -q -m "site: ${description}"
git push -q -u origin "$branch"

url=$(gh pr create --base main --head "$branch" --title "site: ${description}" --body "Published from the development site by the owner's assistant.

Copy, branding and photographs only — everything under \`app/\` and \`frontend/\`. The full \`check\` job runs before this can merge.")
echo "opened $url"

# Local main follows the shipped commit, so the development site keeps showing it. After
# GitHub merges, origin/main is a fast-forward of this, which is what the deploy does.
git switch -q main
git merge -q --ff-only "$branch"
git branch -q -d "$branch"    # main contains it now; the copy on origin is the pull request

# The commit is pushed, so arming cannot merge anything the tests have not seen.
if gh pr merge --auto --merge "$url" >/dev/null 2>&1; then
  echo "armed to merge itself once the tests pass"
else
  echo "could not arm auto-merge; the pull request is waiting for someone to merge it"
fi

echo
echo "The tests take about two minutes and publishing about three more."
