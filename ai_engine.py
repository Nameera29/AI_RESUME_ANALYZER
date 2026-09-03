import os
import json
import re
import time
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")

genai_client = None
if API_KEY and not API_KEY.startswith("YOUR_") and len(API_KEY) > 20:
    try:
        from google import genai
        from google.genai import types
        genai_client = genai.Client(
            api_key=API_KEY,
            http_options=types.HttpOptions(timeout=12000)
        )

    except Exception as e:
        logger.warning(f"Could not initialize google.genai client: {e}")
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=API_KEY)
            genai_client = "legacy"
        except Exception as le:
            logger.warning(f"Could not initialize legacy google.generativeai client: {le}")



def clean_json_string(response_text):
    """
    Strips markdown code fences (```json ... ```) from model output.
    """
    text = response_text.strip()
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1)
    return text.strip()


def heuristic_analyze_resume(resume_text):
    """
    Fast, highly optimized Python local engine.
    Extracts skills, calculates scores, and identifies gaps in < 15 milliseconds.
    """
    text_lower = resume_text.lower()
    words = set(re.findall(r'\b[a-zA-Z0-9+#.-]+\b', text_lower))
    lines = [l.strip() for l in resume_text.split('\n') if l.strip()]
    word_count = len(text_lower.split())

    tech_skills_db = {
        'Python': ['python', 'py', 'django', 'flask', 'fastapi', 'pandas', 'numpy'],
        'Java': ['java', 'spring', 'springboot', 'hibernate', 'maven', 'gradle'],
        'JavaScript / TypeScript': ['javascript', 'js', 'typescript', 'ts', 'node', 'nodejs', 'express', 'react', 'reactjs', 'vue', 'angular', 'next.js', 'nextjs'],
        'C / C++': ['c++', 'cpp', 'c language', 'stl'],
        'Web Development': ['html', 'css', 'bootstrap', 'tailwind', 'flexbox', 'grid', 'web development', 'frontend', 'backend', 'full stack', 'fullstack'],
        'Databases': ['sql', 'mysql', 'postgresql', 'postgres', 'sqlite', 'mongodb', 'redis', 'database', 'nosql', 'orm'],
        'Cloud & DevOps': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'k8s', 'ci/cd', 'git', 'github', 'gitlab', 'linux', 'bash', 'nginx'],
        'AI / Machine Learning': ['ai', 'machine learning', 'ml', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn', 'nlp', 'computer vision', 'gemini', 'openai']
    }

    soft_skills_db = [
        'communication', 'teamwork', 'collaboration', 'leadership', 'problem solving',
        'critical thinking', 'time management', 'adaptability', 'agile', 'scrum',
        'project management', 'analytical', 'creative'
    ]

    found_tech_skills = []
    for skill_name, keywords in tech_skills_db.items():
        if any(kw in text_lower for kw in keywords):
            found_tech_skills.append(skill_name)

    granular_skills = [
        'Python', 'Django', 'Flask', 'Java', 'C++', 'JavaScript', 'React', 'Node.js',
        'SQL', 'PostgreSQL', 'MongoDB', 'Docker', 'AWS', 'Git', 'HTML', 'CSS', 'REST API'
    ]
    specific_found = [s for s in granular_skills if re.search(r'\b' + re.escape(s.lower()) + r'\b', text_lower)]

    found_soft_skills = [s.capitalize() for s in soft_skills_db if s in text_lower]
    if not found_soft_skills:
        found_soft_skills = ['Problem Solving', 'Communication', 'Teamwork']

    role_definitions = [
        {
            'title': 'Full-Stack Software Engineer',
            'required': ['Python', 'JavaScript / TypeScript', 'Web Development', 'Databases'],
            'missing_candidates': ['Docker', 'AWS', 'CI/CD', 'TypeScript']
        },
        {
            'title': 'Python / Django Developer',
            'required': ['Python', 'Web Development', 'Databases'],
            'missing_candidates': ['Docker', 'Redis', 'REST API', 'PostgreSQL']
        },
        {
            'title': 'Backend Developer',
            'required': ['Databases', 'Python'],
            'missing_candidates': ['Microservices', 'Docker', 'Kubernetes', 'System Design']
        },
        {
            'title': 'Frontend Developer',
            'required': ['Web Development', 'JavaScript / TypeScript'],
            'missing_candidates': ['React', 'TypeScript', 'TailwindCSS', 'Redux']
        },
        {
            'title': 'Data & AI Engineer',
            'required': ['Python', 'AI / Machine Learning', 'Databases'],
            'missing_candidates': ['PyTorch', 'TensorFlow', 'Apache Spark', 'MLOps']
        }
    ]

    detected_roles = []
    for role in role_definitions:
        matches = [s for s in role['required'] if s in found_tech_skills]
        match_percentage = int((len(matches) / max(1, len(role['required']))) * 85) + (10 if word_count > 150 else 0)
        match_percentage = min(95, max(50, match_percentage))

        missing_for_role = [s for s in role['missing_candidates'] if s.lower() not in text_lower]

        detected_roles.append({
            'title': role['title'],
            'match_percentage': match_percentage,
            'matching_skills': matches if matches else ['General Programming'],
            'missing_skills': missing_for_role[:3]
        })

    detected_roles.sort(key=lambda x: x['match_percentage'], reverse=True)
    top_roles = detected_roles[:3]

    has_contact = any(k in text_lower for k in ['email', '@', 'phone', 'linkedin', 'github', 'mobile', 'contact'])
    has_education = any(k in text_lower for k in ['education', 'university', 'bachelor', 'b.tech', 'degree', 'college'])
    has_experience = any(k in text_lower for k in ['experience', 'work', 'internship', 'employment', 'position'])
    has_projects = any(k in text_lower for k in ['project', 'projects', 'built', 'developed'])
    has_skills_section = any(k in text_lower for k in ['skill', 'skills', 'technologies', 'proficiencies'])

    completeness = 50
    if has_contact: completeness += 10
    if has_education: completeness += 10
    if has_experience: completeness += 10
    if has_projects: completeness += 10
    if has_skills_section: completeness += 10

    technical_strength = min(95, max(45, len(specific_found) * 12 + len(found_tech_skills) * 8))
    project_impact = 70 if has_projects else 50
    if any(re.search(r'\b\d+%\b|\b\d+x\b|\b\$\d+|\b\d+ users\b', line, re.I) for line in lines):
        project_impact += 15

    role_readiness = int((technical_strength + project_impact + completeness) / 3)
    overall_score = int(technical_strength * 0.35 + project_impact * 0.25 + completeness * 0.25 + role_readiness * 0.15)
    overall_score = min(98, max(45, overall_score))

    potential_missing = ['Docker', 'AWS Cloud', 'CI/CD Pipelines', 'System Design', 'Unit Testing / PyTest', 'RESTful APIs']
    missing_skills = []
    for ms in potential_missing:
        if ms.lower() not in text_lower:
            missing_skills.append({
                'skill': ms,
                'importance': 'High' if ms in ['Docker', 'Git', 'RESTful APIs'] else 'Medium',
                'reason': f"Adding {ms} significantly increases match rate for top technical software roles."
            })

    strengths = []
    if specific_found:
        strengths.append(f"Demonstrates core proficiency in {', '.join(specific_found[:4])}.")
    if has_projects:
        strengths.append("Includes dedicated projects demonstrating applied software development skills.")
    if has_education:
        strengths.append("Clearly states educational background and academic credentials.")
    if len(lines) > 10:
        strengths.append("Well-structured document formatting with defined sections.")

    weaknesses = []
    if not any(re.search(r'\b\d+%\b|\b\d+x\b', line, re.I) for line in lines):
        weaknesses.append("Lacks quantifiable metrics (e.g. '% improvement', 'x faster', 'served N users') in project/work bullets.")
    if 'docker' not in text_lower and 'aws' not in text_lower:
        weaknesses.append("Missing deployment or cloud platform experience (e.g., Docker, AWS, Heroku, Vercel).")
    if not (re.search(r'github\.com|linkedin\.com', text_lower)):
        weaknesses.append("Missing explicit GitHub or LinkedIn profile links for verified code portfolio.")

    actionable_suggestions = [
        "Add quantifiable outcomes to project bullet points (e.g., 'Improved API response time by 30%' or 'Handled 500+ daily queries').",
        "Include links to your GitHub profile and live project demos at the top of your resume.",
        "Add containerization (Docker) or basic Cloud (AWS/GCP) project experience to your skills section.",
        "Ensure bullet points start with strong action verbs (e.g., 'Engineered', 'Optimized', 'Architected', 'Implemented').",
        "Tailor your technical summary to highlight target job roles like " + (top_roles[0]['title'] if top_roles else "Software Engineer") + "."
    ]

    return {
        'overall_score': overall_score,
        'score_breakdown': {
            'technical_strength': technical_strength,
            'project_impact': project_impact,
            'completeness': completeness,
            'role_readiness': role_readiness,
            'explanation': f"Calculated based on {len(specific_found)} core technical skills, section completeness ({completeness}%), and project metric impact."
        },
        'summary': f"Candidate demonstrates solid foundational knowledge in software development with key strengths in {', '.join(specific_found[:3]) if specific_found else 'core programming'}. Recommended for target roles in {top_roles[0]['title'] if top_roles else 'Software Development'}.",
        'important_skills': {
            'technical_skills': specific_found if specific_found else found_tech_skills,
            'soft_skills': found_soft_skills
        },
        'missing_skills': missing_skills[:4],
        'detected_roles': top_roles,
        'strengths': strengths if strengths else ["Clear layout and readable formatting."],
        'weaknesses': weaknesses if weaknesses else ["Could benefit from additional project metrics."],
        'actionable_suggestions': actionable_suggestions
    }


