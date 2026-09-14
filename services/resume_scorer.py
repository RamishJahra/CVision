"""
CVision ATS Resume Scorer

This module calculates an ATS-readiness score for a resume.

The score measures how complete and well-structured the resume is
for automated screening.

It does NOT measure how suitable the applicant is for a particular job.
Job-specific matching will be handled separately.
"""


def get_score_label(score):
    """
    Convert the numerical score into a human-readable label.
    """

    if score >= 90:
        return "Excellent"

    if score >= 80:
        return "Very Good"

    if score >= 70:
        return "Good"

    if score >= 60:
        return "Fair"

    return "Needs Improvement"


# ==========================================================
# CONTACT INFORMATION
# Maximum: 10
# ==========================================================

def score_contact_information(parsed_data):

    score = 0
    recommendations = []

    # Name = 3
    if parsed_data.get("name"):

        score += 3

    else:

        recommendations.append(
            "Add your full name to the resume."
        )

    # Email = 4
    if parsed_data.get("email"):

        score += 4

    else:

        recommendations.append(
            "Add a professional email address."
        )

    # Phone = 3
    if parsed_data.get("phone"):

        score += 3

    else:

        recommendations.append(
            "Add a phone number to the resume."
        )

    return score, recommendations


# ==========================================================
# PROFESSIONAL SUMMARY
# Maximum: 10
# ==========================================================

def score_summary(parsed_data):

    summary = (
        parsed_data.get("summary")
        or ""
    ).strip()

    if not summary:

        return 0, [
            "Add a professional summary describing your background, skills, and career goals."
        ]

    word_count = len(
        summary.split()
    )

    # Strong summary
    if word_count >= 50:

        return 10, []

    # Good but could be improved
    if word_count >= 30:

        return 8, [
            "Consider expanding your professional summary with more relevant details."
        ]

    # Very short summary
    if word_count >= 15:

        return 6, [
            "Your professional summary is quite short. Add more information about your skills and career goals."
        ]

    return 4, [
        "Expand your professional summary to better describe your background and strengths."
    ]


# ==========================================================
# SKILLS
# Maximum: 20
# ==========================================================

def score_skills(parsed_data):

    skills = parsed_data.get(
        "skills",
        []
    )

    if not skills:

        return 0, [
            "Add relevant technical and professional skills."
        ]

    skill_count = len(skills)

    # 10+ skills
    if skill_count >= 10:

        return 20, []

    # 7-9 skills
    if skill_count >= 7:

        return 17, [
            "Consider adding a few more relevant skills to improve keyword coverage."
        ]

    # 4-6 skills
    if skill_count >= 4:

        return 13, [
            "Add more relevant technical and professional skills."
        ]

    # 1-3 skills
    return 8, [
        "Your resume contains relatively few detected skills. Add more relevant skills."
    ]


# ==========================================================
# EDUCATION
# Maximum: 15
# ==========================================================

def score_education(parsed_data):

    education = parsed_data.get(
        "education",
        []
    )

    if not education:

        return 0, [
            "Add your educational qualifications."
        ]

    valid_entries = 0

    for item in education:

        if not isinstance(item, dict):
            continue

        degree = (
            item.get("degree")
            or ""
        ).strip()

        institution = (
            item.get("institution")
            or ""
        ).strip()

        if degree and institution:

            valid_entries += 1

    if valid_entries >= 2:

        return 15, []

    if valid_entries == 1:

        return 12, []

    return 5, [
        "Provide clearer education details, including your degree and institution."
    ]


# ==========================================================
# WORK EXPERIENCE
# Maximum: 20
# ==========================================================

def score_experience(parsed_data):

    experience = parsed_data.get(
        "experience",
        []
    )

    if not experience:

        return 0, [
            "Add relevant work experience, internships, or practical experience if available."
        ]

    valid_entries = 0
    detailed_entries = 0

    for item in experience:

        if not isinstance(item, dict):
            continue

        title = (
            item.get("title")
            or ""
        ).strip()

        company = (
            item.get("company")
            or ""
        ).strip()

        details = item.get(
            "details",
            []
        )

        if title and company:

            valid_entries += 1

            if details:

                detailed_entries += 1

    # Multiple detailed experiences
    if valid_entries >= 2 and detailed_entries >= 2:

        return 20, []

    # Multiple experiences
    if valid_entries >= 2:

        return 17, [
            "Add more detailed responsibilities or achievements to your work experience."
        ]

    # One detailed experience
    if valid_entries == 1 and detailed_entries == 1:

        return 15, [
            "Consider adding more work experience, internships, or practical experience if available."
        ]

    # One basic experience
    if valid_entries == 1:

        return 12, [
            "Add responsibilities, achievements, or measurable results to your experience entry."
        ]

    return 5, [
        "Provide clearer job titles and company information."
    ]


# ==========================================================
# PROJECTS
# Maximum: 15
# ==========================================================

