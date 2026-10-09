"""
evaluate.py  -  GIVES THE CHATBOT A SCORE OUT OF 10
===================================================

"It seems to work" isn't good enough for a real company. So we test the bot
like a student: 10 questions where we already know the right answer.

eval_questions.csv has three columns:
- question:      what we ask
- must_include:  a word the correct answer must contain (e.g. "14" for 14 days).
                 Several accepted words can be separated by | (e.g. "one|1").
- should_answer: "yes" if the answer IS in the documents,
                 "no" if it ISN'T - then the bot passes only if it says "I don't know"

The "no" questions are the important ones: they test that the bot refuses
instead of making something up.
"""

import time
from pathlib import Path

import pandas as pd

from answer import answer_question

QUESTIONS_FILE = Path(__file__).parent / "eval_questions.csv"
PAUSE_SECONDS = 5      # small pause between questions so we stay inside the free tier's per-minute limit


def did_it_pass(row, result):
    """Decide pass or fail for one question."""
    if str(row["should_answer"]).strip().lower() == "no":
        return not result["found"]                        # pass = it admitted it doesn't know
    accepted = [word.strip().lower() for word in str(row["must_include"]).split("|")]
    return result["found"] and any(word in result["answer"].lower() for word in accepted)


def run_evaluation(report=print):
    """
    Ask every question, mark it pass or fail, and return (score, results_table).
    `report` receives progress messages, e.g. "3/10 ...".
    """
    questions = pd.read_csv(QUESTIONS_FILE).fillna("")
    rows = []
    for number, row in questions.iterrows():
        report(f"{number + 1}/{len(questions)}: {row['question']}")
        result = answer_question(row["question"])
        passed = did_it_pass(row, result)
        rows.append({
            "question": row["question"],
            "expected": row["must_include"] if row["should_answer"] == "yes" else "should say I don't know",
            "bot_answer": result["answer"],
            "passed": "PASS" if passed else "FAIL",
        })
        if number < len(questions) - 1:
            time.sleep(PAUSE_SECONDS)
    table = pd.DataFrame(rows)
    score = int((table["passed"] == "PASS").sum())
    return score, table


if __name__ == "__main__":
    score, table = run_evaluation()
    print(table.to_string(index=False))
    print(f"\nScore: {score}/{len(table)}")
