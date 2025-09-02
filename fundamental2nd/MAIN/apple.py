from flask import Flask, render_template, request

app = Flask(__name__)

def parse_input(form, name):
    val = form.get(name, "")
    if val == "":
        return None
    try:
        v = float(val)
        if 0 <= v <= 100:
            return v
    except:
        pass
    return None

def attendance_score(absences):
    if absences is None:
        return 100
    return max(0, 100 - 10*absences)

def period_grade(scores):
    """scores = [absences, quiz, requirements, recitation, exam]"""
    if all(s is None for s in scores[1:]):
        return None
    absences = scores[0] or 0
    quiz = scores[1] or 0
    req = scores[2] or 0
    rec = scores[3] or 0
    exam = scores[4] or 0
    attendance = attendance_score(absences)
    class_standing = 0.4*quiz + 0.3*req + 0.3*rec
    grade = 0.6*exam + 0.1*attendance + 0.3*class_standing
    return round(grade,2)

def overall_grade(prelim, mid, final):
    total_weight = 0
    grade = 0
    if prelim is not None:
        grade += prelim * 0.2
        total_weight += 0.2
    if mid is not None:
        grade += mid * 0.3
        total_weight += 0.3
    if final is not None:
        grade += final * 0.5
        total_weight += 0.5
    if total_weight == 0:
        return None
    return round(grade/total_weight,2)

def required_grades(prelim, mid, final, target):
    filled_total = 0
    empty_weights = {}
    if prelim is not None:
        filled_total += 0.2*prelim
    else:
        empty_weights['prelim'] = 0.2
    if mid is not None:
        filled_total += 0.3*mid
    else:
        empty_weights['mid'] = 0.3
    if final is not None:
        filled_total += 0.5*final
    else:
        empty_weights['final'] = 0.5

    req = {}
    if len(empty_weights) == 2:
        total_w = sum(empty_weights.values())
        needed = (target - filled_total)/total_w
        req['both'] = "Impossible" if needed>100 else round(needed,2)
    else:
        for period, w in empty_weights.items():
            needed = (target - filled_total)/w
            req[period] = "Impossible" if needed>100 else round(needed,2)
    return req

@app.route("/", methods=["GET","POST"])
def index():
    ctx = {
        "failed_due_absences": False,
        "prelim": None, "mid": None, "final": None,
        "overall": None,
        "req75": {}, "req90": {},
        "errors": []
    }

    if request.method == "POST":
        prelim_scores = [parse_input(request.form, n) for n in ["exam_absences","exam_quiz","exam_requirements","exam_recitation","exam_score"]]
        mid_scores = [parse_input(request.form, n) for n in ["mid_absences","mid_quiz","mid_requirements","mid_recitation","mid_score"]]
        final_scores = [parse_input(request.form, n) for n in ["final_absences","final_quiz","final_requirements","final_recitation","final_score"]]

        # Check for missing fields per period
        periods = {"Prelim": prelim_scores, "Midterm": mid_scores, "Final": final_scores}
        for name, scores in periods.items():
            filled = any(s is not None for s in scores)
            empty = any(s is None for s in scores)
            if filled and empty:
                ctx["errors"].append(f"Please fill out all fields for {name} before calculating.")

        # Fail if any period absences >=4
        for scores in [prelim_scores, mid_scores, final_scores]:
            if scores[0] is not None and scores[0] >= 4:
                ctx["failed_due_absences"] = True

        # Sequential input validation
        if not ctx["failed_due_absences"]:
            if any(mid_scores[1:]) and not any(prelim_scores[1:]):
                ctx["errors"].append("Please enter Prelim grades first before calculating Midterm.")
            if any(final_scores[1:]) and not any(prelim_scores[1:]):
                ctx["errors"].append("Please enter Prelim grades first before calculating Final.")
            if any(final_scores[1:]) and not any(mid_scores[1:]):
                ctx["errors"].append("Please enter Midterm grades first before calculating Final.")

        # Only calculate if no errors
        if not ctx["errors"] and not ctx["failed_due_absences"]:
            ctx["prelim"] = period_grade(prelim_scores)
            ctx["mid"] = period_grade(mid_scores)
            ctx["final"] = period_grade(final_scores)

            ctx["overall"] = overall_grade(ctx["prelim"], ctx["mid"], ctx["final"])

            ctx["req75"] = required_grades(ctx["prelim"], ctx["mid"], ctx["final"], 75)
            ctx["req90"] = required_grades(ctx["prelim"], ctx["mid"], ctx["final"], 90)

    return render_template("inch.html", **ctx)

if __name__ == "__main__":
    app.run(debug=True)
