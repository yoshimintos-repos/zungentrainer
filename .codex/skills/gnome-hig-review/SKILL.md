---
name: gnome-hig-review
description: Review GTK 4 / Libadwaita apps against the GNOME Human Interface Guidelines. Use this skill whenever reviewing UI code for a GNOME app, checking HIG compliance, building or modifying GTK4/Libadwaita interfaces, or when the user asks about GNOME design guidelines, UI best practices, or whether their app "looks right" / "follows GNOME standards". Also use when the user mentions AdwViewSwitcher, AdwHeaderBar, AdwPreferencesDialog, or any Libadwaita widget in a review context.
---

# GNOME HIG Review

Review a GTK 4 / Libadwaita app against the complete GNOME Human Interface Guidelines. This produces a structured compliance report with specific issues, locations, and fixes.

## Process

### 1. Gather Context

Read the app's source files in this order:
1. **Design spec** (if exists) — check `docs/` for spec files
2. **Window/Application class** — the central mediator, shows overall structure
3. **UI pages/views** — each page file, looking at widget usage, layout, navigation
4. **Any .ui/.blp files** — Blueprint or XML UI definitions
5. **CSS files** — custom styling

If the codebase is large, focus on UI-facing code. Skip pure backend/service logic unless it affects user-facing behavior.

### 2. Run the Checklist

Work through each category below. For every violation found, record:
- **Category** and **rule** being violated
- **File and line** where the violation occurs
- **What's wrong** (concrete, specific)
- **How to fix it** (actionable, with code if possible)
- **Severity**: Critical (breaks HIG fundamentally), Major (clearly non-compliant), Minor (polish/refinement)

Read `references/hig-checklist.md` for the detailed checklist with all rules per category.

### 3. Produce the Report

Structure the report as follows:

```
## HIG Compliance Report: [App Name]

### Zusammenfassung
- X Kritisch / Y Major / Z Minor
- Staerkste Bereiche: ...
- Groesster Handlungsbedarf: ...

### Kritische Issues
[issues with file:line, problem, fix]

### Major Issues
[issues with file:line, problem, fix]

### Minor Issues
[issues with file:line, problem, fix]

### Positiv (HIG-konform)
[list what's already done well — reinforces good patterns]
```

Write the report in German (matching the app's UI language). Technical terms (widget names, CSS classes, etc.) stay in English.

## Condensed Checklist (Quick Reference)

These are the most commonly violated rules. The full checklist is in `references/hig-checklist.md`.

### Design Principles
- App does ONE thing well — no feature overload
- Progressive disclosure — simple first, advanced behind navigation
- Automatic where possible — minimize manual steps
- Undo over confirmation dialogs

### Navigation
- ViewSwitcher: 3-5 views, nouns with Header Capitalization, consistent label lengths
- Views must not have cross-dependencies (controls in one view affecting another)
- ViewSwitcher must switch to bottom bar at narrow widths (AdwViewSwitcherBar)
- Prefer in-window navigation over secondary windows
- Max 1 level of hierarchy depth

### Header Bars
- Few controls — keep it scannable, leave drag space
- ALL controls need tooltips
- No text-only buttons (always include an icon)
- No `.suggested-action` / `.destructive-action` styles in primary header bars
- No linked button groups — use `.spacer` for grouping instead
- Update header bar controls when view/mode changes

### Buttons
- Max ONE `.suggested-action` or `.destructive-action` button per view
- Labels: imperative verbs, Header Capitalization, short
- No double-click or right-click exclusive actions
- Invalid buttons must be insensitive (greyed out), not error-after-click
- Use `.pill` style for primary view actions in open space

### Boxed Lists & Preferences
- Use `AdwPreferencesDialog` (NOT deprecated `AdwPreferencesWindow`)
- `.boxed-list` style for settings lists
- Max 1-2 controls per row
- Semantic grouping with `AdwPreferencesGroup` (title + description for search)
- Go-next arrow for rows that navigate to sub-views
- Drag handles at row START for reorderable lists

### Toasts vs Banners
- `AdwToast`: transient events, reactions to user actions, undo buttons
- `AdwBanner`: persistent states, ongoing conditions
- Toast titles: informal heading style
- Never use toasts for persistent state or when app is inactive

### Dialogs
- `AdwAlertDialog` for confirmations and errors
- Undo is BETTER than confirmation dialogs
- Affirmative button: specific verb ("Speichern", "Loeschen"), NOT generic ("OK", "Fertig")
- Cancel button first (left in LTR), affirmative last
- Enter → affirmative (EXCEPT for irreversible/destructive actions)
- Escape → cancel
- Never show dialogs unexpectedly — only as response to user action
- Avoid error dialogs where possible (use toasts for non-critical errors)

### Writing Style
- Header Capitalization for: headings, button labels, menu items, tab titles, tooltips
- Sentence capitalization for: checkbox/radio/slider labels, body text, field labels
- No trailing periods (.) in labels, headings, descriptions
- Ellipsis (Unicode U+2026) when action needs further input ("Speichern unter...")
- Neutral tone — no "you"/"my", use "your" if ownership needed
- No Latin abbreviations (i.e., e.g.) — use full words
- Domain-specific terminology over system jargon

### Typography
- NEVER use italic/oblique
- NEVER use ALL CAPS
- NEVER hard-code font sizes — use CSS classes (`body`, `heading`, `caption`, `title-1` to `title-4`)
- Use standard Unicode: curly quotes, proper ellipsis, en-dash for ranges, narrow no-break space for units
- Lighter/smaller for secondary info, heavier/darker for emphasis

### Icons
- Symbolic icons only for UI (16x16 SVG, monochrome)
- Full-color icons only for app identity and large decorative use
- If users won't recognize an icon, use a text label instead
- Some icons only work in pairs/sets (stop, remove)
- Unique app icon required — never reuse existing icons
- App icon: 128x128 canvas, simple geometric, not flat (subtle depth), standard color palette

### Accessibility
- ALL elements need accessible names (for screen readers)
- Must work with: high-contrast mode, large text, keyboard-only, screen reader, on-screen keyboard
- No color as sole differentiator
- No flashing/blinking elements
- Click targets large enough for varied abilities
- Hover must not be sole way to reveal actions

### Adaptive Design
- Minimum desktop: 1024x600px
- Minimum phone (if applicable): 360x294px
- Use `AdwBreakpoint` for layout switches
- Content in max-width containers (prevent long text lines on wide screens)
- Smooth resizing — no jumping widgets
- Design from smallest size up

### Keyboard
- Full keyboard navigation required (test with keyboard only!)
- Standard shortcuts for standard functions (Ctrl+S, Ctrl+Z, etc.)
- Tab order must be logical
- Ctrl+letter for custom shortcuts (mnemonic where possible)
- No Alt shortcuts (conflicts with access keys), no Super (system reserved)
- Access keys (mnemonics) for all labelled controls where possible

### UI Styling
- Support light + dark styles (AdwStyleManager)
- Follow system style preference
- Test with high-contrast mode
- Minimal custom CSS — use Libadwaita style classes and color variables
- Custom styling must work with light, dark, AND high-contrast

### Pointer & Touch
- Large click targets
- No hover-only actions
- No double-click or chord requirements for essential actions
- Esc cancels in-progress pointer operations
- Don't use 3/4 finger gestures (system reserved)
- All pointer actions must also be possible via keyboard
