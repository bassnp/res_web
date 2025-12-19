# Backend Documentation Directive

## Agent Configuration

Role: Technical Documentation Specialist  
Domain: Python Backend Systems, Agent Frameworks, API Services  
Execution Mode: Precision-Constrained Enumeration  
Priority: Factual Precision Within Space Constraints  
Output Limit: **1500 lines maximum**

---

## Critical Mandate

Accuracy is non-negotiable. The output document must not exceed **1500 lines**. Within this constraint, prioritize:

1. **Public API surface** (endpoints, exported functions, key classes)
2. **Core business logic** (agents, workflows, orchestration)
3. **Data models** (schemas, state definitions)
4. **Critical integrations** (external services, authentication)

Omit verbose explanations of trivial utilities. Speculation is prohibited. Ambiguity must be explicitly flagged.

---

## Primary Objective

Generate a comprehensive, surgically precise technical reference document for the backend system. This document must serve as the authoritative source of truth for all backend components, enabling any developer to understand the complete system architecture without consulting source code.

The project type, frameworks, and architecture must be discovered through code analysis, not assumed.

---

## Documentation Scope

### Target Directory Structure

Enumerate the complete directory structure of `backend/` at execution time. Document every file discovered, regardless of whether it existed when this directive was authored.

```
backend/
    [Enumerate all Python modules at root level]
    [Enumerate all configuration files: .yml, .yaml, .json, .toml, .env*]
    [Enumerate all infrastructure files: Dockerfile*, docker-compose*, requirements*]
    models/
        [Enumerate all modules]
    nodes/
        [Enumerate all modules]
    routers/
        [Enumerate all modules]
    services/
        [Enumerate all modules]
    utils/
        [Enumerate all modules]
    tests/
        [Enumerate all test modules]
    [Enumerate any additional subdirectories discovered]
```

CRITICAL: The structure above is illustrative. You must perform directory traversal to discover the actual current state of the codebase. Do not assume this structure is complete or accurate.

---

## Documentation Protocol

### General Principles

Document each module, class, function, and configuration using natural prose or structured format as appropriate to convey maximum clarity. The format is flexible; the accuracy is not.

### Required Information Per Module

For each Python module, capture the following information in whatever format best communicates the facts:

**Module Identity**
- File name and path
- Primary responsibility
- Key dependencies (imports)

**Symbols Defined**
- Classes: name, inheritance, purpose, key attributes, method signatures and behaviors
- Functions: name, parameters with types, return type, purpose, notable side effects
- Constants: name, value, usage context
- Models/Schemas: fields, types, constraints, validation rules

**Behavioral Details**
- Exception handling patterns
- External service calls
- State mutations
- Async/await patterns where relevant

### Flexibility Clause

The documentation format may adapt to the complexity of each component:
- Simple utility functions may be documented briefly
- Complex orchestration logic warrants detailed explanation
- Use tables, lists, prose, or code blocks as clarity demands

What remains constant: every public symbol must be documented, every type must be stated, every behavior must be described factually.

---

## Component-Specific Guidelines

### Agent/Workflow Architecture

If graph-based agent frameworks are present, document:
- Framework identification
- Graph/workflow topology (nodes, edges, conditions)
- State schema and field mutations
- Entry points and termination conditions

Format as diagram, table, or prose based on complexity.

### API Endpoints

For web frameworks, document:
- Route paths and HTTP methods
- Request/response schemas
- Authentication and authorization
- Error responses

### External Integrations

For external services, document:
- Service identity and purpose
- Connection mechanism
- Endpoints consumed
- Error handling approach

---

## Accuracy Requirements

### Core Principles

- Every statement must be verifiable against the source code
- Ambiguity must be explicitly noted rather than resolved through inference
- Missing information must be flagged, not fabricated
- Types must reflect actual implementation, not assumptions

### Validation Guidelines

- Cross-reference function calls to ensure documented functions exist
- Verify import statements match actual dependencies
- Confirm state mutations align with defined schemas
- Trace control flow through actual code paths

### What Constitutes Failure

- Documenting behavior that does not exist in code
- Omitting public symbols without explicit justification
- Stating types that differ from implementation
- Conflating distinct functions or classes

---

## Documentation Guidelines

To maintain accuracy and usefulness:

- Document individual functions rather than grouping as "utility functions"
- Include all parameters and return types, even when seemingly obvious
- Verify behavior through code reading, not name inference
- Include internal and private methods where they affect understanding
- Keep documentation of distinct symbols separate
- Avoid vague placeholders; be specific or note gaps explicitly

---

## Output Guidelines

### Hard Constraint: 1500 Lines Maximum

The final documentation must not exceed **1500 lines**. To achieve this:

- Use terse, technical prose—no filler words
- Combine related symbols into compact tables where appropriate
- Document trivial getters/setters in single lines or omit if obvious
- Prioritize depth on complex logic; brevity on simple utilities
- Use bullet points over paragraphs when listing facts

### Document Structure

Organize documentation to reflect the actual codebase architecture. Suggested sections include:

- **System Overview**: High-level architecture and component relationships
- **Configuration**: Environment variables, settings, constants
- **Data Models**: Schemas, types, validation rules
- **Core Logic**: Primary business logic, agents, workflows
- **API Surface**: Endpoints, request/response contracts
- **Services**: External integrations, utilities
- **Infrastructure**: Deployment configuration, dependencies

### Structural Flexibility

- Section organization should mirror the codebase structure
- Create sections for what exists; omit sections for what does not
- Depth of documentation should match complexity of component
- Use the format (prose, tables, lists, diagrams) that maximizes clarity

### Mandatory Elements

- Complete symbol index (all classes, functions, constants)
- Dependency relationships between modules
- Type information for all public interfaces

---

## Execution Mandate

Factual accuracy within the 1500-line constraint. Every claim must be traceable to source code. Every type must be verified.

**Conciseness Strategy:**
- Merge trivial functions into summary tables
- Use signature-only documentation for self-explanatory utilities
- Reserve detailed prose for complex orchestration and business logic
- Omit boilerplate patterns (standard CRUD, obvious constructors) unless non-trivial

Proceed with precision. Document what matters. Compress what doesn't. Stay under 1500 lines.

---

## OUTPUT DENSITY REQUIREMENT

**HARD LIMIT: 1500 LINES MAXIMUM. NO EXCEPTIONS.**

THE FINAL DOCUMENTATION MUST BE **ZERO-FLUFF AND MAXIMALLY INFORMATION-DENSE**. EVERY SENTENCE MUST CONVEY TECHNICAL SUBSTANCE.

**ELIMINATE:**
- Conversational preambles or conclusions
- Redundant explanations of obvious concepts
- Vague qualitative descriptions without technical backing
- Repetitive pattern documentation (document pattern once, reference thereafter)

**COMPRESSION TECHNIQUES:**
- Use tables for function signatures with similar patterns
- Single-line entries for trivial constants and simple utilities
- Inline type annotations instead of separate type descriptions
- Reference common patterns by name instead of re-explaining

IF APPROACHING 1500 LINES, PRIORITIZE: API surface > core logic > models > utilities > tests.