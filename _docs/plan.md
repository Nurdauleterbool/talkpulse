# TalkPulse: Project Plan

Working name: **TalkPulse** (can be renamed).

## Idea

A tool for collecting feedback from the audience during a talk or defense.
The presenter sees where the audience got lost, and after the talk gets
structured feedback from the listeners.

## Users

- **Presenter**: a student presenting a project or defending it in class.
  Has an account, creates and runs the session.
- **Listener**: a classmate or teacher in the audience. Joins from a phone
  browser, no account needed.

## Joining a session

- The presenter creates a session and gets a QR code and a link.
- Listeners scan the QR code or open the link on their phone.
- No listener account. A listener enters a name or ticks "anonymous".
- Names are shown by default; each listener can choose to stay anonymous.

## Session lifecycle

1. Presenter creates a session (title of the talk).
2. Presenter presses **Start talk**: live reactions open, the timeline starts.
3. Presenter presses **End talk**: live reactions close, the feedback form
   opens for 10 minutes.
4. After 10 minutes the session closes automatically.
5. Presenter opens the results.

## Live reactions (during the talk)

Five fixed reactions, one tap each:

- Unclear
- Too fast
- Too slow
- Great point
- I have a question

Each tap is stored with its time offset from the moment "Start talk" was pressed.

### What the presenter sees during the talk

Only a simple signal, not details: for example, a color bar that turns red
when many listeners tap "Unclear" in a short period. Full details are
available only after the talk.

## Feedback form (after the talk)

Short, should take under a minute:

- Four ratings from 1 to 5: content, delivery, slides, answers to questions
- Text field: "What worked well"
- Text field: "What to improve"

## Results (after the talk)

- Timeline of reactions by minute, so the presenter sees where the audience
  got lost
- Average rating per criterion
- List of comments (author name, or "Anonymous")

## Out of scope for the first version

- Live results visible to the audience (only the presenter sees them)
- Export of the report (PDF or text file)
- Teacher view that compares many presentations
- Built-in audio or video recording of the talk
- Listener accounts or history of a listener's feedback across sessions
- Native mobile apps (the tool is a web app that works in a phone browser)

## To decide next

- Tech stack and architecture (not chosen yet)
