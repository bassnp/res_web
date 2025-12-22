# **The Architect’s Guide to Resume Engineering: A Comprehensive Technical Treatise on "Docs-as-Code" Portfolios**

## **1\. Introduction: The Paradigm Shift in Technical Representation**

In the domain of computer science and software engineering, the resume acts not merely as a historical record of employment but as a primary artifact of technical competency. For decades, the industry relied on proprietary, binary-heavy word processors that conflated content with presentation. This legacy approach results in brittle documents: version control is impossible, collaborative editing is painful, and distinct versions for print, web, and mobile require maintaining separate source files.

The emergence of the "Docs-as-Code" philosophy—treating documentation with the same rigor, tooling, and workflow as software source code—has fundamentally altered this landscape. The modern "Resume as Code" is built upon lightweight markup languages (Markdown), styled via declarative rules (CSS), and compiled through automated build pipelines (Pandoc, GitHub Actions) into immutable artifacts (PDFs).1 This report provides an exhaustive, expert-level analysis of constructing a single-page, visually distinct computer science resume using these technologies. It explores the intersection of semantic markup, CSS Paged Media specifications, typography theory, and continuous delivery workflows to empower the engineer to own their professional narrative completely.

The objective is clear: to produce a document that passes the algorithmic gatekeeping of Applicant Tracking Systems (ATS) while delivering a visually stunning, single-page experience to the human hiring manager. This requires a nuanced understanding of how browser rendering engines handle print media, how vector graphics (SVG) behave in distinct contexts, and how to leverage the separation of concerns to maintain a "living document" that evolves with one's career.1

## **2\. The Semantic Foundation: Advanced Markdown Architectures**

The core of the "Docs-as-Code" resume is the separation of content from presentation. Markdown, specifically standardized dialects like CommonMark or GitHub Flavored Markdown (GFM), serves as the content layer. However, expert-level utilization extends far beyond basic headers and lists; it involves architecting a semantic document structure that optimizes for machine readability and stylistic flexibility.

### **2.1 The Taxonomy of Semantic Headers**

