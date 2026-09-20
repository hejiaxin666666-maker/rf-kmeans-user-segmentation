---
version: alpha
name: "淘宝用户分群运营观测站"
description: "A focused Chinese analytics console that turns purchase behavior into actionable RF user segments."
colors:
  primary: "#17324D"
  signal: "#1BB59A"
  risk: "#E58C4A"
  background: "#F4F1EA"
  surface: "#FFFDF8"
  ink: "#17212B"
  muted: "#6D7882"
  border: "#D7D9D5"
  success: "#198754"
  danger: "#B94A48"
typography:
  sans:
    fontFamily: "Inter, 'Microsoft YaHei', 'Noto Sans CJK SC', system-ui, sans-serif"
  mono:
    fontFamily: "'IBM Plex Mono', 'Cascadia Mono', Consolas, monospace"
rounded:
  DEFAULT: "0.65rem"
  sm: "0.4rem"
  md: "0.65rem"
  lg: "0.95rem"
spacing:
  section-gap: "1.5rem"
  page-max: "88rem"
components:
  button:
    radius: "0.55rem"
    height: "2.55rem"
  card:
    radius: "0.8rem"
    border: "1px solid #D7D9D5"
  table:
    radius: "0.65rem"
---

# 淘宝用户分群运营观测站 Design System

## Overview

### Creative North Star

The interface is an operations observation station: part clean measurement board, part campaign briefing. It should feel like a calm control room for making a next marketing decision, not a generic BI template.

### Product context and register

- **Audience and primary job:** Data analysts, operations candidates, and interviewers need to inspect user segments and explain the next action quickly.
- **Target market(s) and evidence:** Mainland Chinese learning/demo context, based on the Chinese project brief and Taobao behavior vocabulary.
- **Locale(s) and language policy:** Simplified Chinese UI; English appears only in technical filenames or metric abbreviations such as RF, SSE, and K-Means.
- **Usage scene:** Laptop-first presentation and portfolio review, with a readable narrow layout for quick mobile inspection.
- **Register:** Product dashboard with a small amount of editorial personality.
- **Memorable signature:** A slim teal “signal rail” on the left edge of the main analysis surface marks the current data run and keeps the dashboard visually tied to operational action.
- **Restraint:** Charts, tables, and filters remain quiet and legible; no decorative illustrations, gradients, or animation compete with the data.
- **Anti-references:** Avoid generic purple SaaS dashboards, glassmorphism, neon cyberpunk, and card grids with no analytical hierarchy.
- **Token ownership/runtime mapping:** This file is the visual source of truth. `app.py` mirrors its values in one scoped CSS token block.

## Colors

Deep indigo anchors the sidebar and headings. Warm off-white keeps the analysis surface closer to paper than a cold admin panel. Teal-green is reserved for active runs, healthy states, and the primary data series. Orange marks recency risk and reactivation opportunities. Red is reserved for errors, not ordinary dormant users. Charts use the semantic palette plus restrained secondary hues and always include text labels.

## Typography

The system sans stack keeps Chinese glyph coverage dependable while allowing Inter to shape Latin metric labels. Body copy is compact but not cramped; metric numbers use the mono stack with tabular numerals so columns align. Sentence case and plain Chinese verbs are preferred for controls.

## Layout

The wide layout reserves a compact control rail on the left and a document-scrolling analysis surface on the right. Sections are separated by generous vertical rhythm rather than heavy boxes. Metrics form a responsive grid; long tables scroll within their own surface. The page never hides document overflow to force a viewport fit.

## Elevation & Depth

Hierarchy comes from tonal layers and one-pixel borders first. Cards use a very soft shadow only when they need separation from the warm background. The sidebar is a solid indigo plane; charts and tables sit on the warm-white surface.

## Shapes

Controls and cards use moderate rounded corners. Pills are reserved for status labels and never used for every button. Dividers remain hairline and neutral. Focus rings use the signal color with a visible offset.

## Components

### Foundational visual states

Hover slightly raises contrast; focus-visible uses a two-pixel teal outline; disabled controls reduce contrast but remain readable; busy controls preserve their dimensions; success, warning, info, and error states include both iconography or text and color.

### Buttons and actions

The primary action is teal on a light surface or warm white on indigo in the sidebar. Secondary actions are outlined. Download actions are quiet and explicit. No destructive action is needed in this product.

### Navigation and data display

The sidebar is the control surface. Section labels are short and action-oriented. Tables prioritize readable labels and aligned numerics. Charts use a consistent business-label color map and provide captions for sampled displays.

### Forms and overlays

Use Streamlit's native uploader, select controls, checkbox, slider, and buttons. Validation is inline; no browser dialog is used. Upload states explain accepted CSV shape and recovery steps.

### Iconography

Use small text or Unicode-safe symbols sparingly; labels remain present even when an icon is used. Do not rely on icon-only controls.

### Motion

Motion is limited to Streamlit's native progress/spinner behavior and subtle hover/focus transitions. Reduced-motion users receive the same information without animation.

### Content and data visualization

Copy names the user's task: “运行分析”, “下载结果”, “筛选分群”. R is always explained as days since the last purchase; F is always explained as purchase-record count. Chart legends use the business labels when K=4 and generic group names otherwise.

## Do's and Don'ts

- **Do:** Keep the next operational decision visible near the corresponding segment metrics.
- **Do:** Explain data boundaries beside the result, not hidden only in the README.
- **Don't:** Use cluster IDs as if they were stable business labels.
- **Don't:** Use large decorative cards, gradients, or red color to imply business value without evidence.
