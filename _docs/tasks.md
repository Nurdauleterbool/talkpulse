# Backlog

## 1. Set up an empty Django project with a passing test
Goal: A Django project that installs, runs, and has one passing test.
Description: Create the Django project and an app for the sessions, add dependencies in `pyproject.toml`, and add a home page test that checks the page returns 200. Document the install, run, and test commands in `AGENTS.md`.

## 2. Presenter account and session creation
Goal: A presenter can sign up, log in, and create a talk session that gets a join link and a QR code.
Description: Add presenter registration and login with Django auth. A logged-in presenter creates a session with a talk title and sees its page with the join link and a QR code. Listeners do not need accounts.

## 3. Listener join page
Goal: A listener can open the join link on a phone and enter the session with a name or as anonymous.
Description: The join link opens a mobile-friendly page. The listener enters a name or ticks "anonymous", and is then taken to the session screen. The stored listener keeps the name by default, or is marked anonymous.

## 4. Start talk and End talk lifecycle
Goal: The presenter controls the session state with Start talk and End talk, and the session closes automatically after the form window.
Description: A session has the states waiting, live, form open, and closed. "Start talk" moves it to live and records the start time. "End talk" moves it to form open. The form stays open for 10 minutes, after which the session is closed.

## 5. Live reactions and signal bar
Goal: During a live session, listeners can tap five reactions and the presenter sees a simple signal.
Description: Listeners see five buttons: Unclear, Too fast, Too slow, Great point, I have a question. Each tap is stored with its time offset from the start of the talk. The presenter sees only a color bar that turns red when many listeners tap "Unclear" in a short period, with no detailed numbers.

## 6. Post-talk feedback form
Goal: While the form is open, a listener can submit ratings and comments once.
Description: The form has four ratings from 1 to 5 (content, delivery, slides, answers to questions) and two text fields, "What worked well" and "What to improve". A listener can submit it once per session. It is not available before End talk or after the session closes.

## 7. Results page for the presenter
Goal: After the talk, the presenter can open a results page with the reaction timeline, average ratings, and comments.
Description: The page shows the number of reactions per minute by type, the average rating per criterion, and the list of comments with the author name or "Anonymous". Only the presenter who owns the session can open it.
