---
name: GuideRail
description: An evidence-led repair-center worksheet that turns a vague complaint into a validated troubleshooting plan.
colors:
  paper: "#f3efe6"
  sheet: "#fffdf8"
  ink: "#171a1f"
  muted-ink: "#5f635f"
  rule: "#c9c3b8"
  rule-strong: "#6f695f"
  action-cobalt: "#1246d8"
  action-cobalt-dark: "#0b2f9a"
  action-wash: "#eef2ff"
  complete-wash: "#f7f5ee"
  verified-green: "#0d6a4b"
  warning-umber: "#8a4b09"
  error-red: "#9f1d1d"
  focus-orange: "#e46c1c"
  selection-blue: "#c9d6ff"
  code-surface: "#20242a"
  code-ink: "#eff3f6"
typography:
  display:
    fontFamily: "Georgia, serif"
    fontSize: "clamp(3rem, 6.8vw, 6rem)"
    fontWeight: 700
    lineHeight: 0.98
    letterSpacing: "-0.035em"
  headline:
    fontFamily: "Georgia, serif"
    fontSize: "clamp(1.6rem, 2.4vw, 2.2rem)"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Aptos, Segoe UI, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 700
    lineHeight: 1.4
  body:
    fontFamily: "Aptos, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Aptos, Segoe UI, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.08em"
  mono:
    fontFamily: "Cascadia Mono, Consolas, monospace"
    fontSize: "0.78rem"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  field: "8px"
  action: "9px"
  surface: "14px"
  pill: "999px"
  circle: "50%"
spacing:
  xs: "0.45rem"
  sm: "0.75rem"
  md: "1rem"
  lg: "1.4rem"
  xl: "2rem"
  section: "3rem"
components:
  button-primary:
    backgroundColor: "{colors.action-cobalt}"
    textColor: "#ffffff"
    typography: "{typography.body}"
    rounded: "{rounded.action}"
    padding: "0 1.1rem"
    height: "54px"
  button-primary-hover:
    backgroundColor: "{colors.action-cobalt-dark}"
    textColor: "#ffffff"
    rounded: "{rounded.action}"
  chip-example:
    backgroundColor: "transparent"
    textColor: "{colors.muted-ink}"
    rounded: "{rounded.pill}"
    padding: "0.55rem 0.75rem"
    height: "44px"
  input-complaint:
    backgroundColor: "#ffffff"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "1rem"
  panel-workspace:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    rounded: "0"
  stage-active:
    backgroundColor: "{colors.action-wash}"
    textColor: "{colors.ink}"
    rounded: "0"
  stage-complete:
    backgroundColor: "{colors.complete-wash}"
    textColor: "{colors.ink}"
    rounded: "0"
---

# Design System: GuideRail

## Overview

**Creative North Star: "The Repair-Center Diagnostic Worksheet"**

GuideRail should feel like a deliberate paper instrument used by a careful technician: calm, legible, inspectable, and built to make cause and effect visible. A warm pale paper surrounds a cleaner worksheet surface; strong rules, tabular measurements, and an editorial serif hierarchy give the interface authority without imitating proprietary device UI.

The core visual mechanism is complaint-to-plan: complaint intake remains on the left, the validated plan remains on the right, and evidence plus hard guardrails stay in view. Enrich, Retrieve, Resolve, and Validate form the signature process rail, making the deterministic safety envelope visible before and after execution.

**Key Characteristics:**

- Warm paper and clean sheet surfaces with structural rules.
- Editorial serif hierarchy over a restrained operational sans body.
- Action-only cobalt, with green reserved exclusively for verified deeplinks.
- Visible evidence, guardrails, stage state, latency, and execution trace.
- Responsive compaction that preserves the complaint-to-plan mechanism.

## Colors

The palette is a warm archival neutral field punctuated by one operational cobalt and one narrowly reserved verification green.

### Primary

- **Action Cobalt** (`action-cobalt`): Drives the plan-building action, active stage marker, caret, and interactive border states.
- **Deep Action Cobalt** (`action-cobalt-dark`): Signals hover, completion emphasis, and secondary action text without introducing another hue.

### Secondary

- **Verified Green** (`verified-green`): Appears only on catalog-validated deeplinks and their verification label.

### Tertiary

