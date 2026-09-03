import os
import logging
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from .utils import validate_resume_file, extract_resume_text
from ai_engine import analyze_resume, match_job_description

logger = logging.getLogger(__name__)


def home(request):
    context = {}
    if request.method == 'POST':
        # Accept 'resume' or 'resume_file'
        uploaded_file = request.FILES.get('resume') or request.FILES.get('resume_file')
        job_description = request.POST.get('job_description', '').strip()

        is_valid, error_msg = validate_resume_file(uploaded_file)
        if not is_valid:
            context['error_message'] = error_msg
            return render(request, 'home.html', context)

        # --- File Save & Text Extraction ---
        try:
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'resumes')
            os.makedirs(upload_dir, exist_ok=True)

            fs = FileSystemStorage(location=upload_dir, base_url=f"{settings.MEDIA_URL}resumes/")
            filename = fs.save(uploaded_file.name, uploaded_file)
            saved_file_path = fs.path(filename)
            file_url = fs.url(filename)

            ext = os.path.splitext(filename)[1].lower()
            extracted_text = extract_resume_text(saved_file_path, ext)

        except ValueError as ve:
            # Friendly extraction errors (e.g. empty PDF, scanned image)
            context['error_message'] = str(ve)
            return render(request, 'home.html', context)
        except Exception:
            logger.exception("Unexpected error during file save or text extraction.")
            context['error_message'] = (
                "We could not read your resume file. "
                "Please ensure it is a valid, non-password-protected PDF or DOCX and try again."
            )
            return render(request, 'home.html', context)

        if not extracted_text or not extracted_text.strip():
            context['error_message'] = (
                "The resume file appears to be empty or contains no readable text. "
                "Please upload a different file."
            )
            return render(request, 'home.html', context)

        word_count = len(extracted_text.split())
        char_count = len(extracted_text)
        file_size_kb = round(uploaded_file.size / 1024, 1)

        # --- AI Analysis ---
        try:
            analysis_result = analyze_resume(extracted_text)
        except ValueError as ve:
            context['error_message'] = str(ve)
            return render(request, 'home.html', context)
        except Exception:
            logger.exception("Unexpected error during resume analysis.")
            context['error_message'] = (
                "Resume analysis encountered an unexpected problem. Please try again."
            )
            return render(request, 'home.html', context)

        # --- ATS Job Matching (100% local, always safe) ---
        ats_match_result = None
        if job_description:
            try:
                ats_match_result = match_job_description(extracted_text, job_description)
            except Exception:
                logger.exception("Unexpected error during ATS job matching.")
                # Non-fatal: continue without ATS result

        context.update({
            'success_message': 'Resume uploaded and analyzed successfully!',
            'filename': filename,
            'original_name': uploaded_file.name,
            'file_url': file_url,
            'file_size_kb': file_size_kb,
            'extracted_text': extracted_text,
            'job_description': job_description,
            'word_count': word_count,
            'char_count': char_count,
            'analysis': analysis_result,
            'ats_match': ats_match_result,
            'analysis_source': analysis_result.get('analysis_source', 'Local'),
        })

        return render(request, 'results.html', context)

    return render(request, 'home.html', context)
