---
version: "alpha"
name: "BoneScope Research Studio"
description: "Local multi-topic educational chatbot with sourced bone-document lookup. Private Stitch UI design workspace."
colors:
  primary: "#245D75"
  on-primary: "#FFFFFF"
  primary-container: "#D1E9F4"
  on-primary-container: "#123B50"
  secondary: "#52616A"
  surface: "#F7F8FC"
  surface-container-low: "#F0F2F7"
  surface-container: "#EAEDF3"
  surface-high: "#E3E7EF"
  surface-white: "#FFFFFF"
  on-surface: "#191C20"
  on-surface-variant: "#454B54"
  outline: "#747B85"
  outline-variant: "#C5CBD4"
  error: "#BA1A1A"
  error-container: "#FFDAD6"
  success: "#28734E"
  dark-primary: "#A6CEE2"
  dark-on-primary: "#073548"
  dark-primary-container: "#214D61"
  dark-on-primary-container: "#D1E9F4"
  dark-secondary: "#B7C8D1"
  dark-surface: "#111418"
  dark-surface-container-low: "#191D22"
  dark-surface-container: "#20252B"
  dark-surface-high: "#292F36"
  dark-on-surface: "#E1E2E8"
  dark-on-surface-variant: "#C2C7D0"
  dark-outline: "#8C929B"
  dark-outline-variant: "#9099A4"
  dark-error: "#FFB4AB"
  dark-error-container: "#7D2923"
  dark-success: "#87D6A8"
typography:
  display:
    fontFamily: "Segoe UI Variable Display, Segoe UI, Arial, sans-serif"
    fontSize: "2.5rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.045em"
  heading:
    fontFamily: "Segoe UI Variable Display, Segoe UI, Arial, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 700
    lineHeight: 1.4
  body:
    fontFamily: "Segoe UI Variable, Segoe UI, Arial, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: "Segoe UI Variable, Segoe UI, Arial, sans-serif"
    fontSize: "0.625rem"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.12em"
rounded:
  compact: "0.75rem"
  control: "0.9375rem"
  card: "0.8125rem"
  panel: "1.625rem"
  pill: "999px"
spacing:
  xxs: "0.25rem"
  xs: "0.5rem"
  sm: "0.75rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2rem"
components:
  primary-button:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.control}"
    height: "2.25rem"
    padding: "0.8125rem"
  chat-panel:
    backgroundColor: "{colors.surface-white}"
    rounded: "{rounded.panel}"
    padding: "1.25rem"
  composer:
    backgroundColor: "{colors.surface-white}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.card}"
    padding: "0.875rem"
  suggestion-card:
    backgroundColor: "{colors.surface-white}"
    textColor: "{colors.on-surface-variant}"
    rounded: "{rounded.card}"
    height: "3.375rem"
    padding: "0.75rem"
  neutral-hover-control:
    backgroundColor: "{colors.surface-high}"
    textColor: "{colors.on-surface-variant}"
    rounded: "{rounded.compact}"
  local-status:
    backgroundColor: "{colors.success}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.pill}"
  dark-primary-action:
    backgroundColor: "{colors.dark-primary}"
    textColor: "{colors.dark-on-primary}"
    rounded: "{rounded.control}"
  dark-selected-content:
    backgroundColor: "{colors.dark-primary-container}"
    textColor: "{colors.dark-on-primary-container}"
    rounded: "{rounded.card}"
  dark-sidebar:
    backgroundColor: "{colors.dark-surface-container-low}"
    textColor: "{colors.dark-secondary}"
  dark-conversation:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-on-surface}"
  dark-chat-card:
    backgroundColor: "{colors.dark-surface-container}"
    textColor: "{colors.dark-on-surface}"
  dark-hover-control:
    backgroundColor: "{colors.dark-surface-high}"
    textColor: "{colors.dark-on-surface-variant}"
  dark-outlined-surface:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-outline-variant}"
  dark-error-message:
    backgroundColor: "{colors.dark-error-container}"
    textColor: "{colors.dark-error}"
    rounded: "{rounded.card}"
  dark-local-status:
    backgroundColor: "{colors.dark-success}"
    textColor: "{colors.dark-surface}"
    rounded: "{rounded.pill}"
---

## Overview

BoneScope Research Studio is a calm, source-forward educational workspace for exploring a local document collection. Its visual language feels clear, measured, and approachable: a cool blue-green accent anchors the interface while pale blue-gray surfaces keep long reading sessions quiet. The visual hierarchy prioritizes the question, the AI draft label, and source passages. This is a local learning demo; the interface does not present clinical advice or image interpretation.

## Colors