def score_projects(parsed_data):

    projects = parsed_data.get(
        "projects",
        []
    )

    if not projects:

        return 0, [
            "Add relevant projects to demonstrate your practical skills."
        ]

    valid_projects = 0
    detailed_projects = 0

    for project in projects:

        if not isinstance(project, dict):
            continue

        name = (
            project.get("name")
            or ""
        ).strip()

        details = project.get(
            "details",
            []
        )

        if name:

            valid_projects += 1

            if details:

                detailed_projects += 1

    # 3+ detailed projects
    if valid_projects >= 3 and detailed_projects >= 3:

        return 15, []

    # 3 projects
    if valid_projects >= 3:

        return 13, [
            "Add clearer descriptions and technologies used in your projects."
        ]

    # 2 projects
    if valid_projects == 2:

        return 11, [
            "Consider adding another relevant project and describe your contributions clearly."
        ]

    # 1 project with details
    if valid_projects == 1 and detailed_projects == 1:

        return 9, [
            "Consider adding more projects or expanding your project description."
        ]

    # 1 basic project
    if valid_projects == 1:

        return 7, [
            "Add a stronger description of your project and the technologies used."
        ]

    return 3, [
        "Provide clearer project information."
    ]


# ==========================================================
# CERTIFICATIONS
# Maximum: 5
# ==========================================================

def score_certifications(parsed_data):

    certifications = parsed_data.get(
        "certifications",
        []
    )

    if not certifications:

        return 0, [
            "Consider adding relevant certifications if you have any."
        ]

    if len(certifications) >= 2:

        return 5, []

    return 3, []


# ==========================================================
# ACHIEVEMENTS
# Maximum: 5
# ==========================================================

def score_achievements(parsed_data):

    achievements = parsed_data.get(
        "achievements",
        []
    )

    if not achievements:

        return 0, [
            "Add relevant academic, professional, competition, or other achievements if available."
        ]

    if len(achievements) >= 2:

        return 5, []

    return 3, []


# ==========================================================
# MAIN ATS SCORE FUNCTION
# ==========================================================

def calculate_resume_score(parsed_data):

    total_score = 0

    recommendations = []

    breakdown = []

    # ------------------------------------------------------
    # Contact Information
    # ------------------------------------------------------

    score, recs = score_contact_information(
        parsed_data
    )

    total_score += score

    recommendations.extend(
        recs
    )

    breakdown.append({
        "name": "Contact Information",
        "score": score,
        "max_score": 10
    })

    # ------------------------------------------------------
    # Professional Summary
    # ------------------------------------------------------

    score, recs = score_summary(
        parsed_data
    )

    total_score += score

    recommendations.extend(
        recs
    )

    breakdown.append({
        "name": "Professional Summary",
        "score": score,
        "max_score": 10
    })

    # ------------------------------------------------------
    # Skills
    # ------------------------------------------------------

    score, recs = score_skills(
        parsed_data
    )

    total_score += score

    recommendations.extend(
        recs
    )

    breakdown.append({
        "name": "Skills",
        "score": score,
        "max_score": 20
    })

    # ------------------------------------------------------
    # Education
    # ------------------------------------------------------

    score, recs = score_education(
        parsed_data
    )

    total_score += score

    recommendations.extend(
        recs
    )

    breakdown.append({
        "name": "Education",
        "score": score,
        "max_score": 15
    })

    # ------------------------------------------------------
    # Work Experience
    # ------------------------------------------------------

    score, recs = score_experience(
        parsed_data
    )

    total_score += score

    recommendations.extend(
        recs
    )

    breakdown.append({
        "name": "Work Experience",
        "score": score,
        "max_score": 20
    })

    # ------------------------------------------------------
    # Projects
    # ------------------------------------------------------

    score, recs = score_projects(
        parsed_data
    )

    total_score += score

    recommendations.extend(
        recs
    )

    breakdown.append({
        "name": "Projects",
        "score": score,
        "max_score": 15
    })

    # ------------------------------------------------------
    # Certifications
    # ------------------------------------------------------

    score, recs = score_certifications(
        parsed_data
    )

    total_score += score

    recommendations.extend(
        recs
    )

    breakdown.append({
        "name": "Certifications",
        "score": score,
        "max_score": 5
    })

    # ------------------------------------------------------
    # Achievements
    # ------------------------------------------------------

    score, recs = score_achievements(
        parsed_data
    )

    total_score += score

    recommendations.extend(
        recs
    )

    breakdown.append({
        "name": "Achievements",
        "score": score,
        "max_score": 5
    })

    # ------------------------------------------------------
    # Remove duplicate recommendations
    # ------------------------------------------------------

    unique_recommendations = []

    for recommendation in recommendations:

        if recommendation not in unique_recommendations:

            unique_recommendations.append(
                recommendation
            )

    # ------------------------------------------------------
    # Final result
    # ------------------------------------------------------

    return {
        "total_score": total_score,
        "label": get_score_label(
            total_score
        ),
        "breakdown": breakdown,
        "recommendations": unique_recommendations
    }