# Chat brainstorm: TalkPulse

Note: this file is a reconstructed summary of the brainstorm, written from
`_docs/plan.md`, `_docs/tasks.md` and the decisions made while planning.
It is not a word-for-word transcript. The original chat is linked below.

Original chat: https://claude.ai/share/16f1806b-477a-4c2f-9c1a-b77d2c440683

## Problem

During a talk or a defense, the presenter cannot see where the audience got
lost. After the talk, feedback is vague or never collected.

## Idea

TalkPulse: a web app that collects audience feedback during a student talk
and right after it.

- During the talk: listeners send quick reactions, the presenter sees only a
  simple signal.
- After the talk: listeners fill a short form, the presenter gets structured
  results.

## Users

- Presenter: has an account, creates and runs the session.
- Listener: joins from a phone by QR code or link, no account, may stay
  anonymous.

## Decisions and why

- Listeners need no account, so joining takes seconds.
- Names are shown by default, anonymity is a choice of each listener.
- Five fixed reactions (Unclear, Too fast, Too slow, Great point, I have a
  question) instead of free text, so a tap takes one second.
- During the talk the presenter sees only a color bar, not details, so the
  presenter is not distracted. Details come after the talk.
- The feedback form is short (four ratings 1-5, two text fields), under a
  minute, and stays open for 10 minutes after End talk.
- Each reaction is stored with its time offset from Start talk, so the results
  can show a timeline by minute.

## Out of scope for the first version

- Live results visible to the audience
- Export of the report (PDF or text)
- Teacher view comparing many presentations
- Audio or video recording of the talk
- Listener accounts or history across sessions
- Native mobile apps

## Backlog

1. Empty Django project with a passing test
2. Presenter account and session creation (join link and QR code)
3. Listener join page
4. Start talk and End talk lifecycle
5. Live reactions and signal bar
6. Post-talk feedback form
7. Results page for the presenter

The first plan had duplicated issues (#2-#5), which were closed as duplicates.
Seven tasks were kept in the backlog.

## Tech stack

Django with SQLite, pytest and pytest-django, uv for dependencies, segno for
the QR code. Tasks are tracked as GitHub issues, worked one at a time through
PM, engineer and QA roles (see `_docs/process.md`).
