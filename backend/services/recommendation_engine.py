import re
from typing import Dict, List, Optional, Tuple
from ..schemas.analysis import (
    SkillItem,
    RecommendationItem,
    ExperienceAnalysis
)

class RecommendationEngine:
    def __init__(self):
        pass

    def extract_years_of_experience(self, text: str) -> Optional[int]:
        """Extracts requested or stated years of experience from text."""
        match = re.search(r"\b(\d{1,2})\+?\s*(?:to\s*\d{1,2})?\s*(?:years|yrs)(?:\s+of)?\s*(?:experience|exp)?\b", text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, TypeError):
                return None
        return None

    def analyze_experience_and_qualifications(
        self,
        resume_text: str,
        jd_text: str,
        detected_sections: List[str]
    ) -> ExperienceAnalysis:
        """
        Analyzes resume sections, degree qualifications, and years of experience alignment.
        Does not fabricate facts.
        """
        observations: List[str] = []
        education_found: List[str] = []

        # 1. Section presence observations
        essential_sections = ["Skills", "Work Experience", "Projects", "Education"]
        missing_sections = [sec for sec in essential_sections if not any(sec.lower() in d.lower() for d in detected_sections)]
        if missing_sections:
            observations.append(
                f"Your resume appears to be missing explicit headings for: {', '.join(missing_sections)}. "
                "Standard section headings help applicant tracking systems (ATS) correctly categorize your credentials."
            )
        else:
            observations.append(
                f"Core resume sections detected: {', '.join(detected_sections)}."
            )

        # 2. Education extraction
        edu_patterns = [
            (r"\b(?:bachelor|b\.s|b\.tech|b\.e|bca)\b", "Bachelor's Degree or Equivalent"),
            (r"\b(?:master|m\.s|m\.tech|m\.e|mca)\b", "Master's Degree or Equivalent"),
            (r"\b(?:ph\.?d|doctorate)\b", "Doctorate / Ph.D."),
            (r"\b(?:diploma|associate)\b", "Associate Degree or Diploma"),
        ]
        for pattern, label in edu_patterns:
            if re.search(pattern, resume_text, re.IGNORECASE):
                education_found.append(label)

        # Check if JD specifies degree
        jd_degree_req = []
        for pattern, label in edu_patterns:
            if re.search(pattern, jd_text, re.IGNORECASE):
                jd_degree_req.append(label)

        if jd_degree_req:
            if any(deg in education_found for deg in jd_degree_req):
                observations.append(
                    f"Education alignment: Job description seeks {', '.join(jd_degree_req)}, which appears represented in your background."
                )
            elif not education_found:
                observations.append(
                    f"Job description mentions {', '.join(jd_degree_req)}. Ensure your education section clearly lists your highest completed degree and major."
                )
            else:
                observations.append(
                    f"Job specifies: {', '.join(jd_degree_req)}. Resume lists: {', '.join(education_found)}."
                )

        # 3. Years of experience comparison
        jd_years = self.extract_years_of_experience(jd_text)
        res_years = self.extract_years_of_experience(resume_text)
        
        years_comparison = None
        if jd_years:
            if res_years:
                if res_years >= jd_years:
                    years_comparison = (
                        f"Experience target aligned: Job description requests ~{jd_years}+ years, "
                        f"and your resume mentions ~{res_years}+ years of professional background."
                    )
                else:
                    years_comparison = (
                        f"Experience gap note: Job description specifies ~{jd_years}+ years, "
                        f"while resume explicitly mentions ~{res_years} years. Ensure your work history demonstrates the depth required."
                    )
            else:
                years_comparison = (
                    f"Job description specifies {jd_years}+ years of relevant experience. "
                    "Your resume does not explicitly quantify total years in the summary; consider stating your years of experience clearly if you meet this requirement."
                )
        else:
            years_comparison = "Job description does not specify an exact required minimum number of years of experience."

        # 4. Action-verb and metrics density check
        metric_matches = re.findall(r"\b(?:\d+[\%\+]?|\$[\d,]+|\d+x)\b", resume_text)
        if len(metric_matches) < 3:
            observations.append(
                "Limited quantified metrics found. Resumes that include measurable outcomes (e.g. '% latency reduced', 'X users served', 'Y automated tasks') demonstrate greater impact."
            )
        else:
            observations.append(
                f"Observed quantified metrics ({len(metric_matches)} instances found), demonstrating measurable project results."
            )

        return ExperienceAnalysis(
            sections_detected=detected_sections,
            observations=observations,
            education_detected=education_found,
            experience_years_comparison=years_comparison
        )

    def generate_recommendations(
        self,
        matching_skills: List[SkillItem],
        missing_skills: List[SkillItem],
        additional_skills: List[SkillItem],
        resume_text: str,
        target_job_title: Optional[str] = None
    ) -> List[RecommendationItem]:
        """
        Generates practical, actionable recommendations without fabricating false qualifications.
        """
        recommendations: List[RecommendationItem] = []
        role_title = target_job_title or "the target role"

        # 1. Missing Required Skills
        req_missing = [s for s in missing_skills if s.is_required]
        if req_missing:
            top_missing = req_missing[:4]
            skill_names = ", ".join([s.name for s in top_missing])
            recommendations.append(
                RecommendationItem(
                    issue=f"High-priority required skills not evidenced in your resume: {skill_names}",
                    why_it_matters=f"These skills are explicit prerequisites for {role_title}. Automated screeners and hiring managers may disqualify applications lacking evidence of these technologies.",
                    recommended_action=(
                        "If you have hands-on experience or coursework with these technologies, explicitly add them to your Technical Skills section and mention how you used them in project descriptions. "
                        "If you have not used them yet, prioritize building a small portfolio project or learning the fundamentals before claiming proficiency."
                    ),
                    example_rewrite=(
                        f"• Developed scalable backend feature integrating {top_missing[0].name}, ensuring test-driven coverage and clean code principles."
                        if top_missing else None
                    )
                )
            )

        # 2. Missing Preferred Skills
        pref_missing = [s for s in missing_skills if not s.is_required]
        if pref_missing:
            pref_names = ", ".join([s.name for s in pref_missing[:3]])
            recommendations.append(
                RecommendationItem(
                    issue=f"Preferred / nice-to-have technologies not detected: {pref_names}",
                    why_it_matters="Preferred qualifications help candidates stand out from other qualified applicants when primary requirements are met.",
                    recommended_action=(
                        "If you have used these secondary tools in side projects, university labs, or hackathons, reference them in your Projects section to gain a competitive edge."
                    ),
                    example_rewrite=(
                        f"• Deployed application pipeline utilizing {pref_missing[0].name} to streamline continuous integration and automated testing."
                        if pref_missing else None
                    )
                )
            )

        # 3. Substantiating Matching Skills with Project Evidence
        if matching_skills:
            # Check if skills only appear in a raw list vs in descriptive bullets
            skills_to_check = matching_skills[:3]
            unsubstantiated = []
            for s in skills_to_check:
                # Count occurrences of skill in resume text
                occurrences = len(re.findall(rf"\b{re.escape(s.name)}\b", resume_text, re.IGNORECASE))
                if occurrences <= 1:
                    unsubstantiated.append(s.name)

            if unsubstantiated:
                recommendations.append(
                    RecommendationItem(
                        issue=f"Skills listed but lacking descriptive project context: {', '.join(unsubstantiated)}",
                        why_it_matters="Listing a keyword in a skills bank without referencing it in your work history or projects raises questions about your depth of experience.",
                        recommended_action=(
                            "Ensure every major skill listed in your technical skills block is also mentioned at least once in a bullet point explaining an achievement or project."
                        ),
                        example_rewrite=(
                            f"• Engineered data processing component with {unsubstantiated[0]}, optimizing throughput and adhering to clean code standards."
                            if unsubstantiated else None
                        )
                    )
                )

        # 4. Action Verb and Impact Enhancement
        passive_bullets = []
        for line in resume_text.split("\n"):
            clean = line.strip(" -*•\t")
            if clean.lower().startswith(("responsible for", "worked on", "helped with", "handled", "assisted with")):
                passive_bullets.append(clean)
                if len(passive_bullets) >= 2:
                    break

        if passive_bullets:
            first_weak = passive_bullets[0]
            recommendations.append(
                RecommendationItem(
                    issue=f"Passive phrasing found in bullet points (e.g. '{first_weak[:45]}...')",
                    why_it_matters="Hiring managers look for leadership and ownership. Passive language diminishes the perceived impact of your contributions.",
                    recommended_action=(
                        "Replace passive phrases like 'Responsible for' with strong action verbs: 'Architected', 'Implemented', 'Streamlined', 'Engineered', 'Optimized'."
                    ),
                    example_rewrite=(
                        f"• Replaced: '{first_weak[:50]}...'\n  Suggested: 'Architected and implemented [system/feature], improving maintainability and reducing operational overhead.'"
                    )
                )
            )

        # 5. Leveraging Additional Relevant Skills
        if len(additional_skills) >= 3:
            add_names = ", ".join([s.name for s in additional_skills[:3]])
            recommendations.append(
                RecommendationItem(
                    issue=f"Strong additional competencies found that aren't emphasized in the job description: {add_names}",
                    why_it_matters="While valuable, excessive emphasis on unrelated tools may distract reviewers from your alignment with the core requirements.",
                    recommended_action=(
                        "Keep these skills in your resume, but position the technologies requested by the employer higher up on your resume to ensure immediate ATS relevance."
                    ),
                    example_rewrite=None
                )
            )

        return recommendations
