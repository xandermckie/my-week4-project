"""Quiz mode engine — selects questions, checks answers, records results."""

import os
import random

import anthropic

SAMPLE_QUESTIONS = [
    {
        "type": "Weaken",
        "stimulus": (
            "Studies show that students who attend tutoring sessions score higher on standardized tests. "
            "Therefore, tutoring causes higher test scores."
        ),
        "question": "Which of the following, if true, most weakens the argument above?",
        "choices": {
            "A": "Students who attend tutoring also tend to study more independently.",
            "B": "Tutoring sessions are expensive and not available to all students.",
            "C": "Some students who do not attend tutoring also score very high.",
            "D": "The studies were conducted across multiple countries.",
        },
        "correct": "A",
        "explanation": (
            "Choice A weakens the argument by introducing an alternative cause — "
            "the increased independent study, not the tutoring, could be driving the score gains."
        ),
    },
    {
        "type": "Assumption",
        "stimulus": (
            "The law school requires applicants to score in the 90th percentile on the LSAT. "
            "Maria scored in the 92nd percentile. Therefore, Maria will be admitted."
        ),
        "question": "The argument above assumes which of the following?",
        "choices": {
            "A": "Maria applied to only one law school.",
            "B": "The LSAT score is the only admission criterion.",
            "C": "Scoring above the 90th percentile guarantees admission.",
            "D": "Maria prepared extensively for the LSAT.",
        },
        "correct": "B",
        "explanation": (
            "The argument jumps from meeting one criterion (LSAT score) to being admitted. "
            "This only works if the LSAT score is the sole criterion — choice B."
        ),
    },
    {
        "type": "Strengthen",
        "stimulus": (
            "A city health department claims that installing more streetlights in a neighborhood "
            "reduces nighttime crime. They point to a 20% drop in reported crimes after new lights "
            "were installed last year."
        ),
        "question": "Which of the following, if true, most strengthens the argument?",
        "choices": {
            "A": "The police department also increased patrols in the same neighborhood last year.",
            "B": "Crime rates in comparable neighborhoods without new lights remained unchanged.",
            "C": "Some residents complained that the new lights were too bright.",
            "D": "The streetlights were installed in October, which has shorter days.",
        },
        "correct": "B",
        "explanation": (
            "Choice B strengthens the causal claim by providing a control group — nearby neighborhoods "
            "without lights saw no drop, making it more likely the lights caused the reduction."
        ),
    },
    {
        "type": "Flaw",
        "stimulus": (
            "Everyone who has ever won a marathon trained for at least six months beforehand. "
            "Carlos trained for seven months. Therefore, Carlos will win the next marathon."
        ),
        "question": "The reasoning above is flawed because it",
        "choices": {
            "A": "relies on an unrepresentative sample of marathon winners.",
            "B": "treats a necessary condition as if it were a sufficient condition.",
            "C": "fails to consider that Carlos may not run in the marathon.",
            "D": "assumes that training duration is the only factor in winning.",
        },
        "correct": "B",
        "explanation": (
            "Training for six months is necessary to win, but the argument treats it as sufficient. "
            "Many people who train still do not win — choice B identifies this classic necessary/sufficient flaw."
        ),
    },
    {
        "type": "Inference",
        "stimulus": (
            "All first-year associates at the firm must attend the orientation seminar. "
            "No one who attended the orientation seminar failed the bar exam. "
            "Jordan is a first-year associate at the firm."
        ),
        "question": "Which of the following can be properly concluded from the statements above?",
        "choices": {
            "A": "Jordan will become a partner at the firm.",
            "B": "Jordan attended the orientation seminar.",
            "C": "Jordan did not fail the bar exam.",
            "D": "All first-year associates pass the bar exam.",
        },
        "correct": "C",
        "explanation": (
            "Jordan must attend the seminar (premise 1). No seminar attendee failed the bar (premise 2). "
            "Therefore Jordan did not fail the bar — choice C follows necessarily from both premises."
        ),
    },
    {
        "type": "Main Point",
        "stimulus": (
            "Critics argue that social media increases loneliness. However, research shows that users "
            "who engage actively — posting and commenting rather than passively scrolling — report "
            "stronger social connections. Passive consumption, not social media itself, is the problem."
        ),
        "question": "Which of the following best expresses the conclusion of the argument?",
        "choices": {
            "A": "Social media should be redesigned to discourage passive scrolling.",
            "B": "Active social media use is associated with stronger social connections than passive use.",
            "C": "Social media does not cause loneliness; passive use of it does.",
            "D": "Critics of social media have misunderstood the relevant research.",
        },
        "correct": "C",
        "explanation": (
            "The argument concedes that passive use is harmful but argues social media itself is not the "
            "cause. Choice C precisely captures the main conclusion without overstating it."
        ),
    },
    {
        "type": "Parallel Reasoning",
        "stimulus": (
            "All mammals are warm-blooded. Dolphins are mammals. Therefore, dolphins are warm-blooded."
        ),
        "question": "Which of the following most closely parallels the reasoning above?",
        "choices": {
            "A": "Some birds can fly. Penguins are birds. Therefore, penguins can fly.",
            "B": "All contracts require consideration. This agreement has consideration. Therefore, this agreement is a contract.",
            "C": "All registered voters are citizens. Ahmed is a citizen. Therefore, Ahmed is a registered voter.",
            "D": "All felonies are crimes. Robbery is a felony. Therefore, robbery is a crime.",
        },
        "correct": "D",
        "explanation": (
            "The original uses: All A are B; X is A; therefore X is B. "
            "Choice D matches exactly: All felonies are crimes; robbery is a felony; therefore robbery is a crime."
        ),
    },
    {
        "type": "Principle",
        "stimulus": (
            "A journalist published a story that was later found to contain a factual error. "
            "The error was minor and did not change the story's central conclusion. "
            "The editor chose not to issue a correction."
        ),
        "question": "Which principle, if established, most closely conforms to the editor's decision?",
        "choices": {
            "A": "Corrections should be issued whenever any factual error appears in print.",
            "B": "Minor errors that do not affect a story's conclusion do not require correction.",
            "C": "Editors should defer all correction decisions to the original journalist.",
            "D": "Stories should be retracted whenever they contain factual errors.",
        },
        "correct": "B",
        "explanation": (
            "The editor's decision was that the minor, non-material error did not warrant a correction. "
            "Choice B states exactly the principle that would justify this action."
        ),
    },
    {
        "type": "Resolve",
        "stimulus": (
            "A university found that students who live on campus graduate at higher rates than students "
            "who commute. Yet the university also found that commuter students have higher GPAs "
            "on average than on-campus residents."
        ),
        "question": "Which of the following, if true, best reconciles the apparent discrepancy?",
        "choices": {
            "A": "On-campus housing is more expensive than off-campus apartments.",
            "B": "Commuter students are more likely to drop out for financial reasons unrelated to academic performance.",
            "C": "On-campus students have greater access to extracurricular activities.",
            "D": "GPA is the most important factor universities consider when awarding degrees.",
        },
        "correct": "B",
        "explanation": (
            "The paradox: commuters have higher GPAs but lower graduation rates. "
            "Choice B resolves this — commuters drop out for financial reasons, not academic ones, "
            "explaining why high GPA doesn't translate into higher graduation rates for them."
        ),
    },
    {
        "type": "Reading Comprehension",
        "stimulus": (
            "The doctrine of promissory estoppel holds that a promise may be enforceable even without "
            "consideration if the promisee reasonably relied on it to their detriment. Courts have "
            "applied this doctrine cautiously, requiring that reliance be both reasonable and foreseeable "
            "by the promisor. Critics argue the doctrine undermines contract law's certainty, while "
            "proponents contend it prevents unjust outcomes when rigid rules would produce unfairness."
        ),
        "question": "According to the passage, which of the following is required for promissory estoppel to apply?",
        "choices": {
            "A": "The promise must be supported by consideration.",
            "B": "The promisee's reliance must be both reasonable and foreseeable by the promisor.",
            "C": "A court must find that the promisor acted in bad faith.",
            "D": "The promisee must have suffered a financial loss greater than the value of the promise.",
        },
        "correct": "B",
        "explanation": (
            "The passage states courts require that reliance be 'both reasonable and foreseeable by the promisor.' "
            "Choice B restates this condition directly. Choice A is wrong — the doctrine applies precisely when "
            "there is no consideration."
        ),
    },
]


def get_question(question_type: str | None = None) -> dict:
    """Select a quiz question, optionally filtered by type.

    Args:
        question_type: If provided, only return questions of this type.

    Returns:
        A question dict with keys: type, stimulus, question, choices, correct, explanation.
    """
    pool = SAMPLE_QUESTIONS
    if question_type:
        pool = [q for q in SAMPLE_QUESTIONS if q["type"] == question_type] or SAMPLE_QUESTIONS
    return random.choice(pool)


def check_answer(question: dict, submitted: str) -> dict:
    """Evaluate a submitted answer choice against the correct answer.

    Args:
        question: The question dict as returned by get_question().
        submitted: The letter choice submitted by the student (e.g. "A").

    Returns:
        A dict with keys: is_correct (bool), correct (str), explanation (str).
    """
    is_correct = submitted.upper() == question["correct"]
    return {
        "is_correct": is_correct,
        "correct": question["correct"],
        "explanation": question["explanation"],
    }
