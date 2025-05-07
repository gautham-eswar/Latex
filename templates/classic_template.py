from typing import Dict, Any, Optional, List
import re

# Default page height if not specified by the generator (e.g. if auto-sizing is off and no specific height is given)
DEFAULT_TEMPLATE_PAGE_HEIGHT_INCHES = 11.0 

def fix_latex_special_chars(text: Optional[Any]) -> str:
    """
    Escapes LaTeX special characters in a given string.
    Also converts None to an empty string.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text) # Ensure it's a string

    # Order of replacements is critical.
    # Replace backslash first, then other characters including percent.
    replacements = [
        ("\\", r"\textbackslash{}"), # Must be first
        ("&", r"\&"),
        ("%", r"\%"), # Direct replacement for percent
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]

    for old, new in replacements:
        text = text.replace(old, new)
        
    return text


def _generate_header_section(personal_info: Optional[Dict[str, Any]]) -> Optional[str]:
    if not personal_info:
        return None
    
    name = fix_latex_special_chars(personal_info.get("name"))
    email = personal_info.get("email")  # Raw email, will handle special chars in href
    phone = fix_latex_special_chars(personal_info.get("phone"))
    
    # Get raw values for URLs, with a fallback for LinkedIn
    raw_linkedin = personal_info.get("linkedin") or personal_info.get("website/LinkedIn")
    raw_github = personal_info.get("github")
    raw_website = personal_info.get("website")
    
    location = fix_latex_special_chars(personal_info.get("location"))

    lines = []
    if name:
        lines.append(r"\begin{center}")
        lines.append(f"    \\textbf{{\\Huge \\scshape {name}}} \\\\ \\vspace{{1pt}}")
    
    contact_parts = []
    if phone:
        contact_parts.append(phone)
    if email:
        email_display = email.replace("_", r"\_")
        contact_parts.append(f"\\href{{mailto:{email}}}{{{email_display}}}")
    
    if raw_linkedin:
        linkedin_display = fix_latex_special_chars(raw_linkedin)
        linkedin_url = raw_linkedin # Use raw value for URL
        if not linkedin_url.startswith("http"):
            linkedin_url = f"https://{linkedin_url}"
        contact_parts.append(f"\\href{{{linkedin_url}}}{{{linkedin_display}}}")
    
    if raw_github:
        github_display = fix_latex_special_chars(raw_github)
        github_url = raw_github # Use raw value for URL
        if not github_url.startswith("http"):
            github_url = f"https://{github_url}"
        contact_parts.append(f"\\href{{{github_url}}}{{{github_display}}}")
        
    if raw_website:
        website_display = fix_latex_special_chars(raw_website)
        website_url = raw_website # Use raw value for URL
        if not website_url.startswith("http"): # Basic check for protocol
             website_url = f"http://{website_url}"
        contact_parts.append(f"\\href{{{website_url}}}{{{website_display}}}")

    # Add location to contact_parts if it exists
    if location:
        contact_parts.append(location)

    if contact_parts:
        lines.append(f"    \\small {' $|$ '.join(contact_parts)}")
    
    if name: # Only add end{center} if we started it
        lines.append(r"\end{center}")
        lines.append("") # Add a newline for spacing

    return "\n".join(lines) if lines else None


def _generate_objective_section(objective: Optional[str]) -> Optional[str]:
    if not objective: return None
    return fr"""\section*{{Summary}} % Using section* for unnumbered
  {fix_latex_special_chars(objective)}
