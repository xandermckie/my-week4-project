# CLAUDE.md

## Project Overview
This project helps users breakdown LSAT questions and prepare for the exam by hekping them notice patterns, think through common problem structures, and get faster at spotting the common question forms. The application will help keep track of a user's weak areas, notes, and study schedule in order to keep them on track and give them better improvement than standard tutoring would be able to provide due to their time and price constraints. The people who use this should be undegraduate law students or other's preparing to take the LSAT exam in the coming months.

## Architecture
The major components of this project would be the housing of the claude api, creating the user interface, and keeping user's data in a json file.
We should be storing api keys in an extremely safe environment, only calling them when needed and keeping the rate limits under control, encrypting user data, and only having all functions route to the user interface.

## Key Decisions
- Using JSON instead of SQLite because I have more experience using JSON in the previous project and haven't really touched SQLite before.
- Flask instead of FastAPI for the same reason listed above.

## Constraints
[Hard rules Claude Code must follow]
- Never commit .env or any file containing API keys
- Error handling must be explicit — no bare except clauses
- Every function must have a docstring
- User data must be encrypted and hashed
- rate limiting must be in place for all api calls
- any reponses that can be cached should be

## Open Questions
[Things not decided yet — Claude Code can raise these]
How to implement calendar integration?

Best way for responses to be return and analyzed?

Is it possible for anything on the site to be cached or hardcoded when we run into API issues, just as backup?|

What is the best way to make this useful for LSAT students and differentiate from just using claude as a chat bot?

How to keep a longer context using recurring chat compression and context documents?

How should the tutoring and test environments take place?