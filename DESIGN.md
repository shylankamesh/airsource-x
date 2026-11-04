---
name: AirSource X
description: Evidence-first presentation for a retrospective Delhi air-quality study
colors:
  deep-space: "#050912"
  raised-surface: "#0a1120"
  panel: "#0b1423"
  foreground: "#f1f5f9"
  secondary-copy: "#a5b3c6"
  mint-signal: "#6af0b7"
  atmospheric-blue: "#8ab6ff"
  uncertainty-amber: "#f1b976"
  hairline: "rgba(153,177,211,.16)"
---

# Design System: AirSource X

## Overview

**Creative North Star: “The Orbital Evidence Desk.”**

The page uses the supplied Ascend reference's deep-space atmosphere and mint signal color, adapted for a research prototype. Dark navy provides a quiet field for one real result panel and an interactive comparison; mint identifies the project and primary actions, while amber marks uncertainty. The page keeps the original AirSource X identity and copy grounded in its Delhi experiment.

Its visual emphasis comes from typography, measured data, thin structural lines, and restrained orbital geometry. The background motif is conceptual decoration and is explicitly labeled. There are no pretend customer marks, simulated live signals, or made-up charts. The interface keeps the experiment's scope and caveats visible as part of its proof.

**Key Characteristics:**
- A spacious two-column hero pairs the study statement with actual held-out metrics.
- A dark, restrained atmosphere surrounds high-contrast evidence panels.
- Mint, blue, and amber have distinct data roles.
- Hairlines and open space carry structure instead of nested card grids.
- Responsive layouts stack content while preserving the primary action and result labels.

## Colors

Near-black navy grounds the page; cool pale text and a restrained mint accent make measurements and actions easy to find.

### Primary
- **Mint signal** (#6AF0B7): Main brand accent, primary CTA, selected tabs, and model result emphasis.
- **Atmospheric blue** (#8AB6FF): Supporting data distinction and low-emphasis structure.
- **Uncertainty amber** (#F1B976): Warnings and uncertainty states.

### Neutral
- **Deep space** (#050912): Page background.
- **Raised surface** (#0A1120): Section backgrounds.
- **Panel** (#0B1423): Result and data surfaces.
- **Foreground** (#F1F5F9): Headings and primary copy.
- **Secondary copy** (#A5B3C6): Explanatory text and supporting labels.
- **Hairline** (rgba(153,177,211,.16)): Dividers and panel boundaries.

### Named Rules
**The Evidence-First Rule.** Every visible result panel shows its study horizon and retrospective scope; atmospheric art never appears to be a pollution map.

## Typography

**Display Font:** Inter (with system sans-serif fallback; selected to match the supplied reference)
**Body Font:** Inter (with system sans-serif fallback)
**Label/Mono Font:** DM Mono (with ui-monospace fallback)

**Character:** Compact, direct headings are paired with readable explanatory copy. Monospaced labels are reserved for units, short data markers, and study metadata.

### Hierarchy
- **Display** (700, clamp(44px, 5vw, 68px), 1.07): Hero statement.
- **Headline** (600, clamp(38px, 4.2vw, 54px), 1.08): Section headings.
- **Title** (600, 20–21px, 1.2): Data-panel and method titles.
- **Body** (400, 11–15px, 1.7–1.85): Evidence notes and explanatory copy; the hero lead uses 15px.
- **Label** (500, 11px, tracked, uppercase where useful): Short study metadata and control labels.

## Layout

The main content is capped at 1180px with 32px desktop gutters and 18px mobile gutters. The first screen uses a two-column hero: argument and actions on the left, a measured result snapshot on the right. At 950px and below the hero and method/provenance layouts become single-column; the evidence comparison and study-strip data remain readable at phone widths. Sections use generous vertical spacing and thin dividers.

## Elevation & Depth

The system uses tonal layering, one-pixel hairlines, and neutral black shadows for depth. A subtle radial orbital outline is confined to the result panel; it does not encode observations. No colored blur or glow is used as a substitute for elevation.

## Shapes

Panels use 12–17px corners; primary controls use a compact 7px radius. Hairline borders define surfaces and separators. Orbit lines are partial, low-contrast geometry; they never represent geography or measured data.

## Components

### Buttons
- **Shape:** Compact, 7px corners.
- **Primary:** Mint fill with dark ink, 14px by 18px padding.
- **Hover / Focus:** Small upward hover shift; mint outline with offset on keyboard focus.
- **Secondary:** Underlined text link with mint hover color.

### Data Panels
- **Result snapshot:** Dark raised surface with real held-out metrics, unit labels, horizon names, and sample count.
- **Forecast comparison:** Interactive tab selector with a bar chart, explicit units, baseline legend, and a plain-language winner note.
- **Limit notice:** Amber border and copy for under-covered intervals.

### Navigation
- Sticky dark top bar with the AirSource X mark, three in-page anchors, and repository link. At narrow widths, keep the brand and repository action visible and hide the center link row.

## Motion

Native scrolling is smooth unless reduced motion is requested. Forecast-tab bars transition between data states; all result text updates immediately. Hover movement stays small and never carries information on its own.