"""

def _generate_education_section(education_list: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    if not education_list: return None
    content_lines = []
    for edu in education_list:
        uni = fix_latex_special_chars(edu.get("institution") or edu.get("university"))
        loc = fix_latex_special_chars(edu.get("location"))
        degree_parts = [fix_latex_special_chars(edu.get("degree"))]
        if edu.get("specialization"): degree_parts.append(fix_latex_special_chars(edu.get("specialization")))
        degree_str = ", ".join(filter(None, degree_parts))
        start_date = fix_latex_special_chars(edu.get("start_date", ""))
        end_date = fix_latex_special_chars(edu.get("end_date", ""))
        dates = f"{start_date} -- {end_date}" if start_date or end_date else ""
        if end_date and end_date.lower() == 'present': dates = f"{start_date} -- Present"
        elif not end_date and start_date: dates = start_date

        if uni and degree_str:
            content_lines.append(r"    \resumeSubheading")
            content_lines.append(f"      {{{uni}}}{{{loc}}}")
            content_lines.append(f"      {{{degree_str}}}{{{dates}}}")
            gpa = edu.get("gpa")
            honors = fix_latex_special_chars(edu.get("honors"))
            details_parts = []
            if gpa: details_parts.append(f"GPA: {fix_latex_special_chars(gpa)}")
            if honors: details_parts.append(f"Honors: {honors}")
            if details_parts: content_lines.append(f"    \\resumeSubSubheading{{{', '.join(details_parts)}}}{{}}")
            
            additional_info = edu.get("additional_info")
            relevant_coursework = edu.get("relevant_coursework")
            if additional_info:
                content_lines.append(r"      \resumeItemListStart")
                content_lines.append(f"        \\resumeItem{{{fix_latex_special_chars(additional_info)}}}")
                content_lines.append(r"      \resumeItemListEnd")
            elif relevant_coursework and isinstance(relevant_coursework, list):
                content_lines.append(r"      \resumeItemListStart")
                courses_str = ", ".join(fix_latex_special_chars(c) for c in relevant_coursework)
                content_lines.append(f"        \\resumeItem{{Relevant Coursework: {courses_str}}}")
                content_lines.append(r"      \resumeItemListEnd")
    if not content_lines: return None
    final_latex_parts = [r"\section{Education}", r"  \resumeSubHeadingListStart"] + content_lines + [r"  \resumeSubHeadingListEnd", ""]
    return "\n".join(final_latex_parts)

def _generate_experience_section(experience_list: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    if not experience_list: return None
    content_lines = []
    for exp in experience_list:
        company = fix_latex_special_chars(exp.get("company"))
        position = fix_latex_special_chars(exp.get("position") or exp.get("title"))
        if not company and not position: continue
        location = fix_latex_special_chars(exp.get("location"))
        dates_dict = exp.get("dates", {})
        start_date = fix_latex_special_chars(dates_dict.get("start_date"))
        end_date = fix_latex_special_chars(dates_dict.get("end_date"))
        dates_str = f"{start_date} -- {end_date}" if start_date or end_date else ""
        if end_date and end_date.lower() == 'present': dates_str = f"{start_date} -- Present"
        elif not end_date and start_date: dates_str = start_date
        
        content_lines.append(r"    \resumeSubheading")
        content_lines.append(f"      {{{position}}}{{{dates_str}}}")
        content_lines.append(f"      {{{company}}}{{{location}}}")
        responsibilities = exp.get("responsibilities") or exp.get("responsibilities/achievements")
        if responsibilities and isinstance(responsibilities, list):
            content_lines.append(r"      \resumeItemListStart")
            for resp in responsibilities:
                if resp: content_lines.append(f"        \\resumeItem{{{fix_latex_special_chars(resp)}}}")
            content_lines.append(r"      \resumeItemListEnd")
    if not content_lines: return None
    final_latex_parts = [r"\section{Experience}", r"  \resumeSubHeadingListStart"] + content_lines + [r"  \resumeSubHeadingListEnd", ""]
    return "\n".join(final_latex_parts)

def _generate_projects_section(project_list: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    if not project_list: return None
    content_lines = []
    for proj in project_list:
        title = fix_latex_special_chars(proj.get("title"))
        if not title: continue
        dates_val = proj.get("dates") or proj.get("date")
        dates_str = ""
        if isinstance(dates_val, dict):
            start = fix_latex_special_chars(dates_val.get("start_date"))
            end = fix_latex_special_chars(dates_val.get("end_date"))
            dates_str = f"{start} -- {end}" if start or end else ""
            if end and end.lower() == 'present': dates_str = f"{start} -- Present"
            elif not end and start : dates_str = start
        elif isinstance(dates_val, str): dates_str = fix_latex_special_chars(dates_val)
        tech_used = proj.get("technologies") or proj.get("technologies_used")
        
        heading_title_part = f"\\textbf{{{title}}}"
        if tech_used:
            tech_str = ", ".join(fix_latex_special_chars(t) for t in tech_used) if isinstance(tech_used, list) else fix_latex_special_chars(tech_used)
            if tech_str: heading_title_part += f" $|$ \\emph{{{tech_str}}}"
            
        content_lines.append(r"      \resumeProjectHeading")
        content_lines.append(f"          {{{heading_title_part}}}{{{dates_str}}}")
        description = proj.get("description")
        if description:
            content_lines.append(r"          \resumeItemListStart")
            if isinstance(description, list):
                for item in description:
                    if item: content_lines.append(f"            \\resumeItem{{{fix_latex_special_chars(item)}}}")
            else:
                content_lines.append(f"            \\resumeItem{{{fix_latex_special_chars(description)}}}")
            content_lines.append(r"          \resumeItemListEnd")
    if not content_lines: return None
    final_latex_parts = [r"\section{Projects}", r"    \resumeSubHeadingListStart"] + content_lines + [r"    \resumeSubHeadingListEnd", ""]
    return "\n".join(final_latex_parts)


def _generate_skills_section(skills_dict: Optional[Dict[str, Any]]) -> Optional[str]:
    if not skills_dict: return None
    technical_skills_data = skills_dict.get("Technical Skills")
    skills_to_process = {}
    if isinstance(technical_skills_data, dict): skills_to_process = technical_skills_data
    elif isinstance(skills_dict, dict) and not technical_skills_data : skills_to_process = skills_dict
    
    category_lines_content = []
    if skills_to_process:
        for category, skills_list in skills_to_process.items():
            if skills_list and isinstance(skills_list, list):
                skills_str = ", ".join(fix_latex_special_chars(s) for s in skills_list if s)
                if skills_str: category_lines_content.append(f"     \\textbf{{{fix_latex_special_chars(category)}}}{{: {skills_str}}}")
    
    soft_skills_list = skills_dict.get("Soft Skills")
    soft_skills_content_str = ""
    if soft_skills_list and isinstance(soft_skills_list, list):
        processed_soft_skills = [fix_latex_special_chars(s) for s in soft_skills_list if s]
        if processed_soft_skills: soft_skills_content_str = f"     \\textbf{{Soft Skills}}{{: {', '.join(processed_soft_skills)}}}"

    if not category_lines_content and not soft_skills_content_str: return None

    lines = [r"\section{Technical Skills}"]
    lines.append(r" \begin{itemize}[leftmargin=0.15in, label={}]")
    lines.append(r"    \small{\item{")
    if category_lines_content:
        lines.append(" \\\\ ".join(category_lines_content))
        if soft_skills_content_str: lines.append(r" \\ ")
    if soft_skills_content_str:
        lines.append(soft_skills_content_str)
    lines.append(r"    }}")
    lines.append(r" \end{itemize}")
    lines.append("")
    return "\n".join(lines)


def _generate_languages_section(languages_list: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    if not languages_list: return None
    lang_items = []
    for lang_data in languages_list:
        name = fix_latex_special_chars(lang_data.get("name"))
        proficiency = fix_latex_special_chars(lang_data.get("proficiency"))
        if name: # Only add if name is present
            item_str = name
            if proficiency: item_str += f" ({proficiency})"
            lang_items.append(item_str)
    if not lang_items: return None
    final_latex_parts = [r"\section{Languages}", r" \begin{itemize}[leftmargin=0.15in, label={}]"]
    final_latex_parts.append(f"    \\small{{\\item{{{', '.join(lang_items)}}}}}")
    final_latex_parts.extend([r" \end{itemize}", ""])
    return "\n".join(final_latex_parts)


def _generate_certifications_section(cert_list: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    if not cert_list: return None
    content_lines = []
    for cert in cert_list:
        name = fix_latex_special_chars(cert.get("certification"))
        if not name: continue # Skip if no name
        institution = fix_latex_special_chars(cert.get("institution"))
        date = fix_latex_special_chars(cert.get("date"))
        content_lines.extend([
            r"    \resumeSubheading",
            f"      {{{name}}}{{{date}}}",
            f"      {{{institution}}}{{}}"
        ])
    if not content_lines: return None
    final_latex_parts = [r"\section{Certifications}", r"  \resumeSubHeadingListStart"]
    final_latex_parts.extend(content_lines)
    final_latex_parts.extend([r"  \resumeSubHeadingListEnd", ""])
    return "\n".join(final_latex_parts)

def _generate_awards_section(awards_list: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    if not awards_list: return None
    content_lines = []
    for award in awards_list:
        title = fix_latex_special_chars(award.get("title"))
        if not title: continue
        issuer = fix_latex_special_chars(award.get("issuer"))
        date = fix_latex_special_chars(award.get("date"))
        description = fix_latex_special_chars(award.get("description"))
        content_lines.extend([
            r"    \resumeSubheading",
            f"      {{{title}}}{{{date}}}",
            f"      {{{issuer}}}{{}}"
        ])
        if description:
            content_lines.extend([
                r"      \resumeItemListStart",
                f"        \\resumeItem{{{description}}}",
                r"      \resumeItemListEnd"
            ])
    if not content_lines: return None
    final_latex_parts = [r"\section{Awards}", r"  \resumeSubHeadingListStart"]
    final_latex_parts.extend(content_lines)
    final_latex_parts.extend([r"  \resumeSubHeadingListEnd", ""])
    return "\n".join(final_latex_parts)


def _generate_involvement_section(involvement_list: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    if not involvement_list: return None
    content_lines = []
    for item in involvement_list:
        organization = fix_latex_special_chars(item.get("organization"))
        position = fix_latex_special_chars(item.get("position"))
        if not organization and not position: continue
        date_val = item.get("date")
        dates_str = ""
        if isinstance(date_val, dict):
            start = fix_latex_special_chars(date_val.get("start_date"))
            end = fix_latex_special_chars(date_val.get("end_date"))
            dates_str = f"{start} -- {end}" if start or end else ""
            if end and end.lower() == 'present': dates_str = f"{start} -- Present"
            elif not end and start : dates_str = start
        elif isinstance(date_val, str): dates_str = fix_latex_special_chars(date_val)
        content_lines.extend([
            r"    \resumeSubheading",
            f"      {{{position}}}{{{dates_str}}}",
            f"      {{{organization}}}{{}}"
        ])
        responsibilities = item.get("responsibilities")
        if responsibilities and isinstance(responsibilities, list):
            content_lines.append(r"      \resumeItemListStart")
            for resp in responsibilities:
                if resp: content_lines.append(f"        \\resumeItem{{{fix_latex_special_chars(resp)}}}")
            content_lines.append(r"      \resumeItemListEnd")
    if not content_lines: return None
    final_latex_parts = [r"\section{Leadership \& Involvement}", r"  \resumeSubHeadingListStart"]
    final_latex_parts.extend(content_lines)
    final_latex_parts.extend([r"  \resumeSubHeadingListEnd", ""])
    return "\n".join(final_latex_parts)

def _generate_misc_leadership_section(misc_data: Optional[Dict[str, Any]]) -> Optional[str]:
    if not misc_data or not isinstance(misc_data, dict): return None
    leadership_data = misc_data.get("Leadership")
    if not leadership_data or not isinstance(leadership_data, dict): return None
    content_lines = []
    for event_name, details in leadership_data.items():
        name = fix_latex_special_chars(event_name)
        if not name: continue
        dates_dict = details.get("dates", {})
        start_date = fix_latex_special_chars(dates_dict.get("start_date"))
        end_date = fix_latex_special_chars(dates_dict.get("end_date"))
        dates_str = f"{start_date} -- {end_date}" if start_date or end_date else ""
        if end_date and end_date.lower() == 'present': dates_str = f"{start_date} -- Present"
        elif not end_date and start_date: dates_str = start_date
        
        # Use the new single-line subheading command
        content_lines.append(fr"    \resumeSubheadingSingleLine{{{name}}}{{{dates_str}}}")

        responsibilities = details.get("responsibilities/achievements")
        if responsibilities and isinstance(responsibilities, list):
            content_lines.append(r"      \resumeItemListStart")
            for resp in responsibilities:
                if resp: content_lines.append(f"        \\resumeItem{{{fix_latex_special_chars(resp)}}}")
            content_lines.append(r"      \resumeItemListEnd")
    if not content_lines: return None
    final_latex_parts = [r"\section{Leadership \& Activities}", r"  \resumeSubHeadingListStart"]
    final_latex_parts.extend(content_lines)
    final_latex_parts.extend([r"  \resumeSubHeadingListEnd", ""])
    return "\n".join(final_latex_parts)


def generate_latex_content(data: Dict[str, Any], page_height: Optional[float] = None) -> str:
    """
    Generates the full LaTeX document string for a classic resume.
    Args:
        data: The parsed JSON resume data.
        page_height: Optional page height in inches. If None, a template default is used.
    Returns:
        A string containing the complete LaTeX document.
    """
    
    # Determine page height for LaTeX geometry package
    page_height_setting_tex = ""
    text_height_adjustment = ""
    
    if page_height is not None:
        # Set the page height and calculate appropriate text height
        # Ensure backslashes are properly escaped for LaTeX commands in f-strings
        page_height_setting_tex = f"\\setlength{{\\pdfpageheight}}{{{page_height:.2f}in}}" # Double backslashes
        
        # Adjust text height proportionally to page height with more granular tiers
        if page_height > 15.0:  # 15-16 inches
            text_height_adjustment = f"\\addtolength{{\\textheight}}{{5.0in}}" # Double backslashes
        elif page_height > 14.0:  # 14-15 inches
            text_height_adjustment = f"\\addtolength{{\\textheight}}{{4.5in}}" # Double backslashes
        elif page_height > 13.0:  # 13-14 inches
            text_height_adjustment = f"\\addtolength{{\\textheight}}{{4.0in}}" # Double backslashes
        elif page_height > 12.0:  # 12-13 inches
            text_height_adjustment = f"\\addtolength{{\\textheight}}{{3.0in}}" # Double backslashes
        elif page_height > 11.0:  # 11-12 inches
            text_height_adjustment = f"\\addtolength{{\\textheight}}{{2.0in}}" # Double backslashes
        else:  # Up to 11 inches
            text_height_adjustment = f"\\addtolength{{\\textheight}}{{1.0in}}" # Double backslashes
    else:  # Default adjustments if page_height is None
        text_height_adjustment = f"\\addtolength{{\\textheight}}{{1.0in}}" # Double backslashes

    # LaTeX Preamble (derived from the provided sample .tex)
    preamble = r"""
