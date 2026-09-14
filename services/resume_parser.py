
import re


# ============================================================
# SECTION HEADERS
# ============================================================

SECTION_HEADERS = {
    "contact": [
        "contact",
        "contact information",
        "personal information",
    ],

    "skills": [
        "skills",
        "technical skills",
        "professional skills",
        "technical and professional skills",
        "technical & professional skills",
        "technical professional skills",
        "core skills",
        "key skills",
        "core competencies",
        "competencies",
        "areas of expertise",
        "technical expertise",
        "professional competencies",
    ],

    "education": [
        "education",
        "educational background",
        "academic background",
        "academic qualifications",
        "educational qualifications",
        "qualifications",
        "education qualifications",
    ],

    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "career history",
    ],

    "projects": [
        "projects",
        "academic projects",
        "personal projects",
        "professional projects",
        "key projects",
        "project experience",
    ],

    "certifications": [
        "certifications",
        "certificates",
        "professional certifications",
        "licenses and certifications",
        "certification",
    ],

    "achievements": [
         "achievement",
        "achievements",
        "academic achievements",
        "professional achievements",
        "awards",
        "awards and achievements",
        "awards & achievements",
        "honors",
        "honours",
        "honors and awards",
        "honours and awards",
        "honors & awards",
        "accomplishments",
        "awards and honors",
        "awards and honours",
    ],

    "summary": [
        "summary",
        "professional summary",
        "career summary",
        "profile",
        "professional profile",
        "objective",
        "career objective",
        "about me",
    ],
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(text):
    """
    Normalize extracted resume text while preserving
    line-by-line structure.
    """

    if not text:
        return ""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    lines = []

    for line in text.split("\n"):

        line = re.sub(
            r"[ \t]+",
            " ",
            line
        ).strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


# ============================================================
# HEADER CLEANING
# ============================================================

