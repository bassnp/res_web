<style>
/* ============================================================================
   CSS Paged Media - Print-Optimized Resume Stylesheet
   Designed for A4/Letter with zero-margin bleed layout
   ============================================================================ */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

@page {
    size: A4 portrait;
    margin: 0;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 10pt;
    line-height: 1.4;
    color: #2c3e50;
    background: #ffffff;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}

/* Grid Layout Container */
.resume-container {
    display: grid;
    grid-template-columns: 1fr 2.2fr;
    min-height: 100vh;
    height: 100vh;
}

/* Sidebar Styling */
.sidebar {
    background: linear-gradient(180deg, #3d405b 0%, #2c2f42 100%);
    color: #f4f1de;
    padding: 1rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
}

.sidebar h1 {
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 0.1rem;
    color: #ffffff;
}

.sidebar .title {
    font-size: 0.75rem;
    font-weight: 500;
    color: #81b29a;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.2rem;
}

.sidebar h2 {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #f2cc8f;
    border-bottom: 1px solid rgba(242, 204, 143, 0.3);
    padding-bottom: 0.2rem;
    margin-bottom: 0.35rem;
}

.sidebar ul {
    list-style: none;
    padding: 0;
}

.sidebar li {
    font-size: 0.7rem;
    margin-bottom: 0.15rem;
    color: #e8e4d9;
}

.sidebar a {
    color: #81b29a;
    text-decoration: none;
}

.sidebar a:hover {
    text-decoration: underline;
}

.contact-item {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.7rem;
    margin-bottom: 0.2rem;
}

.skill-category {
    margin-bottom: 0.45rem;
}

.skill-category h3 {
    font-size: 0.6rem;
    font-weight: 600;
    color: #e07a5f;
    margin-bottom: 0.15rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.skill-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.2rem;
}

.skill-tag {
    background: rgba(129, 178, 154, 0.2);
    color: #c5d9cf;
    padding: 0.1rem 0.35rem;
    border-radius: 3px;
    font-size: 0.6rem;
    font-family: 'JetBrains Mono', monospace;
}

/* Main Content Styling */
.main-content {
    background: #ffffff;
    padding: 1rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
}

.main-content h2 {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #3d405b;
    border-bottom: 2px solid #e07a5f;
    padding-bottom: 0.2rem;
    margin-bottom: 0.35rem;
}

.summary {
    font-size: 0.75rem;
    line-height: 1.4;
    color: #4a5568;
}

/* Experience & Project Entries */
.entry {
    break-inside: avoid;
    page-break-inside: avoid;
    margin-bottom: 1rem;
}

.entry-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 0.1rem;
}

.entry h3 {
    font-size: 0.8rem;
    font-weight: 600;
    color: #2c3e50;
}

.entry .period {
    font-size: 0.65rem;
    color: #718096;
    font-style: italic;
}

.entry .company {
    font-size: 0.7rem;
    font-weight: 500;
    color: #e07a5f;
    margin-bottom: 0.15rem;
}

.entry ul {
    padding-left: 0.9rem;
    margin: 0;
}

.entry li {
    font-size: 0.7rem;
    margin-bottom: 0.1rem;
    color: #4a5568;
    line-height: 1.35;
}

.entry li::marker {
    color: #81b29a;
}

.tech-stack {
    display: flex;
    flex-wrap: wrap;
    gap: 0.15rem;
    margin-top: 0.2rem;
}

.tech-tag {
    background: #f0f4f8;
    color: #3d405b;
    padding: 0.05rem 0.3rem;
    border-radius: 2px;
    font-size: 0.55rem;
    font-family: 'JetBrains Mono', monospace;
    border: 1px solid #e2e8f0;
}

/* Education Section in Sidebar */
.education-entry {
    margin-bottom: 0.25rem;
}

.education-entry .degree {
    font-size: 0.7rem;
    font-weight: 600;
    color: #ffffff;
}

.education-entry .institution {
    font-size: 0.65rem;
    color: #c5d9cf;
}

.education-entry .date {
    font-size: 0.6rem;
    color: #a0aec0;
    font-style: italic;
}

/* Portrait Image */
.portrait {
    width: 110px;
    height: 110px;
    border-radius: 50%;
    object-fit: cover;
    object-position: center 15%;
    border: 3px solid #81b29a;
    margin: 0 auto 0.25rem auto;
    display: block;
}

/* Print Fragmentation Prevention */
section, article, .entry, .skill-category {
    break-inside: avoid;
    page-break-inside: avoid;
}

h2, h3 {
    break-after: avoid;
    page-break-after: avoid;
}

/* Orphan/Widow Control */
p, li {
    orphans: 3;
    widows: 3;
}
</style>

<div class="resume-container">

<aside class="sidebar">

<header>
<img src="https://i.gyazo.com/7543c8991396edc6b9171ec9ac01cd9b.jpg" alt="Jaden Bruha" class="portrait">
<h1>Jaden Bruha</h1>
<div class="title">Software Engineer</div>
</header>

<section>
<h2>Contact</h2>
<div class="contact-item">jbruha@csus.edu</div>
<div class="contact-item"><a href="https://github.com/bassnp">github.com/bassnp</a></div>
<div class="contact-item"><a href="https://jadenbruha.com">jadenbruha.com</a></div>
</section>

<section>
<h2>Education</h2>
<div class="education-entry">
<div class="degree">B.S. Computer Science</div>
<div class="institution">California State University, Sacramento</div>
<div class="date">December 2025</div>
</div>
</section>

<section>
<h2>Technical Skills</h2>

<div class="skill-category">
<h3>Languages</h3>
<div class="skill-tags">
<span class="skill-tag">Python</span>
<span class="skill-tag">JavaScript</span>
<span class="skill-tag">TypeScript</span>
<span class="skill-tag">Dart</span>
<span class="skill-tag">Lua</span>
<span class="skill-tag">Java</span>
<span class="skill-tag">SQL</span>
</div>
</div>

<div class="skill-category">
<h3>Frameworks</h3>
<div class="skill-tags">
<span class="skill-tag">FastAPI</span>
<span class="skill-tag">Next.js</span>
<span class="skill-tag">React</span>
<span class="skill-tag">Flutter</span>
<span class="skill-tag">LangGraph</span>
<span class="skill-tag">LangChain</span>
<span class="skill-tag">Tailwind</span>
</div>
</div>

<div class="skill-category">
<h3>AI & ML</h3>
<div class="skill-tags">
<span class="skill-tag">Google Gemini</span>
<span class="skill-tag">OpenAI API</span>
<span class="skill-tag">RAG Systems</span>
<span class="skill-tag">MCP Servers</span>
<span class="skill-tag">Prompt Eng.</span>
</div>
</div>

<div class="skill-category">
<h3>DevOps & Cloud</h3>
<div class="skill-tags">
<span class="skill-tag">Docker</span>
<span class="skill-tag">Firebase</span>
<span class="skill-tag">MongoDB</span>
<span class="skill-tag">Redis</span>
<span class="skill-tag">Git</span>
<span class="skill-tag">CI/CD</span>
</div>
</div>

</section>

<section>
<h2>Attributes</h2>
<ul>
<li>Agile/Scrum (Jira)</li>
<li>Comprehensive Testing</li>
<li>Technical Documentation</li>
<li>Team Collaboration</li>
<li>Self-Taught Foundation</li>
</ul>
</section>

</aside>

<main class="main-content">

<section>
<h2>Professional Summary</h2>
<p class="summary">
Full-stack engineer (B.S. Computer Science, Dec 2025) building AI-powered applications and agentic systems. Shipped production software to clients, developed LangGraph research agents, and generated $6k SaaS revenue. Programming since age 15.
</p>
</section>

<section>
<h2>Featured Projects</h2>

<article class="entry">
<div class="entry-header">
<h3>ChurchLink — Web & App Builder Platform</h3>
<span class="period">Nov 2025</span>
</div>
<div class="company">Senior Graduation Project · Team of 6 · Client Delivery</div>
<ul>
<li>Built FastAPI backend with Firebase/MongoDB sync across web and mobile clients</li>
<li>Implemented multi-language localization with per-feature translation management</li>
<li>Integrated PayPal payment processing for donations and event registration</li>
</ul>
<div class="tech-stack">
<span class="tech-tag">Python</span>
<span class="tech-tag">Flutter</span>
<span class="tech-tag">TypeScript</span>
<span class="tech-tag">FastAPI</span>
<span class="tech-tag">Firebase</span>
<span class="tech-tag">MongoDB</span>
<span class="tech-tag">PayPal</span>
</div>
</article>

<article class="entry">
<div class="entry-header">
<h3>GenUI Deep Researcher Agent</h3>
<span class="period">Nov 2025</span>
</div>
<div class="company">Personal Project · AI Web Research System</div>
<ul>
<li>Designed LangGraph 7-phase pipeline for web analysis and structured report generation</li>
<li>Integrated Google CSE API with weighted parallel scoring for result ranking</li>
<li>Implemented circuit breaker pattern (5-failure threshold, 60s reset) for fault tolerance</li>
</ul>
<div class="tech-stack">
<span class="tech-tag">Google Gemini</span>
<span class="tech-tag">LangGraph</span>
<span class="tech-tag">FastAPI</span>
<span class="tech-tag">Redis</span>
<span class="tech-tag">Docker</span>
<span class="tech-tag">SSE Streaming</span>
</div>
</article>

<article class="entry">
<div class="entry-header">
<h3>Zharvis — Videogame AI Overlay</h3>
<span class="period">Oct 2025</span>
</div>
<div class="company">SaaS Product · Overwolf Marketplace</div>
<ul>
<li>Built RAG pipeline processing 15k+ wiki documents with sub-second vector retrieval</li>
<li>Architected MCP server enabling Gemini to build Generative UI HUD components</li>
<li>Designed horizontally-scalable Docker pods for real-time in-game AI assistance</li>
</ul>
<div class="tech-stack">
<span class="tech-tag">Gemini</span>
<span class="tech-tag">Overwolf SDK</span>
<span class="tech-tag">LangChain</span>
<span class="tech-tag">MCP</span>
<span class="tech-tag">TypeScript</span>
<span class="tech-tag">Docker</span>
</div>
</article>

<article class="entry">
<div class="entry-header">
<h3>Interactive AI Portfolio</h3>
<span class="period">Dec 2025</span>
</div>
<div class="company">Full-Stack SSG Application</div>
<ul>
<li>Developed Next.js 15 + React 19 SSG with Radix UI and custom animations</li>
<li>Built SSE streaming backend for real-time 8-phase agentic pipeline visualization</li>
<li>Implemented SPOT data architecture with auto-generated configs from JSON schemas</li>
</ul>
<div class="tech-stack">
<span class="tech-tag">Next.js 15</span>
<span class="tech-tag">React 19</span>
<span class="tech-tag">FastAPI</span>
<span class="tech-tag">LangGraph</span>
<span class="tech-tag">Tailwind</span>
<span class="tech-tag">Radix UI</span>
</div>
</article>

<article class="entry">
<div class="entry-header">
<h3>CS:GO Modding SaaS</h3>
<span class="period">Jan 2023</span>
</div>
<div class="company">Team Lead · $6k Revenue</div>
<ul>
<li>Led 3-developer team building and selling videogame mods via freelance contracts</li>
<li>Developed performance-optimized Lua scripts for real-time gameplay modifications</li>
</ul>
<div class="tech-stack">
<span class="tech-tag">Lua</span>
<span class="tech-tag">Team Leadership</span>
<span class="tech-tag">Freelancing</span>
</div>
</article>

<article class="entry">
<div class="entry-header">
<h3>Ethereum GPU Mining Rig</h3>
<span class="period">Apr 2022</span>
</div>
<div class="company">Personal Project · Passive Income</div>
<ul>
<li>Assembled 7-GPU rig (Nvidia/AMD) achieving ~190 MH/s hashrate</li>
<li>Generated ~$125/month passive income before Ethereum Merge ended PoW mining</li>
</ul>
<div class="tech-stack">
<span class="tech-tag">Ethereum</span>
<span class="tech-tag">GPU Parallelism</span>
<span class="tech-tag">Hardware</span>
</div>
</article>

</section>

</main>

</div>
