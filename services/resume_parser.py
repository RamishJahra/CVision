import re
from datetime import datetime

# ============================================================
# SECTION HEADERS
# ============================================================

SECTION_HEADERS = {

    "contact": [
        "contact",
        "contact information",
        "personal information",
        "personal details",
        "contact details",
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
        "technical competencies",
        "skills & competencies",
        "skills and competencies",
    ],

    "education": [
        "education",
        "educational background",
        "academic background",
        "academic qualifications",
        "educational qualifications",
        "qualifications",
        "education qualifications",
        "academic history",
    ],

    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "career history",
        "professional history",
        "employment experience",
    ],

    "projects": [
        "projects",
        "academic projects",
        "personal projects",
        "professional projects",
        "key projects",
        "project experience",
        "project work",
        "selected projects"
    ],

    "certifications": [
        "certifications",
        "certificates",
        "professional certifications",
        "licenses and certifications",
        "certification",
        "licenses",
        "licenses & certifications",
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
        "about",
    ],

    "leadership": [
        "leadership",
        "leadership & activities",
        "leadership and activities",
        "activities",
        "extracurricular activities",
        "volunteer experience",
        "volunteering",
    ],

    "training": [
        "training",
        "workshop",
        "workshops",
        "workshop & training",
        "workshop and training",
        "training & workshops",
        "training and workshops",
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

    # Unicode spaces
    text = text.replace("\u00a0", " ")
    text = text.replace("\u2007", " ")
    text = text.replace("\u202f", " ")

    lines = []

    for line in text.split("\n"):

        # IMPORTANT:
        # Do not use corrupted patterns such as
        # [ **\t** ].
        line = re.sub(r"[ \t]+", " ", line).strip()

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

    # Remove decorative characters from beginning/end.
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

    text = text.replace("&", "and")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# SECTION HEADER DETECTION
# ============================================================

def detect_section_header(line):

    cleaned = clean_header(line)

    if not cleaned:
        return None

    for section, headers in SECTION_HEADERS.items():

        normalized_headers = [
            clean_header(header)
            for header in headers
        ]

        if cleaned in normalized_headers:
            return section

    return None


# ============================================================
# SECTION EXTRACTION
# ============================================================

def extract_sections(text):
    """
    Divide resume text into logical sections.

    Some PDFs have unusual visual reading order.
    Therefore, section extraction remains line based,
    but later we also perform recovery for education,
    experience, leadership and training.
    """

    text = normalize_text(text)

    sections = {
        "general": []
    }

    current_section = "general"

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
        r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@"
        r"[A-Za-z0-9-]+"
        r"(?:\.[A-Za-z0-9-]+)+\b"
    )

    match = re.search(
        pattern,
        text
    )

    if match:
        return match.group(0).strip()

    return None

# ============================================================
# CONTACT LINKS
# ============================================================

def normalize_url(url):
    if not url:
        return None

    url = url.strip().rstrip(".,;:)")

    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url

    return url