def _validate_ai_qualitative(data):
    """
    Validates that the Gemini AI response contains the expected fields
    with the correct types before merging into the local result.
    Returns (is_valid: bool, issues: list[str]).
    """
    issues = []
    if not isinstance(data, dict):
        return False, ["Response is not a JSON object."]
    if 'summary' in data and not isinstance(data['summary'], str):
        issues.append("'summary' is not a string.")
    if 'strengths' in data and not isinstance(data['strengths'], list):
        issues.append("'strengths' is not a list.")
    if 'weaknesses' in data and not isinstance(data['weaknesses'], list):
        issues.append("'weaknesses' is not a list.")
    if 'actionable_suggestions' in data and not isinstance(data['actionable_suggestions'], list):
        issues.append("'actionable_suggestions' is not a list.")
    return len(issues) == 0, issues


def _call_gemini_with_retry(prompt, max_retries=2):
    """
    Calls the Gemini API with up to max_retries attempts on transient errors
    (503 UNAVAILABLE, 504 DEADLINE_EXCEEDED).
    Returns response text on success, raises the last exception on failure.
    """
    RETRYABLE_CODES = {503, 504}
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            response = genai_client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            last_exception = e
            error_str = str(e)
            # Check if this is a retryable HTTP error
            is_retryable = any(f"{code}" in error_str for code in RETRYABLE_CODES)
            if is_retryable and attempt < max_retries:
                wait_s = attempt * 1.5  # 1.5s, then 3s
                logger.warning(
                    f"Gemini API transient error on attempt {attempt}/{max_retries}: "
                    f"{error_str[:120]}. Retrying in {wait_s}s..."
                )
                time.sleep(wait_s)
            else:
                break

    raise last_exception


