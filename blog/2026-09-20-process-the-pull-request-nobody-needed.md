# The pull request nobody needed

**2026-09-20 · process**

This repository has exactly one committer. Every change so far has gone straight to `main`,
which is the correct amount of process for a one-person project and the exact habit that
breaks the first time somebody else shows up.

The pipeline, though, was built as if a team already existed: a `check` job that needs no
secrets, a `deploy` job guarded by `if: github.event_name != 'pull_request'`, and a
concurrency policy with different rules for branches and for `main`. All of that exists to
serve a workflow the repository has never actually used.

Which means it has never been tested. This post is the test — written on the branch it
describes, opened as the pull request it is about.

## Setup: what a pull request is *for*

It is worth being precise, because "we use PRs" covers at least four different jobs and
teams routinely adopt the ritual while getting none of them:

1. **A safe place to run the tests.** The change is executed somewhere that is not
   production, before anyone can merge it.
2. **A review surface.** Someone who did not write it reads it.
3. **A merge queue.** Two people changing the same thing find out before `main` does.
4. **A durable record.** Why this change, at this time, in the author's words.

Solo, (1) is the only one that pays for itself immediately — and only if CI actually runs
something meaningful. (2) and (3) are worth nothing until there is a second person, and
then they are worth almost everything. (4) is worth something the day you forget why.

The mistake is treating the ritual as the goal. A pull request that only runs a linter and
gets rubber-stamped has all four costs and none of the benefits.

## Buildup: what changes mechanically

Our workflow has three jobs. On a push to `main` all three run in order:

```
push ──► check ──► deploy ──► verify
         runner    droplet    runner
```

On a pull request, exactly one does:

```
pull_request ──► check
                 runner
```

That is a single line of YAML:

```yaml
deploy:
  needs: check
  if: github.event_name != 'pull_request'
```

Everything else follows from four decisions that are worth more than the line itself.

### `check` needs no secrets, on purpose

`check` builds the images, stands the whole stack up on the runner over plain HTTP, and
runs every suite against it. It never touches the droplet and reads no secret.

That is not tidiness. **GitHub does not give secrets to workflows triggered by pull requests
from forks** — and it is right not to, because a fork's branch is code you have not read,
and handing it `DEPLOY_KEY` would hand a stranger a root shell on your server. A `check`
job that needs a secret is a `check` job that cannot run on an outside contribution, which
means outside contributions arrive untested and reviewers become the only gate.

If you are building for a distributed team, design the test job to need nothing. Put the
credentials in the deploy job, where the trigger is a push to a protected branch and the
code has already been merged by someone with commit rights.

### Least privilege on the token you forgot you had

Every workflow run gets a `GITHUB_TOKEN`. Its default permissions are broader than most
pipelines need, and a compromised build step inherits them.

```yaml
permissions:
  contents: read
```

Nothing in this pipeline writes to the repository, so nothing needs write.

### Concurrency: cancel pull requests, never cancel a deploy

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

The group is per-ref, so a pull request and `main` never queue behind each other, and two
pull requests never queue behind each other either. The distinction that matters is the
second line:

- **On a pull request**, pushing a fixup should cancel the run for the commit you have just
  replaced. Nobody cares whether the version you already abandoned passed, and on a busy
  repository that is most of your runner minutes.
- **On `main`**, cancelling is dangerous. An interrupted deploy is a deploy that has
  replaced the app container and not yet checked whether it is healthy — the one state the
  whole pipeline exists to avoid.

There is a subtlety here that cost us a confused minute. `cancel-in-progress` governs the
run that is *already executing*. A newly queued run **always** cancels runs in its group
that are still *pending*, whatever that flag says. So on a busy `main` you will see
`cancelled` against intermediate commits. Nothing was interrupted and nothing was lost: the
deploy resets to the commit that triggered it, so the later run ships the skipped commit's
content too. We added a line to the troubleshooting docs, because a red-looking `cancelled`
next to your own commit is exactly the sort of thing that sends a new team member hunting.

### Branch protection is the part that is not in the repository

The `if:` guard stops a pull request from deploying. It does **not** stop anyone from
pushing straight to `main` and skipping review entirely — as this repository's entire
history demonstrates.

That control lives in GitHub's settings, not in a file: require a pull request before
merging, and require `check` to pass. It is the one piece of this that cannot be reviewed in
a diff, which makes it the one piece worth writing down.

## The part where tests replace a reviewer's memory

The most useful thing in our `check` job is not the browser suite. It is this, from
`tests/smoke.py`:

```python
REGULATED = ('remodel', 'sheetrock', 'drywall', 'tile', 'flooring', 'plumbing',
             'electrical', 'painting', 'shower', 'install', 'repair', 'retaining wall')
```

The business behind this site holds a business registration but no contractor's licence.
Oregon conditions the small-job exemption on *not advertising as a contractor*, so the site
may describe past work as experience and may not offer regulated trades. A test asserts that
those words never appear in the blocks that offer work, and that the disclosure appears on
every page.

That is a legal constraint encoded as a check. It is the clearest example I know of what CI
is genuinely better at than people: a reviewer who has read the licensing rules once, six
months ago, at eleven at night, will not reliably catch the word "install" in a new service
description. The test catches it every time, on every pull request, including from someone
who has never heard of the Oregon CCB.

**If your team has a rule that a reviewer is expected to remember, that rule is a test you
have not written yet.** Accessibility budgets, bundle size, forbidden imports, licence
headers, a naming convention — each of those is a comment thread you will have repeatedly
until you encode it once.

## Climax: opening the pull request

Everything above is a claim about what a pull request does here. Here is the experiment:
this post is committed to a branch called `blog/pr-workflow`, and that branch is opened as
a pull request against `main`.

Predictions, written before the run:

1. `check` runs and passes.
2. `deploy` is skipped — not failed, **skipped** — and the droplet is never contacted.
3. `verify` is skipped too, since it needs `deploy`.
4. The live site never changes, because nothing deployed.
5. Pushing a second commit to the branch cancels the first run rather than queueing it.

*Results follow in the next commit on this branch, which is itself prediction 5.*

## Recap

For a solo repository, a pull request buys you one thing — a rehearsal on a machine that is
not production — and you can get most of that by having CI run on pushes to `main`, as we
did for a week.

What it buys a distributed team is the other three, and the cost of retrofitting them is
mostly not the YAML. It is the habits: pushing to a branch instead of `main`, writing a
description someone else can act on, waiting for a check you used to skip.

The technical parts worth copying:

- **Make the test job need no secrets**, so it can run on forks, so outside contributions
  arrive already tested.
- **Cancel superseded pull-request runs; never cancel a deploy.** They are different risks
  and deserve different answers.
- **Pin what the automatic token may do.** `contents: read` until something needs more.
- **Branch protection is not in your repository.** Write down that it exists, because a
  future reader cannot infer it from any file.
- **Every rule you expect a reviewer to remember is a test you have not written.**

---

*The repository is [github.com/ivangetsitdone/website](https://github.com/ivangetsitdone/website).
The pipeline's reasoning is in [ADR-0010](../docs/adr/0010-continuous-deployment.md); the
previous post, [Eight seconds of 502](2026-09-20-deploy-eight-seconds-of-502.md), is how it
came to exist.*
