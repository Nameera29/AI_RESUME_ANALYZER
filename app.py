from flask import Flask, render_template, request
import os

from PyPDF2 import PdfReader
from ai_engine import analyze_resume


app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        # Get uploaded resume
        resume = request.files["resume"]

        # Get filename
        filename = resume.filename

        # Create file path
        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        # Save PDF
        resume.save(filepath)

        # Read PDF
        reader = PdfReader(filepath)

        # Extract text
        resume_text = ""

        for page in reader.pages:
            resume_text += page.extract_text() or ""

        # Check if text was extracted
        if not resume_text.strip():
            return "Could not extract text from this PDF."

        # Send resume text to Gemini
        result = analyze_resume(resume_text)

        # Display Career DNA
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Career DNA</title>
        </head>

        <body>

            <h1>🧬 Your Career DNA</h1>

            <h2>👤 Candidate Summary</h2>
            <p>{result.candidate_summary}</p>

            <h2>💻 Technical Skills</h2>
            <ul>
                {"".join(f"<li>{skill}</li>" for skill in result.technical_skills)}
            </ul>

            <h2>🤝 Soft Skills</h2>
            <ul>
                {"".join(f"<li>{skill}</li>" for skill in result.soft_skills)}
            </ul>

            <h2>🎓 Education</h2>
            <ul>
                {"".join(f"<li>{item}</li>" for item in result.education)}
            </ul>

            <h2>🚀 Projects</h2>
            <ul>
                {"".join(f"<li>{item}</li>" for item in result.projects)}
            </ul>

            <h2>💼 Experience</h2>
            <ul>
                {"".join(f"<li>{item}</li>" for item in result.experience)}
            </ul>

            <h2>📜 Certifications</h2>
            <ul>
                {"".join(f"<li>{item}</li>" for item in result.certifications)}
            </ul>

            <h2>🏆 Achievements</h2>
            <ul>
                {"".join(f"<li>{item}</li>" for item in result.achievements)}
            </ul>

            <h2>💪 Strengths</h2>
            <ul>
                {"".join(f"<li>{item}</li>" for item in result.strengths)}
            </ul>

            <h2>⚠️ Weaknesses</h2>
            <ul>
                {"".join(f"<li>{item}</li>" for item in result.weaknesses)}
            </ul>

            <h2>🧩 Skill Gaps</h2>
            <ul>
                {"".join(f"<li>{item}</li>" for item in result.skill_gaps)}
            </ul>

            <h2>🎯 Career Directions</h2>
            <ul>
                {"".join(f"<li>{item}</li>" for item in result.career_directions)}
            </ul>

        </body>
        </html>
        """

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)