In typical word processing, a header is simply text with a larger font size. In Markdown, headers (\#, \#\#) define the document object model (DOM) of the resume. This hierarchy is critical for accessibility tools (screen readers) and ATS parsers, which use header levels to categorize data into fields like "Experience," "Education," and "Skills".3

**Table 1: Semantic Header Mapping for Resume Architecture**

| Markdown Syntax | Semantic Level | Resume Function | ATS Implication |
| :---- | :---- | :---- | :---- |
| \# Name | H1 (Root) | Candidate Identity | Identifies the record owner. Must be unique. |
| \#\# Section | H2 (Major) | Categories (Exp, Edu, Skills) | Triggers parsing modules (e.g., "Start parsing work history"). |
| \#\#\# Role/School | H3 (Item) | Specific Entities | Linked to date ranges and locations found in proximity. |
| \#\#\#\# Detail | H4 (Sub-item) | Project Titles / Stack | Often treated as keywords associated with the H3 entity. |

For a computer science resume, the hierarchy must be rigid. Using a Level 2 header for a specific job title (e.g., \#\# Senior Engineer) disrupts the parser's expectation that Level 2 headers denote section boundaries, potentially causing the ATS to misclassify the job title as a new section type. The expert practitioner ensures that the H1 tag is reserved exclusively for their name, establishing the document root.5

### **2.2 Metadata Injection via YAML Frontmatter**

While Markdown handles the visible body text, expert workflows utilize YAML frontmatter—a metadata block at the very start of the file—to handle document variables. This is particularly prevalent in Pandoc workflows. This data is not rendered directly as markdown text but is passed to the template engine to populate meta-tags, PDF properties, and even conditional logic in the build process.2

YAML

\---  
title: "Jane Doe \- Senior Reliability Engineer"  
author: "Jane Doe"  
date: "2025-12-21"  
keywords: "Kubernetes, Go, Rust, CI/CD, Terraform"  
geometry: "margin=0.5in"  
lang: "en-US"  
papersize: "letter"  
header-includes:  
  \- \\usepackage{fontspec}  
\---

This metadata layer is crucial for "invisible" optimization. The keywords field, for instance, often maps to the PDF Keywords metadata property. When a recruiter opens the PDF in a viewer, or when an indexing bot crawls the file, these keywords provide high-signal data before the text is even parsed. Furthermore, defining lang: "en-US" is essential for correct hyphenation algorithms in the CSS/LaTeX rendering engine, preventing awkward line breaks in technical terminology.6

### **2.3 Hybrid Markup: HTML Injection for Layout Control**

Standard Markdown is linear; it flows from top to bottom. To achieve a "modern and unique" single-page layout—often characterized by a two-column split (sidebar for skills/contact, main area for experience)—one must break the linear flow. Markdown allows for the injection of raw HTML, which acts as a wrapper for CSS styling.

The "pure" Markdown purist might reject this, but practical resume engineering demands it. Wrapping sections in div tags with semantic class names creates hooks for the Grid layout system.8

HTML

\<section class\="resume-grid"\>  
  \<aside class\="sidebar"\>  
    \#\# Contact  
   ...  
  \</aside\>  
  \<div class\="main-content"\>  
    \#\# Experience  
   ...  
  \</div\>  
\</section\>

This hybrid approach maintains the readability of Markdown for the actual content (the bullet points and descriptions) while leveraging HTML5 semantic tags (\<section\>, \<aside\>, \<header\>) to define the layout geometry. This ensures that even if the CSS fails or is stripped (as happens in some distinct "Text-Only" views), the semantic order remains logical.1

## **3\. The Visual Engine: CSS Paged Media and Grid Layouts**

The transition from a Markdown file to a stunning PDF is mediated by the web browser's rendering engine (typically Chromium via Puppeteer or VS Code). Unlike designing for the screen, designing for a PDF resume operates under the constraints of **CSS Paged Media**. The canvas is finite (A4 or US Letter), and there is no scrollbar. Every pixel of vertical space is currency.

### **3.1 CSS Grid: The Mechanics of the Two-Column Layout**

Historically, multi-column layouts were achieved with float or flexbox, but these are notoriously difficult to control in paged media, often leading to misalignment when printing. CSS Grid is the robust, modern solution. It allows for the definition of a rigid two-dimensional structure that holds up under the translation to PDF.10

To create a sidebar layout that spans the full height of the page:

1. **The Container:** The top-level wrapper is set to display: grid.  
2. **The Tracks:** grid-template-columns defines the ratio. A 30% 70% split is standard, but using fractional units (1fr 2fr) is often more resilient to margin changes.  
3. **The Height:** Critically, the container must have a min-height of 100vh (viewport height) or 297mm (for A4). This forces the background colors of the sidebar to extend to the very bottom of the page, even if the content stops earlier.9

**Table 2: Comparison of CSS Layout Models for Print Resumes**

| Layout Model | Pros | Cons | Print Stability Score |
| :---- | :---- | :---- | :---- |
| **Floats** | Backward compatible with ancient renderers. | Fragile; requires "clearfix" hacks; poor vertical alignment. | 2/10 |
| **Flexbox** | Good for 1D lists (skill tags, nav bars). | Difficult to align separate columns vertically across pages. | 6/10 |
| **CSS Grid** | Precise 2D control; overlaps allowed; defining areas via ASCII-art syntax. | Requires modern renderer (supported by VS Code/Puppeteer). | **10/10** |

#### **3.1.1 Grid Gap and Alignment**

The gap property in CSS Grid is superior to margins for defining the whitespace between the sidebar and main content. It ensures that the separation is consistent and doesn't collapse or double up unexpectedly.

CSS

.resume-container {  
    display: grid;  
    grid-template-columns: 1fr 2.5fr;  
    grid-template-rows: auto 1fr;  
    gap: 0 2rem; /\* 0 vertical gap, 2rem horizontal gap \*/  
}

This precise control allows the engineer to maximize the "Data-Ink Ratio"—reducing the clutter of borders and lines in favor of whitespace, which improves the document's legibility and perceived modernity.11

### **3.2 The @page Rule: Controlling the Physical Canvas**

The @page CSS at-rule gives the developer access to the browser's print settings programmatically. This is essential for removing the default headers/footers (time stamps, URLs) and setting the margins.12

For a truly modern "bleed" design (where color touches the edge of the paper), the page margins must be zeroed out:

CSS

@page {  
    size: A4 portrait;  
    margin: 0;  
}

Once the page margin is zero, the developer must add padding to the body or the main container to ensure text doesn't run off the page. This "zero-margin \+ internal padding" technique is the secret to professional-grade print layouts in CSS. It prevents the white "printer gutter" that screams "amateur Word document".14

### **3.3 Managing Fragmentation: Widows, Orphans, and Breaks**

A single-page constraint creates a high risk of awkward breaks—a header appearing at the bottom of column 1 while its content starts at the top of column 2\. The CSS Fragmentation Module (Level 3\) provides properties to control this.15

* **break-inside: avoid;**: This is the most critical line of CSS in the entire resume. It should be applied to semantic blocks like job entries (.job-experience-item) or skill categories. It forces the rendering engine to keep the entire block on one page/column. If it fits, it prints; if not, the whole block moves to the next context.  
  CSS  
  section, article,.entry {  
      break-inside: avoid;  
      page-break-inside: avoid; /\* Legacy fallback \*/  
  }

* **Widows and Orphans:** Applying widows: 2; orphans: 2; to paragraph tags prevents single lines of text from being stranded. This is a subtle typographic detail that distinguishes expert documents from hasty exports.17

### **3.4 Print Color fidelity: The print-color-adjust Property**

By default, browsers optimize for "Economy" printing—stripping background colors and high-contrast images to save toner. For a digital resume intended to be viewed as a PDF, this destroys the design.  
The property print-color-adjust: exact; (and its vendor prefix \-webkit-print-color-adjust: exact;) creates a directive that forces the engine to render the document exactly as seen on screen, preserving sidebar fills, skill badge backgrounds, and syntax highlighting colors.19

## **4\. Typography and Aesthetics: The Voice of the Document**

In a text-heavy document like a resume, typography is not just decoration; it is the user interface. The choice of typeface and the handling of whitespace determines the readability and the "personality" of the candidate.

### **4.1 Font Pairing Strategies for Technical Roles**

The standard advice (Serif for body, Sans-Serif for headers) remains valid, but for computer science, a third category is mandatory: **Monospace**.

* **Primary Font (Sans-Serif):** For a modern, clean look, Sans-Serif fonts like **Inter**, **Roboto**, or **Open Sans** are preferred. They render exceptionally well on screens (where the PDF will be viewed 99% of the time). **Inter**, specifically, was designed for computer screens and has excellent legibility at small sizes, making it ideal for dense resumes.21  
* **Secondary Font (Serif):** If a more academic or authoritative tone is desired (e.g., for data science or research roles), a Serif font like **Merriweather** or **Georgia** adds weight.  
* **The Technical Indicator (Monospace):** Code snippets, tool names (e.g., git, kubectl), and package names should be wrapped in backticks in Markdown and styled with a Monospace font like **Fira Code**, **JetBrains Mono**, or **Source Code Pro**. This visual distinction allows technical recruiters to scan the document specifically for hard skills and tools, increasing the document's "scannability".23

**Table 3: Recommended Font Stacks for Developer Resumes**

| Archetype | Header Font | Body Font | Code Font | Vibe |
| :---- | :---- | :---- | :---- | :---- |
| **The Modernist** | Inter (Bold) | Inter (Regular) | JetBrains Mono | Clean, Startup, UI/UX aware. |
| **The Systems Eng** | Roboto | Roboto Slab | Source Code Pro | Robust, Google-esque, Engineering-first. |
| **The Academic** | LaTeX Default (CM) | Merriweather | Fira Code | Research-heavy, Serious, Data Science. |
| **The Minimalist** | Helvetica Neue | Helvetica Neue | Space Mono | Classic, Swiss-style, Timeless. |

### **4.2 Color Theory: Dark Mode in a Light Medium**

Developers often prefer Dark Mode IDEs, and there is a temptation to create a Dark Mode resume. This is strongly discouraged. A resume with a black background is difficult to print (if ever needed), often triggers rendering artifacts in older PDF viewers, and can be harder to read in bright office environments.  
Instead, the expert integrates "Dark Mode aesthetics" via accent colors. Using the palettes from popular IDE themes—Dracula (Purple/Pink), Nord (Frost Blue), or Monokai (Yellow/Green)—as the accent colors for headers and icons creates a subtle "if you know, you know" signal to other developers without compromising the document's professional utility.25

* **Background:** Pure White (\#FFFFFF) or extremely light gray (\#F8F9FA).  
* **Text:** Dark Gray (\#333333) rather than pure black, which softens the contrast and reduces eye strain.  
* **Accents:** Use the primary color of your favorite tech stack (e.g., the Rust orange or the React blue) for links and H2 underlines.

### **4.3 Iconography: Vector vs. Font**

Visualizing the "Skills" section with logos (e.g., the Python logo next to the word "Python") is a controversial but popular design choice. There are two technical approaches: Font Icons (FontAwesome) and Vector Graphics (SVG).

* **Font Icons:** Loading a web font like FontAwesome is convenient but risky. If the PDF renderer fails to embed the font subset, the icons will appear as "tofu" boxes. Furthermore, browser security settings often block remote font loading in local files.27  
* **SVG (Scalable Vector Graphics):** This is the expert choice. SVGs are XML code. They can be embedded directly into the HTML stream. They scale infinitely without pixelation (crucial for high-DPI retina screens) and are styling-agnostic. Libraries like **Devicon** provide thousands of tech-specific logos. Using the raw SVG data ensures that the icon *always* renders, regardless of network conditions or font embedding policies.29

## **5\. Tooling and Build Pipelines: The Engineering Workflow**

The "Docs-as-Code" methodology implies that the resume is built, not just written. There are two primary workflows for the expert user: the interactive **VS Code Ecosystem** and the automated **Pandoc/CI Pipeline**.

### **5.1 Workflow A: The Visual Studio Code Ecosystem**

For immediate visual feedback and ease of editing, VS Code is the superior tool. It allows the developer to write Markdown and see a live preview of the CSS changes.

#### **5.1.1 The "Markdown PDF" Extension**

The standard tool for this workflow is the yzane.markdown-pdf extension. It uses a headless Chromium browser (via Puppeteer) to render the Markdown as HTML and then print it to PDF. This ensures that the PDF looks *exactly* like the web preview.31

* **Configuration:** The critical step is linking the local CSS file. In .vscode/settings.json:  
  JSON  
  "markdown-pdf.styles": \["./styles/resume.css"\],  
  "markdown-pdf.displayHeaderFooter": false,  
  "markdown-pdf.margin.top": "0cm",  
  "markdown-pdf.margin.bottom": "0cm"

  This configuration injects the custom CSS into the headless browser session.  
* **Security constraints:** VS Code restricts local file access. To use local images or fonts, one may need to adjust the security.workspace.trust.enabled settings or use relative paths carefully resolved by the extension.23

#### **5.1.2 Development Cycle**

1. **Split Screen:** Open resume.md in the left pane and resume.css in the right.  
2. **Live Preview:** Open the standard Markdown preview (Ctrl+K V) to monitor content changes.  
3. Export: Run Markdown PDF: Export (pdf) to generate the final artifact.  
   This loop mimics the hot-reload experience of modern frontend development, making it highly intuitive for CS professionals.33

### **5.2 Workflow B: The Pandoc CLI & Automation**

For users who require academic-grade typography (LaTeX) or want to automate the build process via GitHub Actions, **Pandoc** is the engine of choice.

#### **5.2.1 The Haskell AST**

Pandoc works by parsing Markdown into an abstract syntax tree (AST) and then serializing that AST into the target format. This allows for powerful transformations, such as automatically generating a table of contents or converting citations.35

* **HTML-to-PDF Route:** Using Pandoc to generate HTML and then piping it to wkhtmltopdf or WeasyPrint is often preferred over direct PDF generation because it allows the user to stick with CSS for styling.  
  Bash  
  pandoc resume.md \-t html5 \-c resume.css \-o resume.pdf \--pdf-engine=wkhtmltopdf

  This command tells Pandoc to treat the input as HTML5, apply the stylesheet, and use the WebKit engine to print.36

#### **5.2.2 Automation via GitHub Actions**

To achieve true "Resume as Code," the repository can be configured with a CI/CD pipeline. Every time the user pushes a commit (e.g., adding a new job), GitHub Actions spins up a runner, installs Pandoc/Chromium, builds the PDF, and publishes it as a Release artifact.

* **Advantages:**  
  1. **Version History:** Every version of the resume is stored in Git history.  
  2. **Accessibility:** The latest version is always available at a consistent URL (e.g., github.com/user/resume/releases/latest/resume.pdf).  
  3. **Immutability:** The generated PDF is a build artifact, reproducible from the source code.38

## **6\. Optimization for Applicant Tracking Systems (ATS)**

A visually stunning resume is useless if it is rejected by the ATS before a human sees it. "Docs-as-Code" provides unique advantages here, but also pitfalls.

### **6.1 The Parsing Logic**

Modern ATS parsers (like Lever, Greenhouse, Taleo) utilize Optical Character Recognition (OCR) combined with structural heuristics. They look for specific keywords in proximity to dates and semantic headers.

* **Grid Layout Risks:** Early ATS parsers read left-to-right, line-by-line. A two-column layout could result in the parser reading a line from the sidebar, then a line from the main content, scrambling the text.  
* **The Solution:** Using semantic HTML containers (as described in Section 2.3) helps. Furthermore, generating PDFs via Chromium (VS Code/Puppeteer) creates a text layer that is generally more logically ordered than PDFs generated by layout-heavy design tools like InDesign. The *ultimate* safety check is to copy-paste the text from the generated PDF into Notepad. If the text order is logical, the ATS will likely parse it correctly.5

### **6.2 Keyword Optimization via Hidden Text**

One controversial but technically feasible "hack" in the CSS workflow is the inclusion of a "keywords" block that is visible to the ATS but hidden from the human eye.

CSS

.ats-keywords {  
    display: none; /\* or visibility: hidden, or font-size: 0 \*/  
}

*Warning:* Sophisticated ATS algorithms can detect and penalize "keyword stuffing" or hidden text. A safer expert approach is to include a "Technical Skills" section at the bottom of the sidebar that lists these keywords in a small, low-contrast (but visible) font, ensuring they are indexed without dominating the visual hierarchy.5

## **7\. Implementation: The Step-by-Step Build Guide**

This section consolidates the theory into a practical execution plan.

### **7.1 Phase 1: The Blueprint**

Create the project structure:  
/my-resume  
├── content.md \# The Semantic Data  
├── style.css \# The Visual Rules  
├── assets/ \# Images/Icons  
└──.github/  
└── workflows/ \# CI/CD Automation

### **7.2 Phase 2: The Semantic Core**

Draft content.md. Focus purely on data. Use H1 for Name, H2 for Sections, H3 for Roles.

# **Alex Dev**

### **7.3 Phase 3: The Styling Layer**

Draft style.css. Implement the Grid and Print Logic.

CSS

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700\&display=swap');

@page { margin: 0; size: A4; }  
body {  
    font-family: 'Inter', sans-serif;  
    margin: 0;  
    \-webkit-print-color\-adjust: exact;  
}  
.layout-grid {  
    display: grid;  
    grid-template-columns: 28% 72%;  
    height: 100vh;  
}  
.sidebar {  
    background: \#f4f6f8; /\* Subtle Grey \*/  
    padding: 2rem;  
    color: \#2c3e50;  
}  
.main {  
    padding: 2rem;  
    background: \#fff;  
}  
h1, h2, h3 { font-weight: 700; }  
li { margin-bottom: 0.5rem; }  
/\* Critical for single page flow \*/  
h2, h3,.entry { break-inside: avoid; }

### **7.4 Phase 4: The Build**

Open in VS Code. Install "Markdown PDF". Add the CSS path to settings.json. Run export.  
Inspect the output. If the sidebar color doesn't reach the bottom, ensure .layout-grid has height: 100vh and the @page margin is 0\. If icons are missing, check relative paths.

## **8\. Conclusion: The Resume as a Living Artifact**

The "Docs-as-Code" resume represents the convergence of personal branding and software engineering. By adopting this workflow, the computer science professional signals a deep internalization of the industry's best practices: automation, version control, and separation of concerns.

This report has demonstrated that with a rigorous application of semantic Markdown, advanced CSS Grid layouts, and modern rendering pipelines, it is possible to create a document that is not only "unique and modern" but also technically superior to traditional formats. The result is a resume that serves as its own proof of competence—a document that is parsed effectively by machines, admired by humans, and maintained effortlessly by the engineer.

## **9\. Appendix: Technical Reference Tables**

**Table 4: CSS Property Reference for Print Optimization**

| Property | Value | Purpose | Browser Support |
| :---- | :---- | :---- | :---- |
| break-inside | avoid | Prevents element splitting across pages. | Modern Chrome/Firefox (Excellent) |
| print-color-adjust | exact | Forces background colors/images to print. | Modern Chrome/Safari/Firefox |
| page-orientation | upright | Controls rotation of content. | Limited (CSS Paged Media L3) |
| hyphens | auto | Improves text justification in narrow columns. | Requires lang attribute set |
| orphans | 3 | Prevents fewer than 3 lines at page bottom. | Universal |

**Table 5: Common Markdown Extensions for Resumes**

| Extension | Function | Utility for Resume |
| :---- | :---- | :---- |
| **Markdown All in One** | Shortcuts, TOC, List editing | formatting speed. |
| **Markdownlint** | Lints syntax errors | Ensures structural validity for ATS. |
| **Prettier** | Auto-formatting | Keeps the source code clean and readable. |
| **Spell Right** | Spell checking | Critical for avoiding typos. |

By mastering these tools and techniques, the candidate transforms the mundane chore of resume updating into a sophisticated engineering task, resulting in a portfolio that truly stands apart.

#### **Works cited**

1. Composing a resume in markdown \- Scott Berrevoets, accessed December 21, 2025, [https://www.scottberrevoets.com/2025/03/15/composing-a-resume-in-markdown/](https://www.scottberrevoets.com/2025/03/15/composing-a-resume-in-markdown/)  
2. Creating a Maintainable Resume with Markdown and Pandoc \- Daniel Genezini, accessed December 21, 2025, [https://blog.genezini.com/p/creating-a-maintainable-resume-with-markdown-and-pandoc/](https://blog.genezini.com/p/creating-a-maintainable-resume-with-markdown-and-pandoc/)  
3. How to Convert Resume to Markdown \- Resumey.Pro, accessed December 21, 2025, [https://resumey.pro/blog/markdown-resume-creation/](https://resumey.pro/blog/markdown-resume-creation/)  
4. Markdown CV: the ultimate hack to build your resume in 15 minutes, accessed December 21, 2025, [https://resumey.pro/blog/cv-markdown-how-to-create/](https://resumey.pro/blog/cv-markdown-how-to-create/)  
5. Markdown Resume \- Create Professional Resumes with Markdown, accessed December 21, 2025, [https://markdownresume.app/](https://markdownresume.app/)  
6. Pandoc Templates, accessed December 21, 2025, [https://pandoc-templates.org/](https://pandoc-templates.org/)  
7. pandoc-resume | pandoc-templates.org, accessed December 21, 2025, [https://pandoc-templates.org/template/kj-sh604-pandoc-resume/](https://pandoc-templates.org/template/kj-sh604-pandoc-resume/)  
8. How I created my CV with modern HTML and CSS \- Mark Vincze, accessed December 21, 2025, [https://blog.markvincze.com/how-i-created-my-cv-with-modern-html-and-css/](https://blog.markvincze.com/how-i-created-my-cv-with-modern-html-and-css/)  
9. A simple two column CSS grid \- Simon Willison: TIL, accessed December 21, 2025, [https://til.simonwillison.net/css/simple-two-column-grid](https://til.simonwillison.net/css/simple-two-column-grid)  
10. Realizing common layouts using grids \- CSS \- MDN Web Docs, accessed December 21, 2025, [https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid\_layout/Common\_grid\_layouts](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout/Common_grid_layouts)  
11. New Year, New Job? Let's Make a Grid-Powered Resume\! | CSS-Tricks, accessed December 21, 2025, [https://css-tricks.com/new-year-new-job-lets-make-a-grid-powered-resume/](https://css-tricks.com/new-year-new-job-lets-make-a-grid-powered-resume/)  
12. page \- CSS \- MDN Web Docs \- Mozilla, accessed December 21, 2025, [https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@page](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@page)  
13. CSS print page styling \- DocuSeal, accessed December 21, 2025, [https://www.docuseal.com/blog/css-print-page-style](https://www.docuseal.com/blog/css-print-page-style)  
14. Typesetting a Resume with HTML and CSS \- Jack Wrenn, accessed December 21, 2025, [https://jack.wrenn.fyi/blog/pdf-resume-from-html/](https://jack.wrenn.fyi/blog/pdf-resume-from-html/)  
15. page-break-inside \- CSS \- MDN Web Docs, accessed December 21, 2025, [https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/page-break-inside](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/page-break-inside)  
16. break-inside \- CSS \- MDN Web Docs, accessed December 21, 2025, [https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/break-inside](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/break-inside)  
17. Widows and Orphans \- PrintCSS, accessed December 21, 2025, [https://printcss.net/articles/widows-and-orphans](https://printcss.net/articles/widows-and-orphans)  
18. orphans \- CSS-Tricks, accessed December 21, 2025, [https://css-tricks.com/almanac/properties/o/orphans/](https://css-tricks.com/almanac/properties/o/orphans/)  
19. print-color-adjust \- CSS \- MDN Web Docs \- Mozilla, accessed December 21, 2025, [https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/print-color-adjust](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/print-color-adjust)  
20. print-color-adjust \- CSS-Tricks, accessed December 21, 2025, [https://css-tricks.com/almanac/properties/p/print-color-adjust/](https://css-tricks.com/almanac/properties/p/print-color-adjust/)  
21. 10 Font Pairings for Maximum Impact \- Adobe, accessed December 21, 2025, [https://www.adobe.com/express/learn/blog/10-ways-to-pair-fonts-for-maximum-impact](https://www.adobe.com/express/learn/blog/10-ways-to-pair-fonts-for-maximum-impact)  
22. Top 7 best fonts for resumes in 2025: ATS-friendly pick \- CandyCV, accessed December 21, 2025, [https://www.candycv.com/how-to/top-7-best-fonts-for-resumes-in-2025-craft-a-winning-first-impression-10](https://www.candycv.com/how-to/top-7-best-fonts-for-resumes-in-2025-craft-a-winning-first-impression-10)  
23. Changing font used to render a pdf from Markdown in VSCode \- Stack Overflow, accessed December 21, 2025, [https://stackoverflow.com/questions/79755045/changing-font-used-to-render-a-pdf-from-markdown-in-vscode](https://stackoverflow.com/questions/79755045/changing-font-used-to-render-a-pdf-from-markdown-in-vscode)  
24. Popular Google Font and Fontshare Pairings for 2025, accessed December 21, 2025, [https://www.fontpair.co/](https://www.fontpair.co/)  
25. Best Color Palettes for Developer Portfolios (2025) \+ Real Examples \- webportfolios, accessed December 21, 2025, [https://www.webportfolios.dev/blog/best-color-palettes-for-developer-portfolio](https://www.webportfolios.dev/blog/best-color-palettes-for-developer-portfolio)  
26. 40+ Stylish Resume Color Schemes for 2025 \- Design Shack, accessed December 21, 2025, [https://designshack.net/articles/graphics/resume-color-schemes/](https://designshack.net/articles/graphics/resume-color-schemes/)  
27. how can i put fontawesome icons in markdown ? (readme file that will be uploaded to github) \- Stack Overflow, accessed December 21, 2025, [https://stackoverflow.com/questions/63913973/how-can-i-put-fontawesome-icons-in-markdown-readme-file-that-will-be-uploaded](https://stackoverflow.com/questions/63913973/how-can-i-put-fontawesome-icons-in-markdown-readme-file-that-will-be-uploaded)  
28. Font Awesome \- One Step Beyond DevOps, accessed December 21, 2025, [https://devopsdoc.osb.group/help/fontawesome.html](https://devopsdoc.osb.group/help/fontawesome.html)  
29. devicon/README.md at master \- GitHub, accessed December 21, 2025, [https://github.com/devicons/devicon/blob/master/README.md](https://github.com/devicons/devicon/blob/master/README.md)  
30. tandpfun/skill-icons: Showcase your skills on your Github readme or resumé with ease, accessed December 21, 2025, [https://github.com/tandpfun/skill-icons](https://github.com/tandpfun/skill-icons)  
31. Markdown PDF \- Visual Studio Marketplace, accessed December 21, 2025, [https://marketplace.visualstudio.com/items?itemName=yzane.markdown-pdf](https://marketplace.visualstudio.com/items?itemName=yzane.markdown-pdf)  
32. Visual Studio Code Security: Markdown Vulnerabilities in Third-Party Extensions (2/3), accessed December 21, 2025, [https://www.sonarsource.com/blog/vscode-security-markdown-vulnerabilities-in-extensions/](https://www.sonarsource.com/blog/vscode-security-markdown-vulnerabilities-in-extensions/)  
33. tengjuilin/markdown-resume: A simple, elegant, and fast workflow to write resumes and CVs in Markdown. \- GitHub, accessed December 21, 2025, [https://github.com/tengjuilin/markdown-resume](https://github.com/tengjuilin/markdown-resume)  
34. Markdown and Visual Studio Code, accessed December 21, 2025, [https://code.visualstudio.com/docs/languages/markdown](https://code.visualstudio.com/docs/languages/markdown)  
35. Demos \- Pandoc, accessed December 21, 2025, [https://pandoc.org/demos.html](https://pandoc.org/demos.html)  
36. The Markdown Resume \- GitHub Pages, accessed December 21, 2025, [https://mszep.github.io/pandoc\_resume/](https://mszep.github.io/pandoc_resume/)  
37. Create a PDF Resume with Markdown, CSS, and Pandoc \- Small Sharp Software Tools, accessed December 21, 2025, [https://smallsharpsoftwaretools.com/tutorials/pandoc\_resume/](https://smallsharpsoftwaretools.com/tutorials/pandoc_resume/)  
38. Markdown CV Generator: Consistent designs matter \- Charlie Macnamara, accessed December 21, 2025, [https://www.charliemacnamara.uk/blog/markdown-cv/](https://www.charliemacnamara.uk/blog/markdown-cv/)  
39. Resume-md: Manage your resume with GitHub and Markdown \- DEV Community, accessed December 21, 2025, [https://dev.to/siph/resume-md-manage-your-resume-with-github-and-markdown-25f7](https://dev.to/siph/resume-md-manage-your-resume-with-github-and-markdown-25f7)  
40. Build your resume using markdown \- Allan Fernandes, accessed December 21, 2025, [https://www.allanfernandes.dev/blog/build-your-resume-using-markdown](https://www.allanfernandes.dev/blog/build-your-resume-using-markdown)  
41. Colors on a Resume: What Do Employers Really Think in 2025?, accessed December 21, 2025, [https://www.easyresume.io/career-advice/colors-on-a-resume](https://www.easyresume.io/career-advice/colors-on-a-resume)