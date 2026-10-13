import json
from datetime import datetime
from typing import Dict, Any
from ..schemas.analysis import AnalysisResponse

class ReportGenerator:
    @staticmethod
    def generate_markdown_report(data: AnalysisResponse) -> str:
        """Generates a structured, professional Markdown report of the match analysis."""
        scores = data.scores
        exp = data.experience_analysis
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        md_lines = [
            "# AI Resume & Job Description Match Report",
            f"**Generated:** {now_str}  ",
            f"**Target Role:** {data.target_job_title or 'Not specified'}  ",
            f"**Resume Word Count:** {data.resume_word_count} | **JD Word Count:** {data.jd_word_count}  ",
            f"**Processing Time:** {data.processing_time_seconds:.2f}s  ",
            "",
            "---",
            "",
            "## 1. Executive Summary & Alignment Scores",
            "",
            f"- **Overall Alignment Score:** **{scores.overall_score:.1f}%**",
            f"- **Semantic Similarity Score:** {scores.semantic_score:.1f}% (Weight: {scores.weights_applied.get('semantic_weight', 0.4)*100:.0f}%)",
            f"- **Required Skill Coverage:** {scores.required_skill_score:.1f}% (Weight: {scores.weights_applied.get('required_skill_weight', 0.4)*100:.0f}%)",
        ]

        if scores.preferred_skill_score is not None:
            md_lines.append(
                f"- **Preferred Skill Coverage:** {scores.preferred_skill_score:.1f}% (Weight: {scores.weights_applied.get('preferred_skill_weight', 0.2)*100:.0f}%)"
            )
        else:
            md_lines.append(
                "- **Preferred Skill Coverage:** N/A (No separate preferred skills specified in job posting; weights renormalized)"
            )

        md_lines.extend([
            "",
            "> ℹ️ **Disclaimer:** " + scores.disclaimer,
            "",
            "---",
            "",
            "## 2. Technical Skills Breakdown",
            "",
            f"### A. Matching Skills ({len(data.matching_skills)})",
            "| Skill | Category | Type | Evidence / Context |",
            "| :--- | :--- | :--- | :--- |",
        ])

        if data.matching_skills:
            for s in data.matching_skills:
                req_type = "Required" if s.is_required else "Preferred"
                evidence = (s.evidence_snippet or "Identified in resume").replace("|", "\\|")
                md_lines.append(f"| **{s.name}** | {s.category} | {req_type} | {evidence} |")
        else:
            md_lines.append("| *None detected* | - | - | - |")

        md_lines.extend([
            "",
            f"### B. Potentially Missing or Unsubstantiated Skills ({len(data.missing_skills)})",
            "| Skill | Category | Requirement Priority | Job Description Mention |",
            "| :--- | :--- | :--- | :--- |",
        ])

        if data.missing_skills:
            for s in data.missing_skills:
                req_type = "**High (Required)**" if s.is_required else "Medium (Preferred)"
                evidence = (s.evidence_snippet or "Mentioned in job description").replace("|", "\\|")
                md_lines.append(f"| **{s.name}** | {s.category} | {req_type} | {evidence} |")
        else:
            md_lines.append("| *No missing skills identified!* | - | - | - |")

        if data.additional_skills:
            md_lines.extend([
                "",
                f"### C. Additional Technical Competencies Found in Resume ({len(data.additional_skills)})",
                "These skills are present in your resume but were not explicitly required in the job description:",
                "",
                ", ".join([f"`{s.name}`" for s in data.additional_skills]),
                ""
            ])

        md_lines.extend([
            "---",
            "",
            "## 3. Experience & Qualification Analysis",
            "",
            f"- **Resume Sections Identified:** {', '.join(exp.sections_detected) if exp.sections_detected else 'None explicitly labeled'}",
            f"- **Education Identified:** {', '.join(exp.education_detected) if exp.education_detected else 'None explicitly labeled'}",
            f"- **Experience Comparison:** {exp.experience_years_comparison or 'Not evaluated'}",
            "",
            "### Section Observations:",
        ])

        for obs in exp.observations:
            md_lines.append(f"- {obs}")

        md_lines.extend([
            "",
            "---",
            "",
            "## 4. Actionable Resume Improvement Recommendations",
            ""
        ])

        if data.recommendations:
            for idx, rec in enumerate(data.recommendations, 1):
                md_lines.extend([
                    f"### Recommendation {idx}: {rec.issue}",
                    f"- **Why it matters:** {rec.why_it_matters}",
                    f"- **Action to take:** {rec.recommended_action}",
                ])
                if rec.example_rewrite:
                    md_lines.extend([
                        f"- **Illustrative Rewrite:**\n  ```\n  {rec.example_rewrite}\n  ```",
                        f"  *Note: {rec.user_verification_notice}*"
                    ])
                md_lines.append("")
        else:
            md_lines.append("No critical issues found. Your resume strongly matches the criteria evaluated.")

        md_lines.extend([
            "---",
            "",
            "## 5. Report & Privacy Safeguards",
            "- This report was generated locally using open-source NLP models.",
            "- In accordance with security best practices, full resume text is not stored permanently or transmitted to third-party APIs.",
            "- Generated by **AI Resume & Job Description Matcher**."
        ])

        return "\n".join(md_lines)

    @staticmethod
    def generate_json_report(data: AnalysisResponse) -> str:
        """Generates formatted JSON export of analysis data."""
        return json.dumps(data.model_dump(), indent=2, ensure_ascii=False)
