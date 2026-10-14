# Legacy Project Modernization: A Simple Guide

## What is a "legacy project"?

An old codebase that still runs in production. Usually:

- The people who wrote it have left
- The documentation is missing or out of date
- Nobody is 100% sure what every part does

## What kind of work are we doing?

1. Upgrade Same language, newer version
   (e.g. Java 8 → Java 21, Angular 12 → Angular 18)
2. Change language Rewrite in a different language
   (e.g. Java → Python, .NET → Node.js)
3. Change framework or database
   (e.g. Flask → FastAPI, Angular → React, MySQL → Postgres)

In all three cases, the goal is the same:
👉 The new system must behave exactly like the old one
(unless we decide on purpose to change something).

## Golden rule

The code is the only thing you can fully trust.
Old docs, comments and "I think it works like this" can be wrong.
Always check them against the code.

# The 7 Steps

## Step 0: Make a list of everything

Before reading the logic, list what the system has:

- APIs / endpoints (what other systems call)
- Settings (config files, environment variables)
- Database tables
- Other systems it talks to (payment gateway, email service, etc.)
- Background jobs (things that run on a schedule)

Write down the numbers, e.g. "120 APIs, 45 tables, 8 jobs".
Why? So you know when you're finished. 120 of 120 = done.

## Step 1: Write documentation by reading the code

Use an AI skill (like documenting-legacy-codebases) to help.

- For APIs, settings and database tables: document EVERYTHING.
  Other systems depend on these. Missing one = something breaks.
- For internal logic: just explain what it does, in plain words.
  e.g. "Deleted orders are hidden, not removed. Reports skip them."
- Unused code: if nothing calls it, mark it as unused. Don't migrate it.
- Weird behaviour or possible bugs: write them in a separate list.
  Don't fix anything yet.

## Step 2: Write tests that record how it works today

Think of it like taking a photo of the system's behaviour.

- Send a request → save the response
- Do an action → save what changed in the database

Test from the outside (calling APIs), not inside the code.
Why? Java tests can't run on Python code. But an API test
works on both the old and new system.

These tests must pass on the OLD system first.
Later, the NEW system must pass the same tests.

## Step 3: Turn the docs into spec-kit files

1. constitution The ground rules.
   e.g. "Don't change any API without approval."
2. spec.md WHAT the system does. (From your Step 1 docs.)
   This stays the same no matter which language we move to.
3. clarify What are ambiguous
   This will help identify missing, confusing requirements
4. plan.md HOW we'll build it. (Language, framework, database.)
   This is the part that changes per project.
5. tasks Small pieces of work, created from the plan.
   The tiny tasks are ready to build

## Step 4: Decide what to do with the weird stuff

Go through your list of weird behaviour and possible bugs from Step 1.
For each one, decide with your lead:

- Keep it (other systems depend on it)
- Fix it (it's a real bug and nobody relies on it)
- Later (fix after the migration is done)
  Write the decision down. Never "quietly fix" things during a rewrite.

## Step 5: Move one piece at a time

Don't rewrite everything and switch over in one day. That's risky.
Instead:

- Pick one part (e.g. "user login")
- Build it in the new system
- When its tests pass, send its traffic to the new system
- Repeat for the next part
  The old and new systems run side by side until everything is moved.

If the database is changing (e.g. MySQL → Postgres):

- Copy the data over
- Check it: same number of rows, same values
- Treat this as its own task. It's often harder than the code.

## Step 6: Check everything, then switch off the old system

- Run all the Step 2 tests on the new system. All must pass.
- Check speed and errors are as good as or better than before.
- Keep the old system available for a while, just in case.
- Turn it off only when the new one has been stable.

# Quick Summary

0. List everything → know what "done" looks like
1. Document from code → understand it
2. Record behaviour (tests) → have a way to check
3. Write spec-kit files → plan the new system
4. Decide on weird stuff → no surprises
5. Move piece by piece → lower risk
6. Check, then switch off → safe finish
