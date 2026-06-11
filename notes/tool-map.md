**Claude Code:**
- What did Claude Code do this week that would have taken you a meaningful amount of time to do manually?
Built the full structure and architecture of the project and help to implement full overhauls of the UI.

- What did it get wrong? Where did it overshoot, misunderstand, or produce something you had to throw out?
It didn't get much wrong but sometimes it misunderstood my prompts and would create things I didn't ask for and it didn't ask for clarification on like when I added the pro version it just came up with new features for it without asking.

- When did you use `/plan` and did it change what you let it do?
I used plan almost everytime so I could review what Claude Code was about to do. Not really, most of the time I was confident in the plan and only made small changes.

- What would you put in CLAUDE.md at the start of a project, based on what you learned this week?
I think I would probably do it the same way, I was able to implement everything I planned to and then I just added more features that I wasn't expecting to from the start.

**The Cursor handoff:**
- When did you switch to Cursor and why?
I switched to Cursor pretty often, Cursor was easier for editing small details of code that weren't working or making small features like a notification pop up, It was also easier to run the code locally and push to github on Cursor tbh.

- Was it the right call? Give a specific example where Cursor did something better.
Yeah I think so it made me work a lot faster not having to rely on Claude for every single thing and being able to trouble shoot on Cursor is much better.

- Is there anything you did in Cursor that you wish Claude Code could have done?
No, Claude Code could've done everything but some things just make more sense for Cursor.

**The Claude API:**
- What is your `system` prompt doing in your project? Could you explain it to someone who has never seen Claude before?
The system prompt is telling the api to only respond in a specfied format to breakdown how to think through LSAT questions and explain them in simple terms. I could explain it to people who have never seen claude before. 

- Write out your system prompt here. Then write a version that's twice as specific. Which one would produce better results and why?
My system prompt tells Claude to respond only to LSAT-related messages using a fixed structured format (Question Type, Core Skill, Step-by-Step Strategy, Common Trap, Memory Cue), evaluate the student's answer if one is given, and append a hidden RATIO_META tag for progress tracking. A twice-as-specific version would add examples of what each section should look like for each question type, specify tone more precisely (e.g. "address the student directly, second person, no passive voice"), and define exactly when to mark a result "incorrect" vs "neutral" — that version would produce more consistent outputs because there'd be less room for Claude to interpret the instructions differently on each call.

- How is calling the API directly different from using Claude Chat? What does that difference give you?
Calling the API directly means I control the system prompt, the message history, what gets sent, and what happens with the response — Claude Chat is just a fixed interface with no customization. That difference is what lets me inject weak-area context, parse the RATIO_META tag out of every reply, store chat history per user, and enforce the structured breakdown format across the whole app.

- If you used streaming, what was the user experience difference? If you didn't, why not?
I didn't use streaming — the responses come back as a single chunk and render all at once, which works fine for the structured breakdown format since it only makes sense to display it when it's complete anyway.

**Across the full toolkit so far — Claude Chat, Cursor, Claude Code:**
- Give each tool one sentence: what it's actually for
Claude Chat is for quick one-off questions and brainstorming when you don't have a codebase open. Cursor is for fast in-editor edits, debugging, and running/pushing code without leaving your IDE. Claude Code is for building out whole features or overhauling large parts of a project where the context of the entire codebase matters.

- Which tool do you reach for first when starting a new project?
Claude Code — it can scaffold the whole structure and architecture from scratch in a way that Cursor and Claude Chat can't really match.

- What are you still uncertain about?
I'm still not totally sure when it makes more sense to break a big feature into multiple Claude Code prompts vs. just handing it everything at once, and I don't have a great feel yet for how much context Claude Code is actually retaining across a long session.
