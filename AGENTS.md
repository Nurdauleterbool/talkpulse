# TalkPulse

Django web app that collects audience feedback during a student talk or defense.
Product spec: `_docs/plan.md`.

## Commands

- `uv sync` - install dependencies
- `uv run pytest` - the whole suite
- `uv run pytest tests/test_home.py` - one test file
- `uv run python manage.py runserver` - run the app locally

## Rules

- Dependencies are added in `pyproject.toml`. Do not add one without asking
- Tasks are GitHub issues. Work on one issue at a time
- Commit regularly

## Documents

- `_docs/plan.md` - what we are building
- `_docs/process.md` - how work is organized, read it at the start of every session
- `_docs/task-template.md` - the template for a groomed issue
- `_docs/team/` - role descriptions (PM, software engineer, QA)
