---
version: "alpha"
name: "BoneScope Research Studio"
description: "Local multi-topic educational chatbot with sourced bone-document lookup. Private Stitch UI design workspace."
colors:
  primary: "#0284C7"
  on-primary: "#FFFFFF"
  primary-container: "#E0F2FE"
  on-primary-container: "#0C4A6E"
  secondary: "#64748B"
  accent-teal: "#0D9488"
  surface: "#F6F8FB"
  surface-container-low: "#EEF2F7"
  surface-container: "#E2E8F0"
  surface-high: "#CBD5E1"
  surface-white: "#FFFFFF"
  on-surface: "#0F172A"
  on-surface-variant: "#334155"
  outline: "#64748B"
  outline-variant: "#CBD5E1"
  error: "#DC2626"
  error-container: "#FEF2F2"
  success: "#10B981"
  dark-primary: "#38BDF8"
  dark-accent-teal: "#2DD4BF"
  dark-on-primary: "#06131F"
  dark-primary-container: "#153047"
  dark-on-primary-container: "#E0F2FE"
  dark-secondary: "#94A3B8"
  dark-surface: "#0B0E14"
  dark-surface-container-low: "#080B10"
  dark-surface-container: "#151B26"
  dark-surface-high: "#1E2636"
  dark-on-surface: "#F1F5F9"
  dark-on-surface-variant: "#CBD5E1"
  dark-error: "#F87171"
  dark-error-container: "#7F1D1D"
  dark-success: "#34D399"
  dark-hero-gradient: "linear-gradient(145deg, #0D1829 0%, #0F253A 52%, #0C353D 100%)"
  dark-brand-gradient: "linear-gradient(135deg, #38BDF8 0%, #2DD4BF 100%)"
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
    textColor: "{colors.dark-on-surface-variant}"
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

BoneScope Research Studio is a polished, source-forward educational chat workspace. The current design uses an obsidian canvas, cool charcoal panels, cyan-to-teal accents, fine grid texture, subtle ambient light and a radiographic line-art motif. The welcome view centers a conversational headline above an asymmetric bento grid; the conversation view prioritizes readable messages, citations and the anchored composer. The image workflow presents model classification as an educational experiment and does not interpret the X-ray as a diagnosis. The classifier and retrieval run locally; text prompts, recent chat context, retrieved passages and (for an open case) Top-3 labels/scores may be sent to the configured external language-model provider.

## Colors

The light palette uses a cool near-white canvas (#F6F8FB), blue-gray sidebar (#EEF2F7), bright cards and blue/teal accents. The dark palette uses obsidian (#0B0E14), a deeper sidebar (#080B10), raised charcoal cards (#151B26), cyan (#38BDF8) and teal (#2DD4BF). Reserve green for local processing status, red for errors, and retain readable focus indicators in both themes. Keep the X-ray feature card on its deep blue-green gradient in both themes.

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

The application adapts the desktop/mobile composition using the system font stack and inline SVG instead of external font/icon dependencies. The design file describes implementation intent; it is not a runtime dependency or a clinical performance claim.

The welcome state uses a two-line headline, compact studio label, feature card for image analysis, paired topic cards and example prompt chips. Saved conversations are stored in the local SQLite database and can be reopened or deleted; the history stores text and source references, not X-ray images by default. Export saves Markdown locally. The help dialog explains source checking and network use by the selected AI provider. Provider labels follow server configuration; the actual answer label follows the provider returned with that answer. UI cancellation stops waiting in the browser; it does not promise cancellation of server work.

Answer typography is 14px with 1.85 line height. Safe rendering supports paragraphs, headings, lists, bold text, inline code and source references without interpreting model text as HTML. Source excerpts remain plain text. The educational draft label stays visible and `answer_ready=false` remains a backend requirement.

## Conversational update · 2026-10-31

The user selected multi-topic conversation with document lookup for bone questions. The composer now includes an Auto conversation/document mode selector and a strict document-only mode. General replies are labeled as model knowledge and have no fabricated source cards. Document replies retain their citations and provenance. Recent conversation context stays in tab memory and is cleared by New conversation. Updated previews and implementation details are linked from docs/guides/CHATBOT_CONVERSATION_VI.md.

## Current Research Studio · 2026-11-13

Use the slate and teal BoneScope mark from [bonescope.svg](bonescope.svg) for navigation and favicons. The mark combines a bone silhouette with four imaging frame corners. Both the Research Studio and X-ray Workbench use the same asset.

The welcome screen places two actions below a short introduction. One opens the X-ray workflow and the other starts a local source lookup. The sidebar holds new chat, workspace navigation, saved conversations and help. Export and theme controls live in the top bar.

Keep transitions brief and honor reduced motion. Stack the two welcome actions on narrow screens. The composer exposes three modes and disables image attachment during local lookup. An existing image stays in the current browser tab while local lookup is selected. The source list uses the same disclosure controls for local lookup and generated answers.

Make data handling legible: image and 22 metadata fields are processed by the local classifier; the selected external language-model provider receives user text/context, retrieved source excerpts, and only Top-3 labels/scores plus a mapping note for an active image case. Saved chat history stores text and source references in local SQLite; images are not persisted there by default. Keep the educational-use and non-diagnostic notice visible. Never imply that the entire assistant or all conversation data is local, and do not introduce fabricated source counts or clinical claims.

## Pro Obsidian & Bioluminescent Cyan Refinement · 2026-11-06

`graphite.css` serves as the active Pro Obsidian & Bioluminescent Cyan styling layer (`#05070B` deep obsidian canvas, `#00E5FF` cyan accents, `#14F195` emerald status highlights, and `#F8FAF8`/`#CBD5E1` high-contrast typography) with complete light-mode (`html[data-theme="light"]`) and `prefers-reduced-motion` parity:

- **Composer Multimodal Image Attachment:** Supports `#attach-image`, `.image-attachment` preview card with thumbnail/status/remove button, Clipboard Paste (`Ctrl+V`) and Drag-and-Drop image attachment directly onto `#question-form.composer` with `.composer.is-dragging` visual feedback.
- **Step 1 BTXRD Reference & Sample Chips:** Provides `#case-reference-id` / `#case-reference-load` lookup (`GET /api/reference-images/{image_id}`), exact SHA-256 auto-fill status banner (`#case-image-match-note`), `#ask-ai-about-case-image` fallback button for non-BTXRD images, and 6 one-click BTXRD sample case chips (`.btxrd-sample-chips` / `.btxrd-sample-chip`) covering representative tumor and non-tumor classes (`IMG000002`, `IMG000240`, `IMG000234`, `IMG000236`, `IMG000001`, `IMG001868`).
