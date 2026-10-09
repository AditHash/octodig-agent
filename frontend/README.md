# OctoDig Frontend References

This folder holds user-supplied UI/design reference documents and frontend-scoped guidance. **There is no frontend application here yet.** These Markdown files are inputs for future design work, not proof that a UI has been built.

## Source files (preserved)

- [openai-DESIGN.md](openai-DESIGN.md) — an uploaded analysis of a restrained, lightweight OpenAI-inspired interface: visual rhythm, system typography, palette, spacing, contrast concerns and UI patterns. **This is a user-supplied design analysis, not an official OpenAI design-system package or an endorsement.** Treat its tokens as reference examples; do not copy proprietary branding or blindly reuse low-contrast text colors.
- [taste-SKILL.md](taste-SKILL.md) — an uploaded, detailed anti-template frontend design guide. It explicitly targets **landing pages, portfolios and redesigns**, **not dashboards, data tables or multistep product interfaces**. Apply the relevant context-specific rules to future marketing/landing pages; do not impose its landing-page composition restrictions on OctoDig's research workspace.

## How to use these references

1. Read the product requirements in [../docs/PRD.md](../docs/PRD.md) and [../docs/REPORT_CONTRACT.md](../docs/REPORT_CONTRACT.md) before choosing a visual direction.
2. For a public OctoDig landing page, use the supplied design references as inspiration, not as mandatory brand tokens or vendor ownership claims.
3. For the **research application** (jobs, sources, evidence, report sections, outreach, settings, billing/usage), prioritize accessible information hierarchy, trustworthy source provenance, productive data density, responsive layouts and explicit status states. The uploaded taste skill says these app screens are outside its principal scope.
4. Establish original OctoDig design tokens with WCAG-compliant contrast and test them in light and dark modes if both are supported.
5. Design success, empty, loading, interrupted, partial-result and error states. Evidence must be understandable and verifiable before polished animations.
6. Decide the actual frontend framework and component system when implementation begins; do not introduce packages solely because a reference document lists them.

## Development status

No React, Next.js, package.json, component library, or app screens have been committed by adding these references. Create those only as part of a frontend implementation milestone.

See [AGENTS.md](AGENTS.md) for future contributors' rules.