def extract_linkedin(text):
    if not text:
        return None

    pattern = (
        r"(?:https?://)?"
        r"(?:www\.)?"
        r"linkedin\.com/[^\s<>\]\[|]+"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if match:
        return normalize_url(match.group(0))

    return None


def extract_github(text):
    if not text:
        return None

    pattern = (
        r"(?:https?://)?"
        r"(?:www\.)?"
        r"github\.com/[^\s<>\]\[|]+"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if match:
        return normalize_url(match.group(0))

    return None


def extract_website(text):
    if not text:
        return None

    # Find URLs and www-style domains.
    pattern = (
        r"(?:https?://|www\.)"
        r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
        r"(?:/[^\s<>\]\[|]*)?"
    )

    matches = re.findall(
        pattern,
        text,
        re.IGNORECASE
    )

    for match in matches:

        url = normalize_url(match)

        lower = url.lower()

        # Do NOT classify LinkedIn/GitHub as website.
        if "linkedin.com" in lower:
            continue

        if "github.com" in lower:
            continue

        return url

    return None


def extract_contact_links(text):
    return {
        "linkedin": extract_linkedin(text),
        "github": extract_github(text),
        "website": extract_website(text)
    }
# ============================================================
# PHONE
# ============================================================

def normalize_phone(phone):

    if not phone:
        return None

    phone = phone.strip()

    digits = re.sub(
        r"[()\s\-./]",
        "",
        phone
    )

    if digits.startswith("+880"):
        digits = digits[1:]

    if digits.startswith("8801") and len(digits) == 13:
        return digits

    if digits.startswith("01") and len(digits) == 11:
        return "880" + digits

    return digits


def extract_phone(text):
    """
    Extract Bangladeshi phone numbers.

    Keep this implementation stable because the current
    phone detection has already been fixed.
    """

    if not text:
        return None

    patterns = [

        # +880 18-3923-9983
        r"(?<!\d)"
        r"\+880"
        r"[\s\-]?"
        r"1[3-9]"
        r"[\s\-]?"
        r"\d{4}"
        r"[\s\-]?"
        r"\d{4}"
        r"(?!\d)",

        # 880 18-3923-9983
        r"(?<!\d)"
        r"880"
        r"[\s\-]?"
        r"1[3-9]"
        r"[\s\-]?"
        r"\d{4}"
        r"[\s\-]?"
        r"\d{4}"
        r"(?!\d)",

        # 01XXXXXXXXX
        r"(?<!\d)"
        r"01[3-9]\d{8}"
        r"(?!\d)",

        # 01839-239983
        r"(?<!\d)"
        r"01[3-9]\d{2}"
        r"[\s\-]"
        r"\d{6}"
        r"(?!\d)",

        # 0183-9239983
        r"(?<!\d)"
        r"01[3-9]"
        r"[\s\-]"
        r"\d{7}"
        r"(?!\d)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:

            phone = match.group(0)

            normalized = normalize_phone(phone)

            if normalized:
                return phone.strip()

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

    for line in lines[:15]:

        cleaned = line.strip()

        if "@" in cleaned:
            continue

        if extract_phone(cleaned):
            continue

        if re.search(
            r"(https?://|www\.|linkedin\.com|github\.com)",
            cleaned,
            re.IGNORECASE
        ):
            continue

        if len(cleaned) > 60:
            continue

        if detect_section_header(cleaned):
            continue

        if len(re.findall(r"\d", cleaned)) >= 3:
            continue

        if re.fullmatch(
            r"[A-Za-z][A-Za-z .'\-]{2,60}",
            cleaned
        ):

            words = cleaned.split()

            if 2 <= len(words) <= 5:

                ignored = {
                    "curriculum vitae",
                    "resume",
                    "curriculum vitae resume",
                    "professional profile",
                    "software engineer",
                    "computer science student",
                }

                if cleaned.lower() not in ignored:
                    return cleaned

    return None


# ============================================================
# SKILLS
# ============================================================

def extract_skills(section_text):

    if not section_text:
        return []

    skills = []

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
        "framework",
        "technology",
        "tools and technologies",
    }

    cleaned = section_text

    cleaned = re.sub(
        r"[•●▪◦]",
        "\n",
        cleaned
    )

    lines = cleaned.split("\n")

    for line in lines:

        line = line.strip()

        if not line:
            continue

        line = re.sub(
            r"^[*\-–—•▪◦]+\s*",
            "",
            line
        ).strip()

        if not line:
            continue

        if ":" in line:

            possible_label, possible_values = line.split(
                ":",
                1
            )

            label = possible_label.strip().lower()

            if label in known_labels:
                line = possible_values.strip()

        if not line:
            continue

        parts = re.split(
            r",|;|\|",
            line
        )

        for part in parts:

            skill = part.strip()

            skill = re.sub(
                r"^[*\-–—•▪◦]+\s*",
                "",
                skill
            ).strip()

            if not skill:
                continue

            if len(skill) > 80:
                continue

            if detect_section_header(skill):
                continue

            if skill.lower() in known_labels:
                continue

            skills.append(skill)

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

    # Month + year range:
    # July 2023 - Present
    # Aug 2019 – Mar 2022
    # March 2018 - Present

    month = (
        r"(?:"
        r"Jan(?:uary)?|"
        r"Feb(?:ruary)?|"
        r"Mar(?:ch)?|"
        r"Apr(?:il)?|"
        r"May|"
        r"Jun(?:e)?|"
        r"Jul(?:y)?|"
        r"Aug(?:ust)?|"
        r"Sep(?:tember)?|"
        r"Oct(?:ober)?|"
        r"Nov(?:ember)?|"
        r"Dec(?:ember)?"
        r")"
    )

    month_range_pattern = (
        r"\b"
        + month +
        r"\s+"
        r"(?:19|20)\d{2}"
        r"\s*(?:-|–|—|to|until)\s*"
        r"(?:"
        + month +
        r"\s+"
        r"(?:19|20)\d{2}"
        r"|"
        r"Present|Current|Now"
        r")"
        r"\b"
    )

    match = re.search(
        month_range_pattern,
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(0).strip()

    # Year range:
    # 2020 - 2024
    # 2020 - Present

    year_range_pattern = (
        r"\b"
        r"(?:19|20)\d{2}"
        r"\s*(?:-|–|—|to|until)\s*"
        r"(?:"
        r"(?:19|20)\d{2}"
        r"|Present|Current|Now"
        r")"
        r"\b"
    )

    match = re.search(
        year_range_pattern,
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(0).strip()

    # Single month + year

    month_year_pattern = (
        r"\b"
        + month +
        r"\s+"
        r"(?:19|20)\d{2}"
        r"\b"
    )

    match = re.search(
        month_year_pattern,
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(0).strip()

    # Single year

    match = re.search(
        r"\b(?:19|20)\d{2}\b",
        text
    )

    if match:
        return match.group(0)

    return None

def parse_education_years(year_text):
    """
    Convert an education date/range into structured values.

    Examples:
        2022 - 2026
        2022 - Present
        July 2022 - Present
        Aug 2020 - Mar 2024
    """

    if not year_text:
        return {
            "start_year": None,
            "end_year": None,
            "is_current": False
        }

    text = year_text.strip()

    # --------------------------------------------------------
    # Detect ongoing education
    # --------------------------------------------------------

    is_current = bool(
        re.search(
            r"\b(Present|Current|Now)\b",
            text,
            re.IGNORECASE
        )
    )

    years = re.findall(
        r"\b(?:19|20)\d{2}\b",
        text
    )

    if not years:
        return {
            "start_year": None,
            "end_year": None,
            "is_current": is_current
        }

    start_year = int(years[0])

    if is_current:
        end_year = None
    elif len(years) >= 2:
        end_year = int(years[1])
    else:
        end_year = None

    return {
        "start_year": start_year,
        "end_year": end_year,
        "is_current": is_current
    }

def parse_experience_dates(duration_text):
    """
    Convert an experience duration into structured date values.

    Examples:

        July 2023 - Present
        Aug 2021 - Mar 2024
        2020 - 2023
        2022 - Current

    Returns:

        {
            "start_date": "2023-07-01",
            "end_date": None,
            "currently_working": True
        }
    """

    if not duration_text:
        return {
            "start_date": None,
            "end_date": None,
            "currently_working": False
        }

    text = duration_text.strip()

    # --------------------------------------------------
    # Check whether the experience is ongoing
    # --------------------------------------------------

    currently_working = bool(
        re.search(
            r"\b(Present|Current|Now)\b",
            text,
            re.IGNORECASE
        )
    )

    # --------------------------------------------------
    # Extract month/year combinations
    # --------------------------------------------------

    month_pattern = (
        r"(January|February|March|April|May|June|July|"
        r"August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
    )

    month_year_matches = re.findall(
        rf"{month_pattern}\s+((?:19|20)\d{{2}})",
        text,
        re.IGNORECASE
    )

    # --------------------------------------------------
    # Extract years
    # --------------------------------------------------

    years = re.findall(
        r"\b(?:19|20)\d{2}\b",
        text
    )

    start_date = None
    end_date = None

    # --------------------------------------------------
    # Month + Year
    # --------------------------------------------------

    if len(month_year_matches) >= 1:

        start_month = month_year_matches[0][0]
        start_year = int(month_year_matches[0][1])

        try:

            start_month_number = datetime.strptime(
                start_month[:3].title(),
                "%b"
            ).month

        except ValueError:

            start_month_number = 1

        start_date = (
            f"{start_year:04d}-"
            f"{start_month_number:02d}-01"
        )

        # --------------------------------------------------
        # End month + year
        # --------------------------------------------------

        if (
            len(month_year_matches) >= 2
            and not currently_working
        ):

            end_month = month_year_matches[1][0]
            end_year = int(month_year_matches[1][1])

            try:

                end_month_number = datetime.strptime(
                    end_month[:3].title(),
                    "%b"
                ).month

            except ValueError:

                end_month_number = 1

            end_date = (
                f"{end_year:04d}-"
                f"{end_month_number:02d}-01"
            )

    # --------------------------------------------------
    # Year-only dates
    # --------------------------------------------------

    elif len(years) >= 1:

        start_date = (
            f"{int(years[0]):04d}-01-01"
        )

        if (
            len(years) >= 2
            and not currently_working
        ):

            end_date = (
                f"{int(years[1]):04d}-01-01"
            )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "currently_working": currently_working
    }

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
]


def looks_like_degree(text):

    lower = text.lower()

    return any(
        keyword in lower
        for keyword in DEGREE_KEYWORDS
    )


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

    return any(
        keyword in lower
        for keyword in institution_keywords
    )


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

        year_data = parse_education_years(
            year
        )

        # ----------------------------------------------------
        # New degree
        # ----------------------------------------------------

        if looks_like_degree(line):

            if current:
                education.append(current)

            current = {
            "degree": line,
            "institution": None,
            "year": year,
            "start_year": year_data["start_year"],
            "end_year": year_data["end_year"],
            "is_current": year_data["is_current"],
            "details": []
        }

            continue

        # ----------------------------------------------------
        # Institution
        # ----------------------------------------------------

        if looks_like_institution(line):

            if current is None:

                current = {
                    "degree": None,
                    "institution": line,
                    "year": year,
                    "details": []
                }

            else:

                if not current.get("institution"):
                    current["institution"] = line

                if year and not current.get("year"):
                    current["year"] = year

            continue

        # ----------------------------------------------------
        # Date
        # ----------------------------------------------------

        if year:

            if current is None:

                current = {
                    "degree": None,
                    "institution": None,
                    "year": year,
                    "details": []
                }

            elif not current.get("year"):

                current["year"] = year

            else:

                current.setdefault(
                    "details",
                    []
                ).append(line)

            continue

        # ----------------------------------------------------
        # Additional details
        # ----------------------------------------------------

        if current is None:

            continue

        current.setdefault(
            "details",
            []
        ).append(line)

    if current:
        education.append(current)

    # Remove empty details
    for item in education:

        item["details"] = [
            d
            for d in item.get("details", [])
            if d.strip()
        ]

    return education


# ============================================================
# EXPERIENCE HELPERS
# ============================================================

def looks_like_job_title(line):

    if not line:
        return False

    lower = line.lower()

    job_keywords = [
        "engineer",
        "developer",
        "designer",
        "manager",
        "intern",
        "internship",
        "analyst",
        "consultant",
        "administrator",
        "officer",
        "executive",
        "assistant",
        "specialist",
        "lead",
        "architect",
        "researcher",
        "research assistant",
        "scientist",
        "programmer",
        "coordinator",
        "director",
        "trainee",
        "secretary",
        "member",
    ]

    return any(
        keyword in lower
        for keyword in job_keywords
    )


def looks_like_company(line):

    if not line:
        return False

    lower = line.lower()

    company_keywords = [
        "ltd",
        "limited",
        "inc",
        "inc.",
        "llc",
        "corp",
        "corporation",
        "company",
        "technologies",
        "technology",
        "solutions",
        "systems",
        "software",
        "group",
        "agency",
        "organization",
        "foundation",
        "university",
        "college",
        "bank",
        "club",
    ]

    return any(
        keyword in lower
        for keyword in company_keywords
    )


# ============================================================
# EXPERIENCE
# ============================================================

def extract_experience(section_text):

    if not section_text:
        return []

    lines = [
        line.strip()
        for line in section_text.splitlines()
        if line.strip()
    ]

    experience = []
    current = None

    for line in lines:

        # ---------------------------------------------
        # Remove bullets
        # ---------------------------------------------

        line = re.sub(
            r"^[•●▪◦\*\\\-–—]+\s*",
            "",
            line
        ).strip()

        if not line:
            continue

        # ---------------------------------------------
        # Detect date
        # ---------------------------------------------

        year = extract_year_range(line)

        date_data = parse_experience_dates(
            year
        )

        # ---------------------------------------------
        # Decide whether this is REALLY a new title
        # ---------------------------------------------

        words = line.split()

        is_short_title = (
            len(words) <= 8
            and not re.search(
                r"[.!?]$",
                line
            )
        )

        is_new_title = (
            looks_like_job_title(line)
            and is_short_title
        )

        # ---------------------------------------------
        # New experience
        # ---------------------------------------------

        if is_new_title:

            if current:
                experience.append(
                    current
                )

            current = {
                "title": line,
                "company": None,
                "duration": "",

                "start_date": None,
                "end_date": None,
                "currently_working": False,

                "details": []
            }

            continue

        # ---------------------------------------------
        # Ignore anything before first title
        # ---------------------------------------------

        if current is None:
            continue

        # ---------------------------------------------
        # Company / Organization
        # ---------------------------------------------

        if not current["company"]:

            if looks_like_company(line):

                current["company"] = line

                continue

            # First short non-date line after title
            # can be organization/company.

            if (
                not year
                and not current["details"]
                and len(line) <= 150
                and not looks_like_job_title(line)
            ):

                current["company"] = line

                continue

        # ---------------------------------------------
        # Date belongs to CURRENT experience
        # ---------------------------------------------

        if year:

            if not current["duration"]:

                current["duration"] = year

                current["start_date"] = (
                    date_data["start_date"]
                )

                current["end_date"] = (
                    date_data["end_date"]
                )

                current["currently_working"] = (
                    date_data["currently_working"]
                )

            else:

                current["details"].append(
                    line
                )

            continue

        # ---------------------------------------------
        # Everything else is description
        # ---------------------------------------------

        current["details"].append(
            line
        )

    # ---------------------------------------------
    # Save final record
    # ---------------------------------------------

    if current:

        experience.append(
            current
        )

    # ---------------------------------------------
    # Clean result
    # ---------------------------------------------

    cleaned = []

    for item in experience:

        title = (
            item.get("title")
            or ""
        ).strip()

        company = (
            item.get("company")
            or ""
        ).strip()

        duration = (
            item.get("duration")
            or ""
        ).strip()

        details = [
            detail.strip()
            for detail in item.get(
                "details",
                []
            )
            if detail.strip()
        ]

        if not title:
            continue

        cleaned.append({

            "title": title,

            "company": company,

            "duration": duration,

            "start_date": item.get(
                "start_date"
            ),

            "end_date": item.get(
                "end_date"
            ),

            "currently_working": item.get(
                "currently_working",
                False
            ),

            "details": details
        })

    return cleaned
# ============================================================
# PROJECT HELPERS
# ============================================================

def clean_project_line(line):

    if not line:
        return ""

    line = line.strip()

    line = re.sub(
        r"^[•●▪◦]+\s*",
        "",
        line
    )

    return line.strip()


def is_numbered_project(line):

    return bool(
        re.match(
            r"^\d{1,2}\s*[.)]\s+.+",
            line
        )
    )


def remove_project_number(line):

    return re.sub(
        r"^\d{1,2}\s*[.)]\s+",
        "",
        line
    ).strip()


def is_project_label(line):

    lower = line.lower().strip()

    patterns = [
        r"^project\s*:",
        r"^project\s+\d+\s*:",
        r"^project\s+name\s*:",
        r"^title\s*:",
    ]

    return any(
        re.match(pattern, lower)
        for pattern in patterns
    )


def is_technology_line(line):

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

    return any(
        lower.startswith(label)
        for label in technology_labels
    )


def looks_like_project_title(line):

    if not line:
        return False

    line = line.strip()
    lower = line.lower()

    if is_numbered_project(line):
        return True

    if is_project_label(line):
        return True

    if is_technology_line(line):
        return False

    if len(line) > 100:
        return False

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
        "a mobile",
        "an ai",
        "an ml",
        "this project",
        "the project",
        "project description",
        "description:",
        "technologies:",
    ]

    if any(
        lower.startswith(starter)
        for starter in description_starters
    ):
        return False

    if line.endswith("."):
        return False

    word_count = len(line.split())

    if word_count > 12:
        return False

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

    if not section_text:
        return []

    lines = [
        re.sub(
            r"\s+",
            " ",
            line
        ).strip()
        for line in section_text.splitlines()
        if line.strip()
    ]

    if not lines:
        return []

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def is_metadata(line):

        return bool(
            re.match(
                r"^(technologies?|tech\s*stack|"
                r"tools?|frameworks?|"
                r"languages?|description|"
                r"role|responsibilities?)\s*:",
                line,
                re.IGNORECASE
            )
        )

    def is_date(line):

        return bool(
            extract_year_range(line)
        )

    def looks_like_description(line):

        lower = line.lower()

        description_starts = (
            "developed ",
            "designed ",
            "created ",
            "built ",
            "implemented ",
            "developed a ",
            "developed an ",
            "created a ",
            "created an ",
            "designed a ",
            "designed an ",
            "built a ",
            "built an ",
            "this project",
            "the project",
            "a platform ",
            "an application ",
            "a web ",
            "an automated ",
            "used ",
            "using ",
            "responsible ",
            "worked ",
            "integrated ",
            "provided "
        )

        if lower.startswith(
            description_starts
        ):
            return True

        if re.search(
            r"[.!?]$",
            line
        ):
            return True

        return False

    def looks_like_technology(line):

        if is_metadata(line):
            return True

        # Common technology-list pattern
        if re.search(
            r"\b("
            r"PHP|Python|Java|JavaScript|"
            r"C\+\+|C#|HTML|CSS|SQL|MySQL|"
            r"React|Node\.?js|Express\.?js|"
            r"Laravel|Django|Flask|"
            r"Bootstrap|MongoDB|Firebase|"
            r"TensorFlow|PyTorch|"
            r"Git|GitHub|REST|API|"
            r"GraphQL|Socket\.IO"
            r")\b",
            line,
            re.IGNORECASE
        ):
            # Technology lines normally contain several
            # technologies or a technology label.
            if (
                "," in line
                or "|" in line
                or ":" in line
            ):
                return True

        return False

    def is_possible_title(index):

        line = lines[index]

        if not line:
            return False

        if is_metadata(line):
            return False

        if is_date(line):
            return False

        if looks_like_description(line):
            return False

        if looks_like_technology(line):
            return False

        # Project titles are generally short.
        word_count = len(
            line.split()
        )

        if word_count > 8:
            return False

        # A title should not look like a normal sentence.
        if "," in line:
            return False

        # ------------------------------------------------
        # Look at the following lines.
        #
        # A real project title should normally be followed
        # by project-related information.
        # ------------------------------------------------

        following = lines[
            index + 1:
            index + 4
        ]

        if not following:
            return False

        useful_following = 0

        for next_line in following:

            if (
                is_metadata(next_line)
                or looks_like_technology(next_line)
                or looks_like_description(next_line)
                or is_date(next_line)
            ):
                useful_following += 1

        return useful_following > 0

    # --------------------------------------------------
    # Find project boundaries
    # --------------------------------------------------

    title_indexes = []

    for index in range(
        len(lines)
    ):

        if is_possible_title(index):

            title_indexes.append(
                index
            )

    # --------------------------------------------------
    # Remove false consecutive candidates
    #
    # Example:
    #
    # Losers Bank                  <- title
    # Web Based Bank Management    <- subtitle
    # Technologies: PHP...        <- metadata
    #
    # Only Losers Bank remains.
    # --------------------------------------------------

    filtered_indexes = []

    for index in title_indexes:

        if not filtered_indexes:

            filtered_indexes.append(
                index
            )
            continue

        previous = filtered_indexes[-1]

        # If candidate is immediately after another
        # candidate, examine whether it is actually a
        # subtitle.
        if index == previous + 1:

            candidate = lines[index]

            # Subtitle-like phrases
            if re.search(
                r"\b("
                r"web\s+based|"
                r"web-based|"
                r"mobile\s+based|"
                r"mobile-based|"
                r"desktop\s+based|"
                r"desktop-based|"
                r"management\s+system|"
                r"application\s+system|"
                r"information\s+system|"
                r"banking\s+system|"
                r"generation\s+system|"
                r"software\s+system|"
                r"computer\s+peripherals|"
                r"computer\s+interfacing|"
                r"hardware\s+interfacing|"
                r"interfacing\s+lab|"
                r"lab$|"
                r"platform|"
                r"application|"
                r"website|"
                r"mobile\s+app|"
                r"web\s+application"
                r")\b",
                candidate,
                re.IGNORECASE
            ):
                continue

        filtered_indexes.append(
            index
        )

    # --------------------------------------------------
    # Build projects
    # --------------------------------------------------

    projects = []

    for position, start in enumerate(
        filtered_indexes
    ):

        # Don't allow candidates that are actually inside
        # another project's details.

        if position > 0:

            previous_start = (
                filtered_indexes[
                    position - 1
                ]
            )

            if start <= previous_start:
                continue

        if position + 1 < len(
            filtered_indexes
        ):

            end = filtered_indexes[
                position + 1
            ]

        else:

            end = len(lines)

        project_name = lines[start]

        details = lines[
            start + 1:end
        ]

        # --------------------------------------------------
        # Separate Technologies from Description
        # --------------------------------------------------

        technologies = None
        description_details = []

        for detail in details:

            detail = detail.strip()

            if not detail:
                continue

            # ----------------------------------------------
            # Explicit technology metadata
            #
            # Example:
            # Technologies: PHP, MySQL, HTML, CSS
            # Tech Stack: Flask, MySQL
            # Tools: Git, GitHub
            # Frameworks: Bootstrap, Flask
            # ----------------------------------------------

            technology_match = re.match(
                r"^(?:technologies?|"
                r"technologies?\s+used|"
                r"tech\s*stack|"
                r"tech\s*stack\s+used|"
                r"tools?|"
                r"tools?\s+and\s+technologies|"
                r"tools?\s*&\s*technologies|"
                r"frameworks?|"
                r"languages?)"
                r"\s*:\s*(?P<value>.+)$",
                detail,
                re.IGNORECASE
            )

            if technology_match:

                technology_value = (
                    technology_match.group("value")
                    .strip()
                )

                if technology_value:

                    if technologies:

                        technologies = (
                            technologies
                            + ", "
                            + technology_value
                        )

                    else:

                        technologies = technology_value

                continue

            # ----------------------------------------------
            # Description metadata
            #
            # Example:
            # Description: Developed a web application...
            # ----------------------------------------------

            description_match = re.match(
                r"^description\s*:\s*(.+)$",
                detail,
                re.IGNORECASE
            )

            if description_match:

                description_text = (
                    description_match.group(1)
                    .strip()
                )

                if description_text:
                    description_details.append(
                        description_text
                    )

                continue

            # ----------------------------------------------
            # Role / Responsibilities
            #
            # These should remain part of the description.
            # ----------------------------------------------

            role_match = re.match(
                r"^(?:role|responsibilities?)"
                r"\s*:\s*(.+)$",
                detail,
                re.IGNORECASE
            )

            if role_match:

                role_text = (
                    role_match.group(1)
                    .strip()
                )

                if role_text:
                    description_details.append(
                        role_text
                    )

                continue

            # ----------------------------------------------
            # Automatically detect technology lists
            #
            # We intentionally use the EXISTING
            # looks_like_technology() helper.
            #
            # No existing re.search() section is changed.
            # ----------------------------------------------

            if looks_like_technology(detail):

                # Only classify it as technology when it
                # looks like a technology list/metadata.
                #
                # This prevents normal description sentences
                # containing words like "Python" from being
                # incorrectly moved to Technologies.

                if (
                    "," in detail
                    or "|" in detail
                    or ":" in detail
                ):

                    if technologies:

                        technologies = (
                            technologies
                            + ", "
                            + detail
                        )

                    else:

                        technologies = detail

                    continue

            # ----------------------------------------------
            # Everything else remains Description
            # ----------------------------------------------

            description_details.append(
                detail
            )

        projects.append({

            "name": project_name,

            "technologies": (
                technologies
                if technologies
                else None
            ),

            "details": description_details

        })

    # --------------------------------------------------
    # Final cleanup
    # --------------------------------------------------

    cleaned = []

    for project in projects:

        name = (
            project.get("name")
            or ""
        ).strip()

        technologies = (
            project.get("technologies")
            or ""
        ).strip()

        details = [

            detail.strip()

            for detail in project.get(
                "details",
                []
            )

            if detail and detail.strip()

        ]

        if name:

            cleaned.append({

                "name": name,

                "technologies": (
                    technologies
                    if technologies
                    else None
                ),

                "details": details

            })

    return cleaned
# ============================================================
# CERTIFICATIONS
# ============================================================

def extract_certifications(section_text):

    if not section_text:
        return []

    lines = []

    for line in section_text.split("\n"):

        line = re.sub(
        r"^[•●▪◦*\\\-–—]+\s*",
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
            r"^[*\-–—]+\s*",
            "",
            line
        ).strip()

        if line:
            achievements.append(line)

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


def recover_misordered_sections(sections):
    """
    Recover education, experience and training when PDF reading order
    places LEADERSHIP & ACTIVITIES / WORKSHOP & TRAINING before the
    actual education and experience records.

    Expected PDF reading order:

        LEADERSHIP & ACTIVITIES
        WORKSHOP & TRAINING

        B.Sc. ...
        University
        CGPA...
        ...
        Education Secretary
        Organization
        ...
        Workshop on ...
    """

    leadership_text = sections.get(
        "leadership",
        ""
    ) or ""

    training_text = sections.get(
        "training",
        ""
    ) or ""

    combined = "\n".join(
        part
        for part in [
            leadership_text,
            training_text
        ]
        if part.strip()
    )

    lines = [
        re.sub(
            r"\s+",
            " ",
            line
        ).strip()
        for line in combined.splitlines()
        if line.strip()
    ]

    if not lines:
        return [], [], []

    # ------------------------------------------------------
    # Find first education record
    # ------------------------------------------------------

    education_start = None

    for index, line in enumerate(lines):

        if looks_like_degree(line):

            education_start = index
            break

    if education_start is None:
        return [], [], lines

    # ------------------------------------------------------
    # Find the FIRST actual experience title
    #
    # Do NOT use the generic company/job detector here.
    # Education institutions such as "Port City International
    # University" must never become experience.
    # ------------------------------------------------------

    experience_start = None

    experience_title_patterns = [
        r"\bsecretary\b",
        r"\bcoordinator\b",
        r"\bmanager\b",
        r"\bengineer\b",
        r"\bdeveloper\b",
        r"\bdesigner\b",
        r"\bintern\b",
        r"\bteacher\b",
        r"\blecturer\b",
        r"\bofficer\b",
        r"\bexecutive\b",
        r"\bassistant\b",
        r"\bsupervisor\b",
        r"\bdirector\b",
        r"\bleader\b",
        r"\bmember\b",
        r"\bvolunteer\b",
    ]

    for index in range(
        education_start + 1,
        len(lines)
    ):

        line = lines[index]

        # Training starts after experience.
        if re.match(
            r"^workshop\s+on\b",
            line,
            re.IGNORECASE
        ):
            break

        # Ignore obvious education-related lines.
        if (
            looks_like_degree(line)
            or re.search(
                r"\buniversity\b|\bcollege\b|\bschool\b",
                line,
                re.IGNORECASE
            )
            or re.search(
                r"\bCGPA\b|\bGPA\b|\bcoursework\b",
                line,
                re.IGNORECASE
            )
        ):
            continue

        for pattern in experience_title_patterns:

            if re.search(
                pattern,
                line,
                re.IGNORECASE
            ):
                experience_start = index
                break

        if experience_start is not None:
            break

    # ------------------------------------------------------
    # Separate education
    # ------------------------------------------------------

    if experience_start is not None:

        education_lines = lines[
            education_start:experience_start
        ]

    else:

        education_lines = lines[
            education_start:
        ]

    education_candidates = extract_education(
        "\n".join(
            education_lines
        )
    )

    # ------------------------------------------------------
    # Separate experience and training
    # ------------------------------------------------------

    experience_candidates = []
    training_candidates = []

    if experience_start is not None:

        experience_lines = lines[
            experience_start:
        ]

        training_start = None

        for index, line in enumerate(
            experience_lines
        ):

            if re.match(
                r"^workshop\s+on\b",
                line,
                re.IGNORECASE
            ):
                training_start = index
                break

        if training_start is not None:

            actual_experience_lines = (
                experience_lines[
                    :training_start
                ]
            )

            training_lines = (
                experience_lines[
                    training_start:
                ]
            )

            if actual_experience_lines:

                experience_candidates = extract_experience(
                    "\n".join(
                        actual_experience_lines
                    )
                )

            training_candidates = [
                line.strip()
                for line in training_lines
                if line.strip()
            ]

        else:

            experience_candidates = extract_experience(
                "\n".join(
                    experience_lines
                )
            )

    return (
        education_candidates,
        experience_candidates,
        training_candidates
    )
# ============================================================
# MAIN PARSER
# ============================================================

def parse_resume(text):

    text = normalize_text(text)

    sections = extract_sections(
        text
    )
    # --------------------------------------------------------
    # Normal section parsing
    # --------------------------------------------------------

    education = extract_education(
        sections.get(
            "education",
            ""
        )
    )

    experience = extract_experience(
        sections.get(
            "experience",
            ""
        )
    )

    projects = extract_projects(
        sections.get(
            "projects",
            ""
        )
    )

    # --------------------------------------------------------
    # Recover education / experience if PDF reading order
    # placed them elsewhere.
    # --------------------------------------------------------

    recovered_education = []
    recovered_experience = []
    recovered_training = []

    if (
        not education
        or not experience
    ):

        (
            recovered_education,
            recovered_experience,
            recovered_training
        ) = recover_misordered_sections(
            sections
        )

    if not education:
        education = recovered_education

    if not experience:
        experience = recovered_experience

    # --------------------------------------------------------
    # Training
    # --------------------------------------------------------

    training = recovered_training

    if not training:

        training_text = sections.get(
            "training",
            ""
        )

        if training_text:

            training = [
                line.strip()
                for line in training_text.split("\n")
                if line.strip()
            ]

    # --------------------------------------------------------
    # Leadership
    # --------------------------------------------------------

    leadership = []

    leadership_text = sections.get(
        "leadership",
        ""
    )

    if leadership_text:

        leadership = [
            line.strip()
            for line in leadership_text.split("\n")
            if line.strip()
        ]

    # --------------------------------------------------------
    # Final parsed result
    # --------------------------------------------------------

    contact_links = extract_contact_links(text)

    parsed_data = {

        "name": extract_name(text),

        "email": extract_email(text),

        "phone": extract_phone(text),

        "linkedin": contact_links["linkedin"],

        "github": contact_links["github"],

        "website": contact_links["website"],

        "contact": contact_links,

        "skills": extract_skills(
            sections.get(
                "skills",
                ""
            )
        ),
        "education": education,

        "experience": experience,

        "projects": projects,

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

        "leadership": leadership,

        "training": training,

        "sections": sections
    }

    return parsed_data