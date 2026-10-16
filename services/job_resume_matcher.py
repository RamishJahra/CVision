
# services/job_resume_matcher.py

import re
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Normalize common alternative spellings without treating unrelated
# technologies as equivalent.
SKILL_ALIASES = {
    "sklearn": "scikit learn",
    "scikit-learn": "scikit learn",
    "js": "javascript",
    "node.js": "nodejs",
    "node js": "nodejs",
    "postgres": "postgresql",
    "postgres sql": "postgresql",
    "ms sql": "sql server",
    "mssql": "sql server",
    "c sharp": "c#",
    "cplusplus": "c++",
    "cpp": "c++",
    "dotnet": ".net",
    "asp.net core": "asp net core",
    "machine-learning": "machine learning",
    "deep-learning": "deep learning",
}


def normalize_text(value):
    """Normalize text for consistent comparison."""
    value = str(value or "").lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[\u2010-\u2015]", "-", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_skill(skill):
    skill = normalize_text(skill).strip(" ,.;:/")
    return SKILL_ALIASES.get(skill, skill)


def parse_required_skills(value):
    """
    Job skills are currently stored as text.
    Supports comma-separated, semicolon-separated, and line-separated skills.
    """
    if not value:
        return []

    parts = re.split(r"[,;\n\r|]+", value)

    skills = []
    seen = set()

    for part in parts:
        skill = normalize_skill(part)

        if skill and skill not in seen:
            skills.append(skill)
            seen.add(skill)

    return skills


def contains_skill(text, skill):
    """
    Match a skill as a phrase rather than a substring.
    This avoids matching 'R' inside unrelated words, for example.
    """
    text = normalize_text(text)
    skill = normalize_skill(skill)

    if not text or not skill:
        return False

    # Normalize aliases in the text for equivalent skill spellings.
    for alias, canonical in SKILL_ALIASES.items():
        text = re.sub(
            r"(?<!\w)" + re.escape(alias) + r"(?!\w)",
            canonical,
            text
        )

    # Skills containing symbols, such as C++ or C#, need a slightly
    # more permissive boundary check.
    pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
    return re.search(pattern, text) is not None


@lru_cache(maxsize=1)
def _load_sentence_model():
    """Load the compact semantic model only once per process."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def semantic_similarity(job_text, resume_text):
    """
    Return a similarity score from 0 to 100.

    Prefer semantic embeddings. Fall back to TF-IDF if the model is
    unavailable, for example because it has not been downloaded yet.
    """
    job_text = str(job_text or "").strip()
    resume_text = str(resume_text or "").strip()

    if not job_text or not resume_text:
        return 0.0, "insufficient_text"

    try:
        model = _load_sentence_model()
        embeddings = model.encode(
            [job_text, resume_text],
            normalize_embeddings=True
        )

        similarity = float(embeddings[0] @ embeddings[1])

        # Cosine similarity can be negative; clamp to a displayable range.
        score = max(0.0, min(1.0, similarity)) * 100
        return round(score, 2), "semantic"

    except Exception:
        try:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                max_features=20000
            )

            matrix = vectorizer.fit_transform(
                [job_text, resume_text]
            )

            score = float(
                cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
            ) * 100

            return round(score, 2), "tfidf_fallback"

        except Exception:
            return 0.0, "unavailable"


def _education_score(requirement, educations):
    """Compare a job's education requirement with profile education entries."""
    requirement = normalize_text(requirement)

    if not requirement:
        return None, "No education requirement provided."

    if not educations:
        return 0.0, "No education entries found in the profile."

    education_text = " ".join(
        f"{item.degree or ''} {item.field_of_study or ''} "
        f"{item.institution or ''} {item.description or ''}"
        for item in educations
    )

    if contains_skill(education_text, requirement):
        return 100.0, "The education requirement was found in profile information."

    requirement_words = set(re.findall(r"[a-z0-9+#.]+", requirement))
    education_words = set(
        re.findall(r"[a-z0-9+#.]+", normalize_text(education_text))
    )

    meaningful = {
        word for word in requirement_words
        if len(word) > 2 and word not in {
            "degree", "required", "preferred", "in", "or", "and", "the"
        }
    }

    if not meaningful:
        return None, "The education requirement could not be compared reliably."

    overlap = len(meaningful & education_words) / len(meaningful)

    return round(overlap * 100, 2), (
        "Estimated from degree, field of study, and education descriptions."
    )