def analyze_resume(resume_text):
    """
    Hybrid Analysis Engine:
    1. Computes scores, skills, gaps, and roles locally in Python (Instant).
    2. Sends a compact summary to Gemini for qualitative AI insights with retry logic.
    3. Validates the AI response before merging.
    4. Falls back gracefully to local analysis if the AI service is unavailable.

    Always returns analysis_source = 'AI' | 'Hybrid' | 'Local'.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text is empty. Please upload a valid resume document.")

    # Step 1: Instant Local Computations (always runs)
    local_result = heuristic_analyze_resume(resume_text)
    local_result['analysis_source'] = 'Local'

    # Step 2: Gemini AI qualitative refinement (optional, with retry)
    if not (genai_client and genai_client != "legacy"):
        logger.info("Gemini client not available. Using local analysis only.")
        return local_result

    try:
        tech_str = ", ".join(local_result['important_skills']['technical_skills'][:6])
        role_str = (
            local_result['detected_roles'][0]['title']
            if local_result['detected_roles']
            else "Software Developer"
        )
        missing_str = ", ".join([g['skill'] for g in local_result['missing_skills']])

        compact_prompt = f"""You are a professional resume analyst. Given the data below, return ONLY valid raw JSON (no markdown, no code fences).

Role Target: {role_str}
Found Skills: {tech_str}
Skill Gaps: {missing_str}
Resume Score: {local_result['overall_score']}/100