\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage} % This sets margins to be minimal. Might conflict with explicit page height.
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{amsfonts} % For \Huge, \scshape etc. sometimes needs amsfonts or similar
% \input{glyphtounicode} % Assuming this is available if needed for specific glyphs.
% \pdfgentounicode=1     % Ensured in custom commands section in sample, good to have.

%----------FONT OPTIONS----------
% sans-serif
% \usepackage[sfdefault]{FiraSans}
% \usepackage[sfdefault]{roboto}
% \usepackage[sfdefault]{noto-sans}
% \usepackage[default]{sourcesanspro}

% serif
% \usepackage{CormorantGaramond}
% \usepackage{charter}

\pagestyle{fancy}
\fancyhf{} % clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins (from sample)
% These might need to be re-evaluated if we are setting explicit page height.
% fullpage already makes margins small. These are further adjustments.
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
"""

    # Append the dynamic text height adjustment
    preamble += text_height_adjustment

    # Continue with the rest of the preamble
    preamble += r"""

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting (from sample)
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

% Ensure that generated pdf is machine readable/ATS parsable
\pdfgentounicode=1

%-------------------------
% Custom commands (from sample)
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubSubheading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small#1} & \textit{\small #2} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}

\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

% New command for single line subheading
\newcommand{\resumeSubheadingSingleLine}[2]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}
"""

    # Document body start
    # Apply page height setting if provided. This should be early in the document.
    doc_start = f"""\\begin{{document}}
{page_height_setting_tex}
"""

    # Extract data based on schema (and handle Evelyn.json variations where noted)
    # The schema uses 'contact', Evelyn.json uses 'Personal Information'.
    # The schema uses 'objective' or 'summary', Evelyn.json uses 'Summary/Objective'.
    # The schema uses 'work_experience', Evelyn.json uses 'Experience'.
    # The schema uses 'skills' (dict), Evelyn.json uses 'Skills' (dict with sub-dicts).
    # The schema uses 'languages', Evelyn.json uses 'Languages'.
    # The schema uses 'certifications', Evelyn.json uses 'Certifications/Awards' (potentially mixed).
    # The schema uses 'awards', (see above).
    # The schema uses 'involvement' or 'leadership', Evelyn.json has 'Misc' -> 'Leadership'.

    personal_info_data = data.get("Personal Information") or data.get("contact")
    name_from_data = data.get("name") # Top level name from schema.
    if name_from_data and personal_info_data and not personal_info_data.get('name'):
        personal_info_data['name'] = name_from_data # Inject if missing in contact dict

    objective_data = data.get("Summary/Objective") or data.get("objective") or data.get("summary")
    education_data = data.get("Education") or data.get("education")
    experience_data = data.get("Experience") or data.get("work_experience")
    projects_data = data.get("Projects") or data.get("projects")
    skills_data = data.get("Skills") or data.get("skills")
    languages_data = data.get("Languages") or data.get("languages")
    
    # For certs/awards, Evelyn.json has "Certifications/Awards".
    # Schema has separate "certifications" and "awards".
    # We'll prefer direct keys first.
    certifications_data = data.get("certifications")
    awards_data = data.get("awards")
    certs_and_awards_mixed = data.get("Certifications/Awards")

    # If specific keys are empty but mixed one exists, we might need to split them.
    # For now, this template won't try to split a mixed list. It will use dedicated lists if present.
    # If only the mixed list is present and non-empty, we might decide to pass it to one
    # or the other, or a combined section. Given the prompt, let's assume separate lists are preferred.

    involvement_data = data.get("involvement") or data.get("leadership") # Schema direct keys
    misc_data = data.get("Misc") # For Evelyn.json specific "Misc" -> "Leadership"

    print("\n--- Section Generation Log ---") # Restore print
    section_processing_log = []

    # Generate LaTeX for each section and log
    header_tex = _generate_header_section(personal_info_data)
    section_processing_log.append(f"Header section: {'Included' if header_tex else 'Skipped (no data or empty)'}") # Fixed: added ')

    objective_tex = _generate_objective_section(objective_data)
    section_processing_log.append(f"Summary/Objective section: {'Included' if objective_tex else 'Skipped (no data or empty)'}") # Fixed: added ')

    education_tex = _generate_education_section(education_data)
    section_processing_log.append(f"Education section: {'Included' if education_tex else 'Skipped (no data or empty)'}") # Fixed: added ')

    experience_tex = _generate_experience_section(experience_data)
    section_processing_log.append(f"Experience section: {'Included' if experience_tex else 'Skipped (no data or empty)'}") # Fixed: added ')

    projects_tex = _generate_projects_section(projects_data)
    section_processing_log.append(f"Projects section: {'Included' if projects_tex else 'Skipped (no data or empty)'}") # Fixed: added ')

    skills_tex = _generate_skills_section(skills_data)
    section_processing_log.append(f"Skills section: {'Included' if skills_tex else 'Skipped (no data or empty)'}") # Fixed: added ')

    languages_tex = _generate_languages_section(languages_data)
    section_processing_log.append(f"Languages section: {'Included' if languages_tex else 'Skipped (no data or empty)'}") # Fixed: added ')

    certifications_tex = _generate_certifications_section(certifications_data)
    section_processing_log.append(f"Certifications section: {'Included' if certifications_tex else 'Skipped (no data or empty)'}") # Fixed: added ')

    awards_tex = _generate_awards_section(awards_data)
    section_processing_log.append(f"Awards section: {'Included' if awards_tex else 'Skipped (no data or empty)'}") # Fixed: added ')
    
    involvement_tex = None
    if involvement_data: # Prioritize schema's direct key
        involvement_tex = _generate_involvement_section(involvement_data)
        section_processing_log.append(f"Involvement/Leadership section (direct key): {'Included' if involvement_tex else 'Skipped (no data or empty)'}") # Fixed: added ')
    elif misc_data: # Fallback to Evelyn.json's Misc.Leadership structure
        involvement_tex = _generate_misc_leadership_section(misc_data)
        section_processing_log.append(f"Misc/Leadership section (fallback): {'Included' if involvement_tex else 'Skipped (no data or empty)'}") # Fixed: added ')
    else:
        section_processing_log.append("Involvement/Leadership/Misc section: Skipped (no relevant data found)") # This one was already correct

    print("\n".join(section_processing_log)) # Restore print
    print("--- End Section Generation Log ---\n") # Restore print

    # Assemble the document
    content_parts = [
        preamble,
        doc_start,
        header_tex,
        objective_tex,
        education_tex,
        experience_tex,
        projects_tex,
        skills_tex,
        languages_tex,
        certifications_tex,
        awards_tex,
        involvement_tex,
        r"""
