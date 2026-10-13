import re
from typing import Dict, List, Optional, Set, Tuple
from ..schemas.analysis import SkillItem

# Comprehensive, easily extensible taxonomy
# Format: Canonical Name: { "category": ..., "aliases": [...], "strict_regex": ... }
SKILL_TAXONOMY: Dict[str, Dict] = {
    # --- Programming Languages ---
    "Python": {"category": "Programming Languages", "aliases": ["python3", "python 3", "py"]},
    "Java": {"category": "Programming Languages", "aliases": ["core java", "java 8", "java 11", "java 17"]},
    "C++": {"category": "Programming Languages", "aliases": ["cpp", "c plus plus"]},
    "C": {"category": "Programming Languages", "aliases": [], "strict_pattern": r"(?:\bC\b(?:\s*[,/]\s*(?:C\+\+|C\#|Java|Python))|(?:programming in C\b)|(?:\bC language\b)|(?:\bembedded C\b))"},
    "C#": {"category": "Programming Languages", "aliases": ["csharp", "c sharp", ".net c#"]},
    "JavaScript": {"category": "Programming Languages", "aliases": ["js", "es6", "vanilla javascript", "javascript/typescript"]},
    "TypeScript": {"category": "Programming Languages", "aliases": ["ts"]},
    "SQL": {"category": "Programming Languages", "aliases": ["structured query language", "t-sql", "pl/sql"]},
    "Go (Golang)": {"category": "Programming Languages", "aliases": ["golang"], "strict_pattern": r"\b(?:golang|go programming|go language)\b"},
    "Rust": {"category": "Programming Languages", "aliases": ["rust-lang", "rust programming"]},
    "Ruby": {"category": "Programming Languages", "aliases": ["ruby on rails", "ror"]},
    "PHP": {"category": "Programming Languages", "aliases": ["php7", "php8"]},
    "Kotlin": {"category": "Programming Languages", "aliases": []},
    "Swift": {"category": "Programming Languages", "aliases": ["swiftui"]},
    "R": {"category": "Programming Languages", "aliases": [], "strict_pattern": r"(?:\bR\b(?:\s*[,/]\s*(?:Python|SAS|SPSS|SQL))|(?:\bR programming\b)|(?:\bR language\b))"},
    "Scala": {"category": "Programming Languages", "aliases": []},

    # --- AI & Machine Learning ---
    "Machine Learning": {"category": "AI & Machine Learning", "aliases": ["ml", "machine learning algorithms"]},
    "Deep Learning": {"category": "AI & Machine Learning", "aliases": ["dl", "deep neural networks", "neural networks"]},
    "Supervised Learning": {"category": "AI & Machine Learning", "aliases": ["supervised machine learning"]},
    "Unsupervised Learning": {"category": "AI & Machine Learning", "aliases": ["unsupervised machine learning", "clustering"]},
    "Natural Language Processing (NLP)": {"category": "AI & Machine Learning", "aliases": ["nlp", "natural language processing", "text processing"]},
    "Computer Vision": {"category": "AI & Machine Learning", "aliases": ["cv", "opencv", "image classification", "object detection"]},
    "PyTorch": {"category": "AI & Machine Learning", "aliases": ["torch"]},
    "TensorFlow": {"category": "AI & Machine Learning", "aliases": ["tf", "tensorflow 2"]},
    "Scikit-Learn": {"category": "AI & Machine Learning", "aliases": ["sklearn", "scikit learn"]},
    "Hugging Face": {"category": "AI & Machine Learning", "aliases": ["transformers", "huggingface"]},
    "Large Language Models (LLMs)": {"category": "AI & Machine Learning", "aliases": ["llm", "llms", "large language model", "generative ai", "genai", "rag", "langchain", "llamaindex"]},
    "Reinforcement Learning": {"category": "AI & Machine Learning", "aliases": ["rl"]},

    # --- Data & Analytics ---
    "Pandas": {"category": "Data & Analytics", "aliases": []},
    "NumPy": {"category": "Data & Analytics", "aliases": ["numpy"]},
    "SciPy": {"category": "Data & Analytics", "aliases": []},
    "Data Analysis": {"category": "Data & Analytics", "aliases": ["data analytics", "exploratory data analysis", "eda"]},
    "Data Visualization": {"category": "Data & Analytics", "aliases": ["matplotlib", "seaborn", "plotly", "tableau", "power bi", "powerbi"]},
    "Statistics": {"category": "Data & Analytics", "aliases": ["statistical modeling", "statistical analysis", "hypothesis testing", "a/b testing"]},
    "Apache Spark": {"category": "Data & Analytics", "aliases": ["spark", "pyspark"]},
    "Kafka": {"category": "Data & Analytics", "aliases": ["apache kafka"]},
    "Airflow": {"category": "Data & Analytics", "aliases": ["apache airflow"]},
    "Snowflake": {"category": "Data & Analytics", "aliases": []},
    "BigQuery": {"category": "Data & Analytics", "aliases": ["google bigquery"]},
    "Databricks": {"category": "Data & Analytics", "aliases": []},

    # --- Backend Development ---
    "FastAPI": {"category": "Backend Development", "aliases": ["fast api"]},
    "Flask": {"category": "Backend Development", "aliases": []},
    "Django": {"category": "Backend Development", "aliases": ["django rest framework", "drf"]},
    "REST APIs": {"category": "Backend Development", "aliases": ["rest", "restful", "restful api", "rest api", "rest apis", "restful apis"]},
    "GraphQL": {"category": "Backend Development", "aliases": []},
    "Microservices": {"category": "Backend Development", "aliases": ["microservice architecture", "distributed systems"]},
    "PostgreSQL": {"category": "Backend Development", "aliases": ["postgres", "pgsql"]},
    "MySQL": {"category": "Backend Development", "aliases": ["mariadb"]},
    "MongoDB": {"category": "Backend Development", "aliases": ["mongo", "nosql"]},
    "Redis": {"category": "Backend Development", "aliases": []},
    "Node.js": {"category": "Backend Development", "aliases": ["nodejs", "node js"]},
    "Express.js": {"category": "Backend Development", "aliases": ["express", "expressjs"]},
    "Spring Boot": {"category": "Backend Development", "aliases": ["spring", "spring framework"]},

    # --- Frontend Development ---
    "HTML": {"category": "Frontend Development", "aliases": ["html5"]},
    "CSS": {"category": "Frontend Development", "aliases": ["css3", "sass", "scss"]},
    "React": {"category": "Frontend Development", "aliases": ["reactjs", "react.js"]},
    "Next.js": {"category": "Frontend Development", "aliases": ["nextjs"]},
    "Vue.js": {"category": "Frontend Development", "aliases": ["vue", "vuejs"]},
    "Angular": {"category": "Frontend Development", "aliases": ["angularjs", "angular 2+"]},
    "Tailwind CSS": {"category": "Frontend Development", "aliases": ["tailwind", "tailwindcss"]},

    # --- Cloud Computing ---
    "AWS": {"category": "Cloud Computing", "aliases": ["amazon web services"]},
    "Amazon EC2": {"category": "Cloud Computing", "aliases": ["ec2"]},
    "Amazon S3": {"category": "Cloud Computing", "aliases": ["s3"]},
    "AWS IAM": {"category": "Cloud Computing", "aliases": ["iam"]},
    "Amazon CloudWatch": {"category": "Cloud Computing", "aliases": ["cloudwatch"]},
    "AWS Lambda": {"category": "Cloud Computing", "aliases": ["lambda", "serverless lambda"]},
    "Google Cloud (GCP)": {"category": "Cloud Computing", "aliases": ["gcp", "google cloud platform", "google cloud"]},
    "Microsoft Azure": {"category": "Cloud Computing", "aliases": ["azure"]},

    # --- DevOps & Infrastructure ---
    "Git": {"category": "DevOps & Infrastructure", "aliases": ["github", "gitlab", "bitbucket", "version control"]},
    "GitHub Actions": {"category": "DevOps & Infrastructure", "aliases": ["gh actions", "github action"]},
    "CI/CD": {"category": "DevOps & Infrastructure", "aliases": ["continuous integration", "continuous deployment", "cicd"]},
    "Jenkins": {"category": "DevOps & Infrastructure", "aliases": []},
    "Docker": {"category": "DevOps & Infrastructure", "aliases": ["dockerization", "containerization", "containers"]},
    "Kubernetes": {"category": "DevOps & Infrastructure", "aliases": ["k8s"]},
    "Terraform": {"category": "DevOps & Infrastructure", "aliases": ["iac", "infrastructure as code"]},
    "Linux": {"category": "DevOps & Infrastructure", "aliases": ["unix", "bash", "shell scripting"]},

    # --- General Engineering ---
    "Data Structures": {"category": "General Engineering", "aliases": ["dsa", "data structures and algorithms"]},
    "Algorithms": {"category": "General Engineering", "aliases": ["algorithm design"]},
    "Testing": {"category": "General Engineering", "aliases": ["pytest", "unit testing", "integration testing", "test automation", "tdd"]},
    "Debugging": {"category": "General Engineering", "aliases": ["troubleshooting", "root cause analysis"]},
    "System Design": {"category": "General Engineering", "aliases": ["software architecture", "high level design", "low level design"]},
    "Agile / Scrum": {"category": "General Engineering", "aliases": ["scrum", "agile", "sprints", "kanban"]},
}