Return exactly this JSON structure:
{{
  "summary": "2-sentence executive summary of the candidate.",
  "strengths": ["Strength 1", "Strength 2", "Strength 3"],
  "weaknesses": ["Weakness 1", "Weakness 2"],
  "actionable_suggestions": ["Actionable advice 1", "Actionable advice 2", "Actionable advice 3"]
}}"""

        # Call with retry logic
        response_text = _call_gemini_with_retry(compact_prompt, max_retries=2)

        # Parse JSON response
        try:
            cleaned = clean_json_string(response_text)
            ai_qualitative = json.loads(cleaned)
        except json.JSONDecodeError as json_err:
            logger.warning(
                f"Gemini returned non-JSON response (JSONDecodeError: {json_err}). "
                f"Raw response (first 300 chars): {response_text[:300]!r}"
            )
            return local_result

        # Validate structure before merging
        is_valid, validation_issues = _validate_ai_qualitative(ai_qualitative)
        if not is_valid:
            logger.warning(
                f"Gemini response failed validation: {validation_issues}. "
                f"Falling back to local results."
            )
            return local_result

        # Safely merge AI qualitative fields (preserving local values if AI field is empty)
        if isinstance(ai_qualitative.get('summary'), str) and ai_qualitative['summary'].strip():
            local_result['summary'] = ai_qualitative['summary'].strip()

        if (isinstance(ai_qualitative.get('strengths'), list)
                and len(ai_qualitative['strengths']) > 0):
            local_result['strengths'] = [
                str(s) for s in ai_qualitative['strengths'] if str(s).strip()
            ]

        if (isinstance(ai_qualitative.get('weaknesses'), list)
                and len(ai_qualitative['weaknesses']) > 0):
            local_result['weaknesses'] = [
                str(w) for w in ai_qualitative['weaknesses'] if str(w).strip()
            ]

        if (isinstance(ai_qualitative.get('actionable_suggestions'), list)
                and len(ai_qualitative['actionable_suggestions']) > 0):
            local_result['actionable_suggestions'] = [
                str(s) for s in ai_qualitative['actionable_suggestions'] if str(s).strip()
            ]

        local_result['analysis_source'] = 'AI'
        logger.info(
            f"Hybrid Engine: Gemini AI qualitative insights merged successfully "
            f"(score={local_result['overall_score']})."
        )

    except Exception as e:
        # Log full error server-side; do NOT propagate to user
        logger.warning(
            f"Gemini API unavailable after retries: {type(e).__name__}: {e}. "
            f"Analysis completed using local engine only."
        )
        local_result['analysis_source'] = 'Local'

    return local_result


def match_job_description(resume_text, job_description):
    """
    Upgraded 100% Local ATS Job Description Matcher.
    - Expanded 40+ term tech map
    - Fair weighted score formula (tech 60% + keywords 40%)
    - JD-aware actionable recommendations
    - Returns coverage metadata for the UI
    Runs instantaneously in Python (< 15 ms).
    """
    if not job_description or not job_description.strip():
        return None

    res_lower = resume_text.lower()
    jd_lower = job_description.lower()

    # ── Expanded Tech / Tool Map (40+ recognised terms) ──────────────────
    TECH_MAP = {
        # Languages
        'python': 'Python', 'java': 'Java', 'javascript': 'JavaScript',
        'typescript': 'TypeScript', 'c++': 'C++', 'cpp': 'C++',
        'golang': 'Go', 'ruby': 'Ruby', 'php': 'PHP', 'kotlin': 'Kotlin',
        'swift': 'Swift', 'scala': 'Scala', 'rust': 'Rust',
        # Web Frameworks
        'django': 'Django', 'flask': 'Flask', 'fastapi': 'FastAPI',
        'react': 'React', 'angular': 'Angular', 'vue': 'Vue.js',
        'nodejs': 'Node.js', 'express': 'Express.js', 'nextjs': 'Next.js',
        'spring': 'Spring Boot',
        # Databases
        'sql': 'SQL', 'postgresql': 'PostgreSQL', 'postgres': 'PostgreSQL',
        'mysql': 'MySQL', 'mongodb': 'MongoDB', 'redis': 'Redis',
        'sqlite': 'SQLite', 'elasticsearch': 'Elasticsearch',
        # Cloud & DevOps
        'aws': 'AWS', 'azure': 'Azure', 'gcp': 'GCP',
        'docker': 'Docker', 'kubernetes': 'Kubernetes', 'k8s': 'Kubernetes',
        'terraform': 'Terraform', 'ansible': 'Ansible',
        'jenkins': 'Jenkins', 'gitlab': 'GitLab CI', 'github': 'GitHub Actions',
        'ci/cd': 'CI/CD',
        # Tools & Practices
        'git': 'Git', 'linux': 'Linux', 'nginx': 'Nginx',
        'rest': 'REST API', 'graphql': 'GraphQL', 'grpc': 'gRPC',
        'microservices': 'Microservices', 'agile': 'Agile',
        'html': 'HTML5', 'css': 'CSS3', 'tailwind': 'Tailwind CSS',
        # AI / Data
        'tensorflow': 'TensorFlow', 'pytorch': 'PyTorch',
        'pandas': 'Pandas', 'numpy': 'NumPy', 'scikit': 'Scikit-learn',
    }

    STOP_WORDS = {
        'and', 'the', 'for', 'with', 'you', 'that', 'this', 'have', 'will',
        'are', 'from', 'your', 'our', 'work', 'team', 'ability', 'must',
        'experience', 'skills', 'role', 'job', 'responsibilities',
        'requirements', 'looking', 'candidate', 'strong', 'position',
        'plus', 'bonus', 'preferred', 'required', 'minimum', 'years',
        'develop', 'design', 'implement', 'build', 'write', 'use', 'using',
        'knowledge', 'proficient', 'familiar', 'understanding', 'ability',
        'excellent', 'good', 'great', 'high', 'key', 'also', 'well',
    }

    # ── Tokenise JD ──────────────────────────────────────────────────────
    raw_jd_words = re.findall(r'\b[a-zA-Z0-9+#./\-]{2,}\b', jd_lower)
    jd_tokens = [w for w in raw_jd_words if w not in STOP_WORDS and not w.isdigit()]

    # Split into tech keywords (known) vs. general keywords
    jd_tech_tokens = [t for t in jd_tokens if t in TECH_MAP]
    jd_general_tokens = list({
        t for t in jd_tokens
        if t not in TECH_MAP and len(t) >= 4
    })

    # ── Matching / Missing ───────────────────────────────────────────────
    seen_display = set()
    matching_tech, missing_tech = [], []
    for kw in dict.fromkeys(jd_tech_tokens):          # preserve order, dedupe
        display = TECH_MAP[kw]
        if display in seen_display:
            continue
        seen_display.add(display)
        if kw in res_lower or display.lower() in res_lower:
            matching_tech.append(display)
        else:
            missing_tech.append(display)

    matching_general, missing_general = [], []
    seen_gen = set()
    for kw in jd_general_tokens:
        display = kw.capitalize()
        if display in seen_gen or display in seen_display:
            continue
        seen_gen.add(display)
        if kw in res_lower:
            matching_general.append(display)
        else:
            missing_general.append(display)

    # Combine: tech first, then general
    all_matching = matching_tech + [g for g in matching_general if g not in matching_tech]
    all_missing  = missing_tech  + [g for g in missing_general  if g not in missing_tech]

    # ── Score Formula ─────────────────────────────────────────────────────
    # Weighted: tech skills count for 60%, general keywords for 40%
    tech_total = max(1, len(jd_tech_tokens))
    gen_total  = max(1, len(jd_general_tokens))

    tech_ratio = len(matching_tech)    / tech_total
    gen_ratio  = len(matching_general) / gen_total

    raw_score   = (tech_ratio * 0.60 + gen_ratio * 0.40) * 100
    ats_score   = int(min(97, max(30, round(raw_score))))

    # Coverage stats for the UI
    total_jd_kw   = len(set(jd_tech_tokens)) + len(jd_general_tokens)
    matched_count = len(matching_tech) + len(matching_general)
    coverage_pct  = int((matched_count / max(1, total_jd_kw)) * 100)

    # Score tier labelling
    if ats_score >= 80:
        score_tier, score_color = 'Excellent Match', 'success-color'
    elif ats_score >= 65:
        score_tier, score_color = 'Good Match',      'accent-cyan'
    elif ats_score >= 50:
        score_tier, score_color = 'Fair Match',      'warning-color'
    else:
        score_tier, score_color = 'Needs Work',      'danger-color'

    # ── Relevant Experience Summary ───────────────────────────────────────
    relevant_experience = []
    if matching_tech:
        relevant_experience.append(
            f"Strong alignment on core technical requirements: {', '.join(matching_tech[:5])}."
        )
    if ats_score >= 65:
        relevant_experience.append(
            "Resume demonstrates relevant industry terminology and tooling aligned with this role."
        )
    else:
        relevant_experience.append(
            "Resume contains foundational technical skills applicable to this role — targeting is recommended."
        )

    # ── JD-Aware Recommendations ──────────────────────────────────────────
    recommendations = []

    if missing_tech:
        top_missing = ', '.join(missing_tech[:5])
        recommendations.append(
            f"Add the following missing technical skills to your Skills section if you have experience with them: {top_missing}."
        )

    if missing_general:
        top_gen = ', '.join(missing_general[:4])
        recommendations.append(
            f"Naturally incorporate these JD keywords into your experience bullets or summary: {top_gen}."
        )

    if ats_score < 55:
        recommendations.append(
            "Your resume needs significant re-targeting for this role. Rewrite the Professional Summary "
            "to include the job title and 3–4 core tools from the Job Description."
        )
    elif ats_score < 75:
        recommendations.append(
            "Increase keyword density: mirror the exact phrasing used in the Job Description for tools and "
            "frameworks (e.g., use 'PostgreSQL' instead of 'relational database')."
        )
    else:
        recommendations.append(
            "Strong keyword match. Focus on quantifying achievements — add metrics such as '30% faster', "
            "'10k daily users', or 'reduced cost by $X' to stand out at the interview stage."
        )

    recommendations.append(
        "Ensure your resume's Professional Summary opens with the target job title and 2–3 of the most "
        "critical skills from the Job Description to pass automated screening systems."
    )
    recommendations.append(
        "Tailor your project descriptions to directly reference the responsibilities listed in the Job "
        "Description — ATS systems reward specificity and exact terminology."
    )

    return {
        # ── Existing keys (backwards-compatible) ──────────────────────────
        'match_score':         ats_score,
        'matching_skills':     all_matching[:12],
        'missing_skills':      all_missing[:10],
        'relevant_experience': relevant_experience,
        'recommendations':     recommendations,
        # ── New metadata keys (used by the improved UI) ───────────────────
        'matched_count':       matched_count,
        'jd_total_keywords':   total_jd_kw,
        'keyword_coverage_pct': coverage_pct,
        'score_tier':          score_tier,
        'score_color':         score_color,
    }