\end{document}
"""
    ]
    
    # Filter out None parts (e.g., if a section is empty and its generate function returns None)
    # and join them.
    full_latex_doc = "\n".join(filter(None, content_parts))
    
    return full_latex_doc

# --- Minimal test for the template if run directly (not typical use) ---
if __name__ == '__main__':
    # Sample data structure (simplified, matching some keys from schema and Evelyn.json)
    sample_resume_data = {
        "Personal Information": {
            "name": "Ruo-Yi Evelyn Liang",
            "email": "ruoyi_liang@berkeley.edu",
            "phone": "(510) 282-2716",
            "linkedin": "linkedin.com/in/Evelyn_Liang", # Assume schema wants full URL or just handle
            "location": "Berkeley, CA",
            "github": "github.com/evelyn"
        },
        "Summary/Objective": "Data Science Meets Product Strategy—Turning Analytics into Action. & a test of _ and % and $ and # and { and } and \\\\ and ~ and ^",
        "Education": [
            {
                "university": "University of California, Berkeley",
                "location": "Berkeley, CA",
                "degree": "Master of Analytics",
                "specialization": "IEOR, College of Engineering",
                "start_date": "Aug 2025",
                "end_date": "Present",
                "gpa": "3.7/4.0",
                "additional_info": "Courses: Machine Learning, Optimization, Design of Databases."
            },
            {
                "university": "National Taiwan University (NTU)",
                "degree": "Bachelor of Business Administration",
                "start_date": "June 2024", # No end date
                "gpa": "3.8/4.0",
                "relevant_coursework": ["Data Analysis", "Project Management"]
            }
        ],
        "Experience": [ # work_experience
            {
                "company": "Shopee Pte. Ltd.",
                "title": "Data Analysis Intern", # position
                "location": "Taipei, Taiwan",
                "dates": {"start_date": "June 2023", "end_date": "Dec 2023"},
                "responsibilities/achievements": [ # responsibilities
                    "Monitored performance & saved 5% costs.",
                    "Increased 2% sales via A/B testing."
                ]
            }
        ],
        "Projects": [
            {
                "title": "Capstone - Google Case Competition",
                "description": "Achieved a 16% profit boost.",
                "technologies_used": "Linear Programming", # technologies
                "date": "Spring 2023"
            }
        ],
        "Skills": { # skills (dict of categories to lists)
            "Technical Skills": {
                "Programming languages": ["Python", "SQL", "R", "C# & C++"],
                "Data Analysis": ["Pandas", "NumPy", "TensorFlow"],
                "Database": ["MySQL", "MongoDB"]
            },
            "Soft Skills": ["Communication", "Teamwork"]
        },
        "Languages": [ # languages (list of dicts)
            {"name": "Mandarin", "proficiency": "Native"},
            {"name": "English", "proficiency": "Fluent"}
        ],
        "Certifications/Awards": [], # Combined in Evelyn.json, schema is separate
        "certifications": [
            {"certification": "TensorFlow Developer Certificate", "institution": "Google", "date": "2022"}
        ],
        "awards": [
            {"title": "Dean's List", "issuer": "NTU", "date": "2021", "description": "Top 5% of students."}
        ],
        "involvement": [ # Schema's 'involvement' or 'leadership'
            {
                "organization": "Analytics Club", "position": "President",
                "date": {"start_date": "Jan 2022", "end_date": "Dec 2022"},
                "responsibilities": ["Led weekly meetings", "Organized workshops"]
            }
        ],
        "Misc": { # Evelyn.json's structure for leadership
            "Leadership": {
                "Event General Coordinator": {
                    "dates": {"start_date": "Apr 2023", "end_date": "May 2023"},
                    "responsibilities/achievements": ["Led a team of 100+", "Coordinated with 12 sponsors"]
                }
            }
        }
    }

    print("--- Generating LaTeX from sample data (page_height = None) ---")
    latex_output_default = generate_latex_content(sample_resume_data)
    # print(latex_output_default)
    with open("classic_template_test_default.tex", "w", encoding='utf-8') as f:
        f.write(latex_output_default)
    print("Saved to classic_template_test_default.tex")

    print("\n--- Generating LaTeX from sample data (page_height = 13.0 inches) ---")
    latex_output_custom_h = generate_latex_content(sample_resume_data, page_height=13.0)
    # print(latex_output_custom_h)
    with open("classic_template_test_custom_h.tex", "w", encoding='utf-8') as f:
        f.write(latex_output_custom_h)
    print("Saved to classic_template_test_custom_h.tex")
    
    print("\n--- Testing fix_latex_special_chars ---")
    test_str = "Text with \\ backslash, {curly braces}, & ampersand, % percent, $ dollar, # hash, _ underscore, ~ tilde, ^ caret."
    print(f"Original: {test_str}")
    print(f"Escaped:  {fix_latex_special_chars(test_str)}")
    
    # Test with a more minimal data set to check optional sections
    minimal_data = {
        "Personal Information": {"name": "Test User", "email": "test@example.com"},
        "Education": [{"university": "Test Uni", "degree": "BS CS"}]
    }
    print("\n--- Generating LaTeX from minimal data ---")
    latex_minimal = generate_latex_content(minimal_data)
    with open("classic_template_test_minimal.tex", "w", encoding='utf-8') as f:
        f.write(latex_minimal)
    print("Saved to classic_template_test_minimal.tex")