def clean_header(text):

    if not text:
        return ""

    text = text.strip().lower()

    text = re.sub(
        r"^[\s•●▪◦*\-–—:|]+",
        "",
        text
    )

    text = re.sub(
        r"[\s•●▪◦*\-–—:|]+$",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ============================================================
# SECTION HEADER DETECTION
# ============================================================

def detect_section_header(line):
    """
    Detect known resume section headings.
    """

    cleaned = clean_header(line)

    if not cleaned:
        return None

    for section, headers in SECTION_HEADERS.items():

        if cleaned in headers:
            return section

    return None


# ============================================================
# SECTION EXTRACTION
# ============================================================

def extract_sections(text):
    """
    Divide resume text into logical sections.
    """

    text = normalize_text(text)

    sections = {}

    current_section = "general"

    sections[current_section] = []

    for line in text.split("\n"):

        section = detect_section_header(line)

        if section:

            current_section = section

            if current_section not in sections:
                sections[current_section] = []

            continue

        sections.setdefault(
            current_section,
            []
        ).append(line)

    for section in sections:

        sections[section] = "\n".join(
            sections[section]
        ).strip()

    return sections


# ============================================================
# EMAIL
# ============================================================

def extract_email(text):

    if not text:
        return None

    pattern = (
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\."
        r"[A-Za-z]{2,}\b"
    )

    match = re.search(
        pattern,
        text
    )

    if match:
        return match.group(0)

    return None


# ============================================================
# PHONE
# ============================================================

def extract_phone(text):

    if not text:
        return None

    patterns = [
        r"\+8801[3-9]\d{8}",
        r"8801[3-9]\d{8}",
        r"01[3-9]\d{8}",
        r"\+880\s*1[3-9]\s*\d{4}\s*\d{4}",
        r"01[3-9][\s-]\d{4}[\s-]\d{4}",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:
            return match.group(0)

    return None


# ============================================================
# NAME
# ============================================================

def extract_name(text):

    if not text:
        return None

    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]

    for line in lines[:10]:

        cleaned = line.strip()

        if "@" in cleaned:
            continue

        if re.search(
            r"\d{5,}",
            cleaned
        ):
            continue

        if len(cleaned) > 60:
            continue

        if detect_section_header(cleaned):
            continue

        if re.fullmatch(
            r"[A-Za-z][A-Za-z .'-]{2,60}",
            cleaned
        ):

            words = cleaned.split()

            if 2 <= len(words) <= 5:
                return cleaned

    return None


# ============================================================
# SKILLS
# ============================================================

def extract_skills(section_text):

    if not section_text:
        return []

    skills = []

    cleaned = section_text

    for bullet in [
        "•",
        "●",
        "▪",
        "◦",
    ]:
        cleaned = cleaned.replace(
            bullet,
            "\n"
        )

    lines = cleaned.split("\n")

    known_labels = {
        "programming languages",
        "languages",
        "frameworks",
        "libraries",
        "tools",
        "technologies",
        "technical skills",
        "professional skills",
        "soft skills",
        "soft skills and communication",
        "database",
        "databases",
        "web technologies",
        "technical",
        "development tools",
    }

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # Handle:
        # Programming Languages: Python, C, C++
        if ":" in line:

            possible_label, possible_values = line.split(
                ":",
                1
            )

            label = possible_label.strip().lower()

            if label in known_labels:

                line = possible_values.strip()

        parts = re.split(
            r",|;|\||\s•\s",
            line
        )

        for part in parts:

            skill = part.strip()

            skill = re.sub(
                r"^[\-–—*•▪◦]+\s*",
                "",
                skill
            )

            if not skill:
                continue

            if len(skill) > 80:
                continue

            if detect_section_header(skill):
                continue

            skills.append(skill)

    # Remove duplicates
    unique_skills = []

    seen = set()

    for skill in skills:

        key = skill.lower()

        if key not in seen:

            seen.add(key)
            unique_skills.append(skill)

    return unique_skills


# ============================================================
# YEAR / DATE EXTRACTION
# ============================================================

def extract_year_range(text):

    if not text:
        return None

    pattern = (
        r"\b"
        r"(?:19|20)\d{2}"
        r"\s*"
        r"(?:-|–|—|to|until)"
        r"\s*"
        r"(?:(?:19|20)\d{2}|Present|present|Current|current)"
        r"\b"
    )

    match = re.search(
        pattern,
        text
    )

    if match:
        return match.group(0)

    # Single year
    match = re.search(
        r"\b(?:19|20)\d{2}\b",
        text
    )

    if match:
        return match.group(0)

    return None


# ============================================================
# EDUCATION
# ============================================================

DEGREE_KEYWORDS = [
    "b.sc",
    "bsc",
    "bachelor",
    "bachelors",
    "b.eng",
    "beng",
    "bba",
    "b.a",
    "b.a.",
    "b.s.",
    "bs ",
    "m.sc",
    "msc",
    "master",
    "masters",
    "m.eng",
    "meng",
    "mba",
    "m.a",
    "m.a.",
    "m.s.",
    "ms ",
    "phd",
    "ph.d",
    "doctorate",
    "diploma",
    "hsc",
    "higher secondary",
    "higher secondary certificate",
    "ssc",
    "secondary school certificate",
    "secondary",
    "o level",
    "o-level",
    "a level",
    "a-level",
    "alevel",
    "olevel",
    "bachelor of",
    "master of",
]


def looks_like_degree(text):

    lower = text.lower()

    for keyword in DEGREE_KEYWORDS:

        if keyword in lower:
            return True

    return False


def looks_like_institution(text):

    lower = text.lower()

    institution_keywords = [
        "university",
        "college",
        "school",
        "institute",
        "academy",
        "polytechnic",
        "institution",
        "madrasa",
        "madrassa",
    ]

    for keyword in institution_keywords:

        if keyword in lower:
            return True

    return False


def extract_education(section_text):

    if not section_text:
        return []

    lines = [
        line.strip()
        for line in section_text.split("\n")
        if line.strip()
    ]

    education = []

    current = None

    for line in lines:

        line = re.sub(
            r"^[•●▪◦*\-–—]+\s*",
            "",
            line
        ).strip()

        if not line:
            continue

        year = extract_year_range(line)

        is_degree = looks_like_degree(line)
        is_institution = looks_like_institution(line)

        # ----------------------------------------------------
        # New degree
        # ----------------------------------------------------

        if is_degree:

            if current:

                education.append(
                    current
                )

            current = {
                "degree": line,
                "institution": None,
                "year": year
            }

            continue

        # ----------------------------------------------------
        # Institution
        # ----------------------------------------------------

        if is_institution:

            if current is None:

                current = {
                    "degree": None,
                    "institution": line,
                    "year": year
                }

            else:

                if not current.get("institution"):

                    current["institution"] = line

                if year and not current.get("year"):

                    current["year"] = year

            continue

        # ----------------------------------------------------
        # Year
        # ----------------------------------------------------

        if year:

            if current is None:

                current = {
                    "degree": None,
                    "institution": None,
                    "year": year
                }

            elif not current.get("year"):

                current["year"] = year

            continue

        # ----------------------------------------------------
        # Additional education information
        # ----------------------------------------------------

        if current is None:

            current = {
                "degree": line,
                "institution": None,
                "year": None
            }

        elif (
            current.get("degree")
            and not current.get("institution")
        ):

            current["institution"] = line

        else:

            details = current.get(
                "details",
                []
            )

            details.append(line)

            current["details"] = details

    if current:
        education.append(current)

    cleaned = []

    for item in education:

        if any([
            item.get("degree"),
            item.get("institution"),
            item.get("year"),
            item.get("details")
        ]):

            cleaned.append(item)

    return cleaned


# ============================================================
# EXPERIENCE
# ============================================================

def extract_experience(section_text):

    if not section_text:
        return []

    lines = [
        line.strip()
        for line in section_text.split("\n")
        if line.strip()
    ]

    experience = []

    current = None

    for line in lines:

        line = re.sub(
            r"^[•●▪◦*\-–—]+\s*",
            "",
            line
        ).strip()

        if not line:
            continue

        year = extract_year_range(line)

        if current is None:

            current = {
                "title": line,
                "company": None,
                "duration": year,
                "details": []
            }

            continue

        if year and not current.get("duration"):

            current["duration"] = year

            continue

        if (
            not current.get("company")
            and len(line) < 100
        ):

            current["company"] = line

            continue

        current["details"].append(
            line
        )

    if current:
        experience.append(current)

    return experience


# ============================================================
# PROJECT HELPERS
# ============================================================

def clean_project_line(line):

    if not line:
        return ""

    line = line.strip()

    # Remove common bullets
    line = re.sub(
        r"^[•●▪◦]+\s*",
        "",
        line
    )

    return line.strip()


def is_numbered_project(line):

    """
    Detect:
        1. Project Name
        2) Project Name
        01. Project Name
    """

    return bool(
        re.match(
            r"^\d{1,2}\s*[\.\)]\s+.+",
            line
        )
    )


def remove_project_number(line):

    return re.sub(
        r"^\d{1,2}\s*[\.\)]\s+",
        "",
        line
    ).strip()


def is_project_label(line):

    """
    Detect lines such as:

    Project:
    Project 1:
    Project Name:
    Title:
    """

    lower = line.lower().strip()

    patterns = [
        r"^project\s*:",
        r"^project\s+\d+\s*:",
        r"^project\s+name\s*:",
        r"^title\s*:",
    ]

    for pattern in patterns:

        if re.match(
            pattern,
            lower
        ):
            return True

    return False


def is_technology_line(line):

    """
    Detect common technology-stack lines.

    Example:
        Technologies: Flask, MySQL
        Tech Stack: Python, Django
        Tools: Git, GitHub
    """

    lower = line.lower().strip()

    technology_labels = [
        "technologies:",
        "technology:",
        "tech stack:",
        "tech-stack:",
        "tech:",
        "tools:",
        "technologies used:",
        "built with:",
        "developed using:",
        "language:",
        "languages:",
    ]

    for label in technology_labels:

        if lower.startswith(label):
            return True

    return False


def looks_like_project_title(line):

    """
    Heuristic for identifying a project title.

    This is intentionally conservative so normal
    description sentences are not incorrectly treated
    as new projects.
    """

    if not line:
        return False

    line = line.strip()

    lower = line.lower()

    # Numbered project
    if is_numbered_project(line):
        return True

    # Explicit Project label
    if is_project_label(line):
        return True

    # Technology/description lines are not titles
    if is_technology_line(line):
        return False

    # Very long lines are usually descriptions
    if len(line) > 100:
        return False

    # Description-style sentence
    description_starters = [
        "developed ",
        "designed ",
        "created ",
        "built ",
        "implemented ",
        "developing ",
        "worked ",
        "responsible ",
        "an application",
        "a web",
        "an ai",
        "an ml",
        "this project",
        "the project",
        "project description",
        "description:",
    ]

    for starter in description_starters:

        if lower.startswith(starter):
            return False

    # Lines ending with a sentence period are more likely
    # to be descriptions.
    if line.endswith("."):
        return False

    # If the line contains a long sentence-like structure,
    # avoid treating it as a title.
    word_count = len(
        line.split()
    )

    if word_count > 12:
        return False

    # Technology-heavy lines are usually details.
    technology_terms = [
        "python",
        "java",
        "javascript",
        "typescript",
        "flask",
        "django",
        "react",
        "node",
        "mysql",
        "postgresql",
        "mongodb",
        "html",
        "css",
        "bootstrap",
        "tensorflow",
        "pytorch",
        "scikit",
        "opencv",
        "github",
        "git",
    ]

    technology_count = sum(
        1
        for term in technology_terms
        if term in lower
    )

    if technology_count >= 2:
        return False

    return True


# ============================================================
# PROJECTS
# ============================================================

def extract_projects(section_text):

    """
    Extract multiple projects separately.

    Supports common resume formats such as:

        Project 1: CVision
        Description...
        Technologies: Flask, MySQL

        Project 2: Lost & Found
        Description...
        Technologies: PHP, MySQL

    Also supports:

        CVision - AI Resume Screening System
        Description...

        Lost & Found Management System
        Description...

    The parser attempts to distinguish project titles
    from descriptions and technology lines.
    """

    if not section_text:
        return []

    raw_lines = section_text.split("\n")

    lines = []

    for raw_line in raw_lines:

        line = clean_project_line(
            raw_line
        )

        if line:
            lines.append(line)

    if not lines:
        return []

    projects = []

    current = None

    for index, line in enumerate(lines):

        # ----------------------------------------------------
        # Numbered project
        # ----------------------------------------------------

        if is_numbered_project(line):

            if current:
                projects.append(
                    current
                )

            title = remove_project_number(
                line
            )

            current = {
                "name": title,
                "details": []
            }

            continue

        # ----------------------------------------------------
        # Explicit project label
        # ----------------------------------------------------

        if is_project_label(line):

            if current:
                projects.append(
                    current
                )

            title = re.sub(
                r"^project(?:\s+\d+)?\s*(?:name)?\s*:\s*",
                "",
                line,
                flags=re.IGNORECASE
            ).strip()

            current = {
                "name": title or "Untitled Project",
                "details": []
            }

            continue

        # ----------------------------------------------------
        # First project
        # ----------------------------------------------------

        if current is None:

            current = {
                "name": line,
                "details": []
            }

            continue

        # ----------------------------------------------------
        # Detect a likely new project title
        # ----------------------------------------------------

        if looks_like_project_title(line):

            # If current project has enough content,
            # consider this line a new project title.
            if (
                current.get("name")
                and (
                    current.get("details")
                    or index > 0
                )
            ):

                projects.append(
                    current
                )

                current = {
                    "name": line,
                    "details": []
                }

                continue

        # ----------------------------------------------------
        # Otherwise it belongs to current project
        # ----------------------------------------------------

        current["details"].append(
            line
        )

    # Add final project
    if current:

        projects.append(
            current
        )

    # --------------------------------------------------------
    # Clean projects
    # --------------------------------------------------------

    cleaned_projects = []

    for project in projects:

        name = project.get(
            "name",
            ""
        ).strip()

        details = [
            detail.strip()
            for detail in project.get(
                "details",
                []
            )
            if detail.strip()
        ]

        if not name:
            continue

        # Avoid accidentally creating a project from
        # technology/detail-only content.
        cleaned_projects.append({
            "name": name,
            "details": details
        })

    return cleaned_projects


# ============================================================
# CERTIFICATIONS
# ============================================================

def extract_certifications(section_text):

    if not section_text:
        return []

    lines = []

    for line in section_text.split("\n"):

        line = re.sub(
            r"^[•●▪◦*\-–—]+\s*",
            "",
            line.strip()
        )

        if line:
            lines.append(line)

    return lines


# ============================================================
# ACHIEVEMENTS
# ============================================================

def extract_achievements(section_text):

    if not section_text:
        return []

    achievements = []

    cleaned = section_text

    for bullet in [
        "•",
        "●",
        "▪",
        "◦",
    ]:

        cleaned = cleaned.replace(
            bullet,
            "\n"
        )

    for line in cleaned.split("\n"):

        line = line.strip()

        if not line:
            continue

        line = re.sub(
            r"^[\-–—*]+\s*",
            "",
            line
        ).strip()

        if not line:
            continue

        achievements.append(
            line
        )

    # Remove duplicates
    unique_achievements = []

    seen = set()

    for achievement in achievements:

        key = achievement.lower()

        if key not in seen:

            seen.add(key)

            unique_achievements.append(
                achievement
            )

    return unique_achievements


# ============================================================
# MAIN PARSER
# ============================================================

def parse_resume(text):

    text = normalize_text(
        text
    )

    sections = extract_sections(
        text
    )

    parsed_data = {

        "name": extract_name(
            text
        ),

        "email": extract_email(
            text
        ),

        "phone": extract_phone(
            text
        ),

        "skills": extract_skills(
            sections.get(
                "skills",
                ""
            )
        ),

        "education": extract_education(
            sections.get(
                "education",
                ""
            )
        ),

        "experience": extract_experience(
            sections.get(
                "experience",
                ""
            )
        ),

        "projects": extract_projects(
            sections.get(
                "projects",
                ""
            )
        ),

        "certifications": extract_certifications(
            sections.get(
                "certifications",
                ""
            )
        ),

        "achievements": extract_achievements(
            sections.get(
                "achievements",
                ""
            )
        ),

        "sections": sections
    }

    return parsed_data