def build_candidate_text(applicant, resume):
    """Build comparison text from existing CVision profile information."""
    sections = []

    if applicant:
        profile = getattr(applicant, "applicant_profile", None)

        if profile:
            sections.extend([
                profile.bio or "",
            ])

        for skill in getattr(applicant, "skills", []) or []:
            sections.append(skill.skill_name or "")

        for experience in getattr(applicant, "work_experiences", []) or []:
            sections.extend([
                experience.job_title or "",
                experience.company_name or "",
                experience.description or "",
                experience.employment_type or "",
            ])

        for education in getattr(applicant, "educations", []) or []:
            sections.extend([
                education.degree or "",
                education.field_of_study or "",
                education.institution or "",
                education.description or "",
            ])

        for project in getattr(applicant, "projects", []) or []:
            sections.extend([
                project.project_title or "",
                project.description or "",
                project.technologies or "",
            ])

        for certification in getattr(applicant, "certifications", []) or []:
            sections.extend([
                certification.certification_name or "",
                certification.issuing_organization or "",
                certification.description or "",
            ])

    if resume and resume.extracted_text:
        sections.append(resume.extracted_text)

    return "\n".join(
        str(section).strip()
        for section in sections
        if section and str(section).strip()
    )


def calculate_job_match(job, application):
    """
    Calculate a job-specific match score.

    The existing ATS Resume Score is not changed or reused here.
    Experience is excluded from the score because its estimation
    can be unreliable.

    Weights when all components are available:
        Description similarity: 40%
        Required skills:        40%
        Education:              20%
    """
    applicant = application.applicant

    active_resumes = [
        resume for resume in (getattr(applicant, "resumes", []) or [])
        if resume.status == "active"
    ]

    active_resumes.sort(
        key=lambda item: (
            item.uploaded_at.timestamp()
            if item.uploaded_at
            else 0
        ),
        reverse=True
    )

    resume = active_resumes[0] if active_resumes else None

    candidate_text = build_candidate_text(applicant, resume)

    # Description similarity uses job title + description.
    description_text = " ".join([
        job.job_title or "",
        job.description or "",
    ]).strip()

    description_score, similarity_method = semantic_similarity(
        description_text,
        candidate_text
    )

    required_skills = parse_required_skills(job.skills_required)

    matched_skills = []
    missing_skills = []

    candidate_skills = [
        skill.skill_name
        for skill in (getattr(applicant, "skills", []) or [])
        if skill.skill_name
    ]

    candidate_skill_text = " ".join(candidate_skills)

    # Match against both explicitly recorded skills and the candidate's
    # broader available text, including the extracted resume.
    for skill in required_skills:
        if (
            contains_skill(candidate_skill_text, skill)
            or contains_skill(candidate_text, skill)
        ):
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    skill_score = (
        round(len(matched_skills) / len(required_skills) * 100, 2)
        if required_skills
        else None
    )

    education_score, education_note = _education_score(
        job.education_required,
        getattr(applicant, "educations", []) or []
    )

    # Only description, skills, and education contribute to the final score.
    # If a requirement is unavailable, the remaining weights are
    # proportionally redistributed.
    components = [
        ("description", description_score, 40.0),
    ]

    if skill_score is not None:
        components.append(("skills", skill_score, 40.0))

    if education_score is not None:
        components.append(("education", education_score, 20.0))

    total_weight = sum(weight for _, _, weight in components)

    overall_score = (
        sum(score * weight for _, score, weight in components) / total_weight
        if total_weight
        else 0.0
    )

    return {
        "application_id": application.id,
        "job_id": job.id,
        "applicant_id": applicant.id,
        "applicant_name": applicant.full_name or applicant.username,
        "applicant_username": applicant.username,
        "job_title": job.job_title,
        "application_status": application.status,
        "applied_at": application.applied_at,
        "overall_score": round(overall_score, 2),
        "description_score": description_score,
        "skill_score": skill_score,
        "education_score": education_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "required_skills": required_skills,
        "similarity_method": similarity_method,
        "resume_available": bool(resume and resume.extracted_text),
        "education_note": education_note,
    }
