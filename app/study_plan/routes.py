"""Study plan blueprint routes."""

from datetime import date

from flask import flash, redirect, render_template, request, session, url_for

from app.analysis.weak_area_detector import get_ranked_weak_areas
from app.auth.helpers import login_required
from app.storage import load_session, load_user, save_user
from app.study_plan import study_plan_bp
from app.study_plan.plan_generator import generate_study_plan


def _exam_passed(exam_date_str: str | None) -> bool:
    """Return True if the stored exam date is today or in the past."""
    if not exam_date_str:
        return False
    try:
        exam = date.fromisoformat(exam_date_str)
        return exam <= date.today()
    except ValueError:
        return False


@study_plan_bp.route("/study-plan", methods=["GET", "POST"])
@login_required
def plan():
    """Render or generate a personalized study plan.

    Users get one plan generation and one free date correction.
    After both are used the plan is locked until the exam date passes.
    """
    email = session["email"]
    user = load_user(email)
    session_data = load_session(email)
    weak_areas = get_ranked_weak_areas(session_data)

    stored_plan = user.get("study_plan_content")
    fix_used = user.get("study_plan_fix_used", False)
    stored_exam_date = user.get("study_plan_exam_date")
    plan_expired = _exam_passed(stored_exam_date)

    # Reset if exam date has passed so they can generate a fresh plan.
    if plan_expired and stored_plan:
        user["study_plan_content"] = None
        user["study_plan_fix_used"] = False
        user["study_plan_exam_date"] = None
        save_user(email, user)
        stored_plan = None
        fix_used = False
        stored_exam_date = None

    if request.method == "POST":
        target_date = request.form.get("target_date") or user.get("target_exam_date")
        is_fix = request.form.get("is_fix") == "1"

        if stored_plan and fix_used:
            flash("You have already used your one plan correction. Your plan is locked until your exam date passes.")
            return redirect(url_for("study_plan.plan"))

        if stored_plan and not fix_used and not is_fix:
            # They somehow POSTed the generate form again without using the fix path.
            flash("You have already generated a plan. Use the date correction option if needed.")
            return redirect(url_for("study_plan.plan"))

        generated = generate_study_plan(weak_areas, target_date)
        user["study_plan_content"] = generated
        user["study_plan_exam_date"] = target_date
        if is_fix:
            user["study_plan_fix_used"] = True
        else:
            user["study_plan_fix_used"] = False
        save_user(email, user)
        return redirect(url_for("study_plan.plan"))

    return render_template(
        "study_plan/plan.html",
        weak_areas=weak_areas,
        generated_plan=stored_plan,
        target_date=stored_exam_date or user.get("target_exam_date"),
        fix_used=fix_used,
        has_plan=bool(stored_plan),
    )
