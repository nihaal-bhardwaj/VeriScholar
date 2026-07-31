# Team Workflow

## Repository workflow

All members work on a single branch:

```text
main
```

No separate member branches or `develop` branch are required at this stage. Members work one at a time, sequentially.

## Before a member starts working

The member must run:

```bash
git switch main
git pull origin main
git status
```

They must confirm in the team group that they have started and that nobody else should edit or push until they finish.

## While working

- Work only on the assigned module.
- Avoid unrelated changes.
- Do not change another member's module without coordination.
- Commit logical, understandable pieces of work.
- Never commit credentials or `.env`.
- Do not add large datasets or model files directly to Git.
- Run the relevant tests before pushing.

## Before pushing

Run:

```bash
git status
git pull --rebase origin main
```

Then run relevant verification:

### Backend changes

```bash
cd backend
python -m pytest
```

### Frontend changes

```bash
cd frontend
npm run lint
npm run build
```

Return to the root before committing when necessary.

## Commit and push

```bash
git add .
git commit -m "Clear description of completed work"
git push origin main
```

The member must then notify the team that the push is complete.

## Important rules

- Only one member works at a time.
- Always pull before beginning.
- Pull with rebase immediately before pushing.
- Never force-push.
- Never use `git reset --hard` on shared work unless the team leader explicitly approves it.
- Never delete another member's work to resolve a conflict.
- The `main` branch should remain runnable after every push.
- If tests fail, do not push until the reason is understood.
- Use clear commit messages.
- Keep commits reasonably small.
- Notify the team immediately if a conflict, broken build or accidental push occurs.

## Example sequence

1. Nihaal tells the team he is starting.
2. Nihaal pulls the latest main.
3. Everyone else pauses repository work.
4. Nihaal completes and tests the PDF parser update.
5. Nihaal pulls with rebase again.
6. Nihaal commits and pushes to main.
7. Nihaal tells the team the push is complete.
8. The next member pulls main and begins.