- **Warning Umber** (`warning-umber`): Marks disclosure and service-check status where attention is needed but the plan has not failed.
- **Error Red** (`error-red`): Reserved for failed plan generation and critical-action classification.

### Neutral

- **Pale Repair Paper** (`paper`): The page ground and sticky header material.
- **Worksheet Sheet** (`sheet`): The stage rail and complaint-to-plan work surface.
- **Carbon Ink** (`ink`): Primary copy, heavy rules, and footer field.
- **Graphite Note** (`muted-ink`): Supporting explanation, metadata, and inactive control text.
- **Pencil Rule** (`rule`) and **Dark Rule** (`rule-strong`): Establish hierarchy through borders rather than extra containers.
- **Active Wash** (`action-wash`) and **Completed Wash** (`complete-wash`): Quiet stage-state fills that preserve the paper character.
- **Code Surface** (`code-surface`) and **Code Ink** (`code-ink`): Isolate raw API output as a technical artifact.

### Named Rules

**The Action-Only Cobalt Rule.** Cobalt identifies actions, interaction states, and process progression; it is not decorative color.

**The Verified-Green Rule.** Green is exclusive to exact, catalog-validated deeplinks. Never use it for generic success, service readiness, or completed stages.

**The Paper-First Rule.** Preserve the warm paper and sheet relationship; do not replace it with a generic cool-gray application shell.

## Typography

**Display Font:** Georgia (with serif fallback)  
**Body Font:** Aptos (with Segoe UI and sans-serif fallbacks)  
**Label/Mono Font:** Aptos for labels; Cascadia Mono with Consolas fallback for raw JSON and counters

**Character:** The serif is editorial and declarative, framing the product as a serious diagnostic instrument. The sans body is quiet and operational, while monospace is limited to machine evidence and numbered traces.

### Hierarchy

- **Display** (700, `clamp(3rem, 6.8vw, 6rem)`, 0.98): The single page thesis, held to roughly 13 characters per line.
- **Headline** (700, `clamp(1.6rem, 2.4vw, 2.2rem)`, 1.1): Worksheet section headings and major evidence statements.
- **Title** (700, 1.05rem, compact): Action names and concise local headings.
- **Body** (400, 1rem, 1.55): Operational explanation and form content, generally constrained to 48–68 characters per line where prose is prominent.
- **Label** (700, 0.78rem, 0.08em): Uppercase metadata, categories, summary labels, and dividers.
- **Mono** (400, 0.78rem, 1.55): JSON, numerical counters, and machine-readable evidence only.

### Named Rules

**The Editorial-Over-Operational Rule.** Use serif for thesis and section hierarchy; use sans for controls, evidence, and instructions.

**The Machine-Evidence Rule.** Monospace belongs to raw API output and compact counters, never to primary product messaging.

## Layout

The page uses a centered container capped at 1480px with a slim exterior gutter. Its wide-screen composition is intentionally asymmetric: the preamble pairs a larger thesis with a compact runtime contract, and the main worksheet pairs a narrower complaint intake with a wider validated-plan area. The intake/plan split is approximately 35/65 and is divided by a strong rule rather than card spacing.

Spacing follows a restrained rhythm from compact metadata gaps through 1rem control padding, 2rem section separation, and larger 3–7rem editorial breathing room. Evidence and guardrails remain visually adjacent to the mechanism they justify.

At 900px and below, the preamble and evidence become single-column, the stage rail becomes two-by-two, and complaint intake stacks above the plan. At 560px and below, the preamble compresses, runtime facts become a three-column strip, and all four stages return to one compact horizontal rail with descriptions hidden. The complaint-to-plan sequence remains intact; nothing essential is replaced by a mobile-only pattern.

**The Mechanism-Preservation Rule.** Responsive changes may compact or stack the worksheet, but complaint intake must still lead directly into the validated plan and its evidence.

## Elevation & Depth

GuideRail is flat by default. Depth comes primarily from paper tone, structural rules, and nested tonal surfaces. Only the stage rail and main worksheet receive the shared ambient sheet shadow (`0 12px 32px rgba(37, 31, 21, .09)`); the primary action carries a smaller cobalt-tinted action shadow that tightens on press.

### Shadow Vocabulary

