#!/usr/bin/env bash
# What has changed on the website lately, and whether it has reached the live site.
set -euo pipefail
cd "$(dirname "$0")/../../../.."

echo "ON DEV (https://dev.ivangetsitdone.com) — saved here, not yet published"
if git diff --quiet HEAD -- app frontend; then
  echo "  nothing unpublished"
else
  git diff --stat HEAD -- app frontend | sed 's/^/  /'
fi

echo
echo "WAITING — published and being tested"
gh pr list --state open --json number,title,createdAt \
  --jq '.[] | "  #\(.number)  \(.title)"' 2>/dev/null || echo "  (could not reach GitHub)"

echo
echo "PUBLISHED — live on https://ivangetsitdone.com"
gh run list --workflow=deploy.yml --branch main --limit 5 \
  --json conclusion,displayTitle,createdAt \
  --jq '.[] | "  \(.createdAt[0:16] | sub("T"; " "))  \(if .conclusion == "success" then "published" elif .conclusion == "failure" then "FAILED" else .conclusion end)  \(.displayTitle)"' \
  2>/dev/null || echo "  (could not reach GitHub)"