The light palette uses a muted deep teal-blue for primary actions, a pale blue container for selected and user-authored content, and cool neutral surfaces for reading areas. Text uses dark ink and slate roles; outlines remain visible around interactive cards and fields. Error red marks failed requests. Green is reserved for local-session indicators. The dark palette keeps the same hierarchy with charcoal surfaces and pale blue primary actions. Always pair each surface with its corresponding readable foreground token.

## Typography

Use the local system sans-serif stack (`Segoe UI Variable`, `Segoe UI`, Arial) so the local demo does not depend on an external font request. Display headings are bold, compact, and slightly tightened. Body copy stays regular with generous line height for Vietnamese text and source excerpts. Small uppercase labels use medium-bold weight and expanded tracking; keep them secondary to sentence case content.

## Layout

On wide screens, use a persistent 256px navigation sidebar beside a centered conversation workspace with a maximum width of 1020px. The top bar identifies the workspace and provides export and theme controls. Keep the message history scrollable while the composer stays anchored below it. Let the conversation sit directly on the quiet page surface instead of framing the entire workspace in another card. Below 760px, use a hidden sidebar drawer opened by the menu button, stack suggested prompts, and preserve a full-width composer. Mobile action controls have 44px touch targets. Use a 4px spacing base, grouping most content with 12px, 16px, 24px, and 32px gaps.

## Elevation & Depth

Prefer outlined surfaces and a single soft panel shadow over stacked elevation. Keep the sidebar, conversation card, and composer distinct with subtle surface changes and thin outline tokens. Hover and focus states add restrained contrast; motion is brief and should respect reduced-motion preferences.

## Shapes

Use softly rounded geometry throughout: compact icon controls around 12px, cards and suggestion rows around 15–20px, and the main conversation panel around 26px. Avatar and brand marks use rounded squares. Avoid sharp corners and ornamental shapes that compete with source readability.

## Components

- **Primary action:** A filled teal-blue button with white text, a compact arrow icon, and a 12px corner radius. Disabled state lowers contrast and prevents duplicate submission.
- **New conversation and theme controls:** Outlined surface buttons with clear accessible names and visible keyboard focus.
- **Suggestion cards:** Full-width outlined cards on mobile and paired cards on desktop; present them as optional example prompts.
- **Messages:** Right-align user messages in a pale blue container. Keep assistant replies on the neutral surface and identify generated content as an unverified draft.
- **Source cards:** Disclosure rows numbered `[S1]`, `[S2]` and so on. Inline citation buttons open the matching source and move keyboard focus to it. Expand to show source excerpt, section, and an HTTPS link when present; place license, identifiers and hashes in a secondary disclosure.
- **Composer:** Multiline text field with character count, Enter/Shift+Enter guidance, submit state, and a persistent educational-use notice.
- **Status and errors:** Use an announced loading state, clear timeout or request errors, and a retry action. A new conversation must not receive stale output from an earlier request.

## Do's and Don'ts

- Keep source attribution and the educational scope visible in both themes.
- Keep the conversation usable with keyboard focus, screen readers, reduced motion, and narrow viewports.
- Preserve whitespace around source passages and avoid decorative elements inside evidence text.
- Do not style a generated draft as a verified answer or imply a clinical recommendation.
- Do not add external fonts or remote assets to the local-only interface.

## Implemented application · 2026-10-31

Private Stitch project: `7327687804675427525`. Screen IDs and design-system asset are recorded in `.stitch/metadata.json`. The local application adapts the generated desktop/mobile composition using the system font stack and inline SVG instead of external font/icon dependencies. Preview images show the actual local frontend, not the generated mockup.

The welcome state uses a two-line 40px headline, an understated sparkle mark, paired topic cards and a three-step reading hint. The sidebar lists questions from the current tab; there is no persistent conversation database. Export saves Markdown locally. The help dialog explains source checking and network use by the selected AI provider. Groq and OpenAI labels follow server configuration; the actual answer label follows the provider returned with that answer. UI cancellation stops waiting in the browser; it does not promise cancellation of server work.

Answer typography is 14px with 1.85 line height. Safe rendering supports paragraphs, headings, lists, bold text, inline code and source references without interpreting model text as HTML. Source excerpts remain plain text. The educational draft label stays visible and `answer_ready=false` remains a backend requirement.

## Conversational update · 2026-10-31

The user selected multi-topic conversation with document lookup for bone questions. The composer now includes an Auto conversation/document mode selector and a strict document-only mode. General replies are labeled as model knowledge and have no fabricated source cards. Document replies retain their citations and provenance. Recent conversation context stays in tab memory and is cleared by New conversation. Updated previews and implementation details are linked from docs/guides/CHATBOT_CONVERSATION_VI.md.