- **Worksheet Lift** (`0 12px 32px rgba(37, 31, 21, .09)`): Used only for the stage rail and complaint-to-plan workspace.
- **Action Lift** (`0 5px 16px rgba(18, 70, 216, .25)`): Gives the primary action a tactile but restrained affordance.
- **Action Hover** (`0 7px 20px rgba(18, 70, 216, .32)`): Appears only while the primary action is hovered.

### Named Rules

**The Structural-Depth Rule.** Prefer tone and rules to shadow; shadow is reserved for the worksheet and the main action.

## Shapes

The system is predominantly rectilinear, like a ruled diagnostic form. Major surfaces and process cells have square corners. Text fields and code panes use gently rounded corners (`field`, 8px), the primary action uses a slightly firmer action radius (`action`, 9px), and the global surface radius (`surface`, 14px) is available only where a genuinely contained surface requires it. Pills are limited to example prompts; circles are limited to status dots and the empty-state mark.

**The Worksheet-Edge Rule.** Do not turn the main stage rail, workspace, result rows, or evidence rows into floating rounded cards.

## Components

Components should feel inspectable and mechanically honest: visible borders, direct labels, explicit state, and motion that communicates cause rather than decoration.

### Buttons

- **Shape:** The primary action has a modest action radius (`action`) and fills the intake width; example controls are compact pills (`pill`).
- **Primary:** Action Cobalt with white text, a 54px minimum height, 1.1rem horizontal padding, and a directional arrow.
- **Hover / Focus:** Hover deepens to Deep Action Cobalt and increases its tinted lift; active presses down by 2px. Every control receives the high-contrast orange focus outline. Reduced-motion mode collapses transitions to effectively zero.
- **Secondary / Ghost:** Text actions remain transparent and underlined. Example pills use neutral borders and adopt cobalt only on hover.

### Chips

- **Style:** Example complaints are transparent, neutral-outlined pills with muted text and a 44px minimum target.
- **State:** Hover changes only the border and text to the action family; chips do not use filled selection color.

### Cards / Containers

- **Corner Style:** The stage rail and main workspace remain square.
- **Background:** Worksheet Sheet over Pale Repair Paper.
- **Shadow Strategy:** Only the shared Worksheet Lift described above.
- **Border:** One-pixel dark structural perimeter with lighter internal rules.
- **Internal Padding:** Fluid 1.4–2.5rem panel padding, compressed to 1.15rem on narrow screens.

### Inputs / Fields

- **Style:** White field, one-pixel dark rule, Field radius, 1rem padding, and a cobalt caret.
- **Focus:** Border shifts to Action Cobalt while the global orange focus ring remains visible.
- **Error / Disabled:** Errors use Error Red copy; disabled controls reduce opacity while retaining their shape and label.

### Navigation

- **Style:** A sticky paper-toned bar with an editorial wordmark and quiet sans links. Links underline on hover; on the narrowest layout only the primary Console destination remains visible.

### Stage Rail

The Enrich, Retrieve, Resolve, and Validate rail is the signature component. It uses numbered square cells, subtle tonal state changes, and cobalt numerals for active or completed progress. Wide screens show the full four-column rail; medium screens use two-by-two; narrow screens preserve all four stages in one compact row and hide only the descriptions.

### Validated Plan

The result summary, ordered action list, verified deeplink, execution trace, and raw JSON form one disclosure ladder. The readable plan comes first, evidence remains expandable but present, and raw output is visually isolated in the dark code surface.

## Do's and Don'ts

### Do:

- **Do** keep the complaint intake and validated plan visibly connected as one worksheet.
- **Do** expose stage progress, source-grounded evidence, action order, deeplink status, cache path, and latency.
- **Do** use cobalt only where the user can act or where processing state advances.
- **Do** keep guardrails and synthetic-data disclosure visible, calm, and unambiguous.
- **Do** preserve keyboard focus, 44px touch targets, high contrast, and reduced-motion behavior.

### Don't:

- **Don't** use Verified Green for general success, healthy service state, or completed process stages.
- **Don't** introduce gradients, glass effects, ornamental illustration, or a field of rounded cards.
- **Don't** hide evidence or guardrails to make the interface appear simpler.
- **Don't** imitate proprietary Samsung screens or use visual language that implies endorsement.
- **Don't** let responsive layouts separate the complaint from the resulting plan or remove the four-stage process.
