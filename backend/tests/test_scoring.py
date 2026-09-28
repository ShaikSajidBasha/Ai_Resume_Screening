from app.agents import scoring_agent


def test_overall_score_weighted_average():
    sub_scores = {
        "ats_score": 80,
        "skill_score": 70,
        "keyword_score": 60,
        "experience_score": 90,
        "education_score": 100,
        "resume_quality_score": 50,
    }
    overall = scoring_agent.compute_overall_score(sub_scores)
    expected = 80 * 0.25 + 70 * 0.30 + 60 * 0.15 + 90 * 0.15 + 100 * 0.10 + 50 * 0.05
    assert round(expected, 2) == overall


def test_status_thresholds():
    assert scoring_agent.resolve_status_label(90) == "Strong Match"
    assert scoring_agent.resolve_status_label(70) == "Moderate Match"
    assert scoring_agent.resolve_status_label(50) == "Needs Improvement"
    assert scoring_agent.resolve_status_label(10) == "Low Match"
