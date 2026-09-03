from ai_engine import analyze_resume


sample_resume = """
Kutagula Nameera

B.Tech Electronics and Communication Engineering  student.

Skills:
Python, Flask, SQL, HTML, CSS, JavaScript

Projects:
AI Resume Analyzer using Python and Flask.
Luggage Detection System using YOLOv5.

Certifications:
Python Essentials.

Interests:
Artificial Intelligence and Machine Learning.
"""


result = analyze_resume(sample_resume)


print("\n========== CAREER DNA ==========\n")

print("SUMMARY:")
print(result.candidate_summary)

print("\nTECHNICAL SKILLS:")
print(result.technical_skills)

print("\nSOFT SKILLS:")
print(result.soft_skills)

print("\nEDUCATION:")
print(result.education)

print("\nPROJECTS:")
print(result.projects)

print("\nEXPERIENCE:")
print(result.experience)

print("\nCERTIFICATIONS:")
print(result.certifications)

print("\nACHIEVEMENTS:")
print(result.achievements)

print("\nSTRENGTHS:")
print(result.strengths)

print("\nWEAKNESSES:")
print(result.weaknesses)

print("\nSKILL GAPS:")
print(result.skill_gaps)

print("\nCAREER DIRECTIONS:")
print(result.career_directions)

print("\n================================\n")