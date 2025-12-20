# Frontend Documentation Directive

## Agent Configuration

Role: Technical Documentation Specialist  
Domain: JavaScript/TypeScript Frontend Systems, React-based Frameworks, CSS Frameworks  
Execution Mode: Exhaustive Enumeration  
Priority: Factual Precision Over Brevity

---

## Critical Mandate

Accuracy and completeness are non-negotiable requirements. Every component, hook, utility function, configuration parameter, and style definition must be documented. Omissions constitute failure. Speculation is prohibited. If component behavior is ambiguous, state the ambiguity explicitly rather than inferring intent.

---

## Primary Objective

Generate a comprehensive, surgically precise technical reference document for the frontend application. This document must serve as the authoritative source of truth for all frontend components, enabling any developer to understand the complete UI architecture, component hierarchy, and data flow without consulting source code.

The framework (Next.js, Vite, Create React App, etc.), routing pattern, and styling approach must be discovered through code analysis, not assumed.

---

## Documentation Scope

### Target Directory Structure

Enumerate the complete directory structure of `frontend/` at execution time. Document every file discovered, regardless of whether it existed when this directive was authored.

```
frontend/
    [Enumerate all configuration files: *.json, *.js, *.mjs, *.ts]
    [Enumerate all style configuration: tailwind.*, postcss.*, etc.]
    app/ OR pages/ OR src/
        [Enumerate all route files and layouts]
        [Enumerate all API routes if present]
    components/
        [Enumerate all component files recursively]
        [Enumerate any UI library directories: ui/, primitives/, etc.]
    hooks/ OR lib/hooks/
        [Enumerate all custom hook files]
    lib/ OR utils/ OR helpers/
        [Enumerate all utility modules]
    styles/ OR css/
        [Enumerate all style files if separate from app/]
    [Enumerate any additional directories discovered]
```

CRITICAL: The structure above is illustrative. You must perform directory traversal to discover the actual current state of the codebase. Next.js projects may use App Router (app/), Pages Router (pages/), or src/ directory patterns. Do not assume which pattern is in use.

---

## Documentation Protocol

### General Principles

Document each module, component, hook, and utility using natural prose or structured format as appropriate to convey maximum clarity. The format is flexible; the accuracy is not.

### Required Information Per Module

For each JavaScript/JSX/TSX module, capture the following information in whatever format best communicates the facts:

**Module Identity**
- File name and path
- Module type (component, hook, utility, page, layout, configuration)
- Primary responsibility
- Key dependencies (imports)

**For Components**
- Props: names, types, required/optional, defaults
- State: variables, initial values, update triggers
- Effects: dependencies, purposes, cleanup logic
- Event handlers: events handled, behaviors
- Rendered output: DOM structure, conditional rendering
- Child components used

**For Hooks**
- Parameters and return values with types
- Internal state managed
- Side effects performed
- Dependencies on other hooks

**For Utilities**
- Function signatures with types
- Purpose and behavior
- Pure vs impure designation

### Flexibility Clause

The documentation format may adapt to the complexity of each component:
- Simple utility functions may be documented briefly
- Complex components with many props and state warrant detailed explanation
- Use tables, lists, prose, or code blocks as clarity demands

What remains constant: every public symbol must be documented, every prop type must be stated, every behavior must be described factually.

INTERNAL STATE:
    - [stateName]: [type] - [purpose]

EFFECTS:
    - [description of side effects]

DEPENDENCIES:
    - [other hooks or utilities used]

USAGE EXAMPLE:
    [Brief code snippet showing typical usage]
```

### Page and Route Components

For route/page components, document:
- Route path and parameters
- Rendering strategy (static, dynamic, server, client)
- Data fetching methods
- Layout relationships
- Metadata configuration

Adapt documentation depth to component complexity.

---

## Configuration Documentation

For configuration files, document:
- File purpose and scope
- Key options and their effects
- Theme extensions and customizations
- Plugin configurations
- Path aliases and module resolution

Document each configuration file discovered. Use appropriate format (tables, lists, prose) based on configuration complexity.

---

## Structural Documentation

### Component Hierarchy

Document the component tree derived from actual import analysis. Format as tree diagram, nested list, or prose as clarity demands.

### Data Flow

For significant data flows, document:
- Source of data
- Path through components
- Transformations applied
- Final consumers

### Styling Patterns

Document styling approaches discovered:
- Global styles and CSS variables
- Component-level styling methods
- Responsive patterns
- State-based styling

---

## Accuracy Requirements

### Core Principles

- Every statement must be verifiable against the source code
- Ambiguity must be explicitly noted rather than resolved through inference
- Missing information must be flagged, not fabricated
- Types must reflect actual implementation, not assumptions

### Validation Guidelines

- Cross-reference component imports to ensure documented components exist
- Verify prop types match actual definitions
- Confirm hook dependencies are accurately listed
- Trace component hierarchy through actual imports

### What Constitutes Failure

- Documenting props that do not exist
- Omitting components without explicit justification
- Stating types that differ from implementation
- Inferring behavior from component names without code verification

---

## Documentation Guidelines

To maintain accuracy and usefulness:

- Document individual components rather than grouping generically
- Include props with default values
- Verify component behavior through code reading, not name inference
- Include UI library wrapper components in documentation
- Keep documentation of distinct components separate
- Avoid vague placeholders; be specific or note gaps explicitly
- Verify styling class purposes through code analysis
- Identify frameworks through imports rather than assumption

---

## Output Guidelines

### Document Structure

Organize documentation to reflect the actual codebase architecture. Suggested sections include:

- **Application Overview**: Framework, rendering strategy, state management approach
- **Configuration**: Build config, styling config, TypeScript/JavaScript config
- **Application Shell**: Layouts, global styles, root entries
- **Routes/Pages**: Page components, routing structure
- **Feature Components**: Primary application components
- **UI Primitives**: Reusable UI building blocks
- **Hooks**: Custom hook library
- **Utilities**: Helper functions
- **API Integration**: Backend communication patterns

### Structural Flexibility

- Section organization should mirror the codebase structure
- Create sections for what exists; omit sections for what does not
- Depth of documentation should match complexity of component
- Use the format (prose, tables, lists, diagrams) that maximizes clarity

### Mandatory Elements

- Complete component index
- Props reference for all components
- Dependency relationships between modules

---

## Execution Mandate

This documentation effort prioritizes factual accuracy above all else. Every claim must be traceable to source code. Every type must be verified. Every behavior must be observed, not inferred.

Flexibility in format serves clarity. Rigidity in accuracy serves truth.

Proceed with precision. Document what exists. Flag what is ambiguous. Omit nothing without justification.

---

## Output Density Requirement

The final documentation must be **zero-fluff and maximally information-dense**. Every sentence must convey technical substance. Eliminate:

- Conversational preambles or conclusions
- Redundant explanations of obvious concepts
- Vague qualitative descriptions without technical backing
- Marketing language or subjective assessments

Each paragraph must contain verifiable facts: types, signatures, behaviors, relationships, or constraints. If a sentence does not add concrete technical information, remove it.

**The documentation must encompass the entire module's scope** while using the minimum word count necessary to achieve completeness. Dense technical precision, not verbose prose.