class SkillExtractor:
    def __init__(self, taxonomy: Optional[Dict[str, Dict]] = None):
        self.taxonomy = taxonomy or SKILL_TAXONOMY
        self._compiled_patterns = self._build_compiled_patterns()

    def _build_compiled_patterns(self) -> Dict[str, List[re.Pattern]]:
        compiled = {}
        for canonical, info in self.taxonomy.items():
            patterns = []
            
            # Check if strict custom pattern is specified (for short/ambiguous words like C, R, Go)
            if "strict_pattern" in info:
                patterns.append(re.compile(info["strict_pattern"], re.IGNORECASE))
            else:
                # Word boundary pattern for canonical name
                # Handle special chars like C++
                escaped_canonical = re.escape(canonical)
                patterns.append(re.compile(rf"(?<!\w){escaped_canonical}(?!\w)", re.IGNORECASE))
                
                # Aliases
                for alias in info.get("aliases", []):
                    escaped_alias = re.escape(alias)
                    patterns.append(re.compile(rf"(?<!\w){escaped_alias}(?!\w)", re.IGNORECASE))

            compiled[canonical] = patterns
        return compiled

    def extract_skills(self, text: str) -> Dict[str, Dict]:
        """
        Extracts skills present in text, returning a mapping of:
        Canonical Name -> { "category": str, "evidence": str, "snippets": List[str] }
        """
        results = {}
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        for canonical, patterns in self._compiled_patterns.items():
            matched = False
            evidence_snippets = []

            for pattern in patterns:
                for line in lines:
                    match = pattern.search(line)
                    if match:
                        matched = True
                        evidence_snippets.append(line)
                        if len(evidence_snippets) >= 2:
                            break
                if matched:
                    break

            if matched:
                category = self.taxonomy[canonical]["category"]
                snippet = evidence_snippets[0] if evidence_snippets else f"Mentioned: {canonical}"
                results[canonical] = {
                    "category": category,
                    "evidence": snippet,
                    "snippets": evidence_snippets
                }

        return results

    def split_job_description_requirements(self, jd_text: str) -> Tuple[str, str]:
        """
        Splits job description into (required_section_text, preferred_section_text).
        If no explicit preferred section is found, returns (jd_text, "").
        """
        preferred_markers = [
            r"(?:preferred|nice to have|desired|bonus points|good to have|plus points|preferred qualifications|preferred skills|additional qualifications)"
        ]
        required_markers = [
            r"(?:required qualifications|minimum qualifications|must have|requirements|what you need|qualifications|what we are looking for|basic qualifications)"
        ]

        pattern_pref = re.compile(rf"(?:\n|^)\s*(?:[\#\*\-\s]*)(?:{'|'.join(preferred_markers)})[:\s]*", re.IGNORECASE)
        match_pref = pattern_pref.search(jd_text)

        if match_pref:
            pref_start = match_pref.start()
            required_part = jd_text[:pref_start]
            preferred_part = jd_text[pref_start:]
            return required_part, preferred_part
        
        return jd_text, ""

    def compare_skills(
        self,
        resume_text: str,
        jd_text: str
    ) -> Tuple[List[SkillItem], List[SkillItem], List[SkillItem], Dict[str, float]]:
        """
        Compares skills between resume and job description.
        Returns:
            matching_skills: List[SkillItem]
            missing_skills: List[SkillItem]
            additional_skills: List[SkillItem]
            coverage_stats: {"required_coverage": float, "preferred_coverage": Optional[float]}
        """
        resume_skills = self.extract_skills(resume_text)
        
        # Split JD into required vs preferred
        req_text, pref_text = self.split_job_description_requirements(jd_text)
        
        req_jd_skills = self.extract_skills(req_text)
        pref_jd_skills = self.extract_skills(pref_text) if pref_text else {}

        # Resolve duplicates if a skill appeared in both
        for skill in req_jd_skills:
            if skill in pref_jd_skills:
                del pref_jd_skills[skill]

        # All JD skills
        all_jd_skills = {**req_jd_skills, **pref_jd_skills}

        matching: List[SkillItem] = []
        missing: List[SkillItem] = []
        additional: List[SkillItem] = []

        # Find matching and missing skills from JD
        for skill_name, jd_info in all_jd_skills.items():
            is_req = skill_name in req_jd_skills
            category = jd_info["category"]
            
            if skill_name in resume_skills:
                matching.append(
                    SkillItem(
                        name=skill_name,
                        category=category,
                        is_required=is_req,
                        evidence_snippet=resume_skills[skill_name]["evidence"],
                        section_found="Resume"
                    )
                )
            else:
                missing.append(
                    SkillItem(
                        name=skill_name,
                        category=category,
                        is_required=is_req,
                        evidence_snippet=jd_info["evidence"],
                        section_found="Job Description"
                    )
                )

        # Additional skills found in resume but not mentioned in JD
        for skill_name, res_info in resume_skills.items():
            if skill_name not in all_jd_skills:
                additional.append(
                    SkillItem(
                        name=skill_name,
                        category=res_info["category"],
                        is_required=False,
                        evidence_snippet=res_info["evidence"],
                        section_found="Resume"
                    )
                )

        # Sort matching, missing, additional
        matching.sort(key=lambda s: (not s.is_required, s.category, s.name))
        missing.sort(key=lambda s: (not s.is_required, s.category, s.name))
        additional.sort(key=lambda s: (s.category, s.name))

        # Calculate coverage scores
        req_total = len(req_jd_skills)
        req_matched = sum(1 for s in matching if s.name in req_jd_skills)
        req_coverage = (req_matched / req_total * 100.0) if req_total > 0 else 100.0

        pref_total = len(pref_jd_skills)
        pref_coverage = None
        if pref_total > 0:
            pref_matched = sum(1 for s in matching if s.name in pref_jd_skills)
            pref_coverage = (pref_matched / pref_total * 100.0)

        coverage_stats = {
            "required_coverage": round(req_coverage, 2),
            "preferred_coverage": round(pref_coverage, 2) if pref_coverage is not None else None,
            "required_total": float(req_total),
            "preferred_total": float(pref_total)
        }

        return matching, missing, additional, coverage_stats
