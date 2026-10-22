---
name: Liquid Crystal Glass
colors:
  surface: '#0c1511'
  surface-dim: '#0c1511'
  surface-bright: '#323b36'
  surface-container-lowest: '#07100c'
  surface-container-low: '#141d19'
  surface-container: '#18221d'
  surface-container-high: '#232c27'
  surface-container-highest: '#2d3732'
  on-surface: '#dbe5de'
  on-surface-variant: '#b9ccb5'
  inverse-surface: '#dbe5de'
  inverse-on-surface: '#29322e'
  outline: '#849581'
  outline-variant: '#3b4b3a'
  surface-tint: '#00e55b'
  primary: '#edffe8'
  on-primary: '#003911'
  primary-container: '#00ff66'
  on-primary-container: '#007128'
  inverse-primary: '#006e27'
  secondary: '#afceb8'
  on-secondary: '#1b3627'
  secondary-container: '#314d3c'
  on-secondary-container: '#9ebca7'
  tertiary: '#edffea'
  on-tertiary: '#003915'
  tertiary-container: '#95f2a2'
  on-tertiary-container: '#047130'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#6bff83'
  primary-fixed-dim: '#00e55b'
  on-primary-fixed: '#002107'
  on-primary-fixed-variant: '#00531b'
  secondary-fixed: '#caead4'
  secondary-fixed-dim: '#afceb8'
  on-secondary-fixed: '#042013'
  on-secondary-fixed-variant: '#314d3c'
  tertiary-fixed: '#9af7a7'
  tertiary-fixed-dim: '#7eda8d'
  on-tertiary-fixed: '#002109'
  on-tertiary-fixed-variant: '#005321'
  background: '#0c1511'
  on-background: '#dbe5de'
  surface-variant: '#2d3732'
typography:
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 40px
    fontWeight: '600'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  margin: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.75rem
  space-xl: 3rem
---

## Brand & Style

This design system channels a futuristic, Apple-inspired Liquid Crystal Glass aesthetic paired with an Emerald Obsidian color theme. It merges deep obsidian charcoal environments with vibrant emerald green glows, translucent mint glass highlights, and crisp white typography.

The target audience consists of forward-thinking developers, tech enthusiasts, and elite professionals who demand uncompromising visual precision and cutting-edge presentation. 

The emotional response to evoke is one of high-tech luxury, immersive depth, and clinical yet captivating focus. By blending sleek glassmorphic refraction with dark-mode technological sophistication, the interface feels both weightless and grounded in advanced computing power.

## Colors

The palette is anchored by a deep obsidian charcoal base (`#09120e`), establishing an infinite dark canvas for luminous accents. The primary accent is a vibrant emerald green (`#00FF66`), driving interactive elements and core focal points with an electric pulse. 

Secondary and tertiary tones leverage deep forest glass tones (`#0A2618`) and glowing mint highlights (`#8CE99A`) to construct layered, translucent surfaces that simulate liquid crystal refractions against the dark background. Typography utilizes high-contrast pure white and soft silver gradients to ensure razor-sharp legibility.

## Typography

Typography balances geometric futuristic headings with ultra-clean, utilitarian body text. Space Grotesk commands attention at larger scales with its engineered proportions and subtle technical flair, while Inter provides immaculate legibility across dense data displays and fluid UI elements. 

Ensure that all large display headings scale down gracefully on mobile viewports to prevent awkward wrapping, maintaining strict proportional hierarchy across all form factors.

## Layout & Spacing

The layout philosophy relies on a fluid 12-column grid system optimized for immersive, edge-to-edge experiences. Content breathes within generous margins, utilizing a deliberate 1.5rem gutter to separate luminous glass panels without crowding.

Spacing follows an 8px modular rhythm, scaling smoothly from tight component internal padding (`space-xs`) to expansive section breaks (`space-xl`). On mobile devices, outer margins collapse to 1rem while maintaining the structural integrity of the underlying grid.

## Elevation & Depth

Depth is achieved through an advanced Glassmorphism execution. Surfaces mimic frosted, semi-transparent liquid crystal planes layered over the deep obsidian background. 

Instead of traditional heavy drop shadows, elevation relies on multi-pass ambient glows: low-opacity emerald backlighting, crisp 1px inner mint borders (`rgba(140, 233, 154, 0.2)`), and heavy backdrop blurs (20px to 40px). This creates a hyper-modern floating effect where interactive layers catch simulated light as the cursor moves across the viewport.

## Shapes

The shape language embraces smooth, continuous curvature inspired by high-end hardware design. Elements utilize a balanced roundedness (Level 2), translating to a default 0.5rem radius for standard containers, 1rem (`rounded-lg`) for prominent cards, and 1.5rem (`rounded-xl`) for modal overlays and major structural panels. 

Pill shapes (`9999px`) are strictly reserved for status badges, interactive chips, and primary action buttons to emphasize touch targets.

## Components

### Buttons
Primary buttons feature a luminous emerald green gradient (`#00FF66` to `#8CE99A`) with a subtle outer glow on hover and a crisp white label. Secondary and ghost buttons utilize translucent glass panels with thin mint borders and text that shifts to pure white on interaction.

### Chips & Badges
Compact pill-shaped containers featuring semi-transparent dark emerald backgrounds, 1px mint outlines, and glowing indicator dots. Ideal for tagging states, system statuses, or categorical filters.

### Lists & Navigation
Structured with generous row padding and subtle bottom dividers using low-opacity mint strokes. Hover states illuminate the entire row with a faint frosted glass wash and an intensifying left-edge emerald accent line.

### Checkboxes & Radio Buttons
Custom geometric forms built on dark obsidian wells. Checked states ignite with an inner emerald fill, a soft radial glow, and a crisp white checkmark or center core.

### Input Fields
Encapsulated in deep charcoal wells with frosted glass translucency. Inputs feature subtle inner shadows and a 1px border that transitions from low-opacity mint to vibrant emerald green upon focus, accompanied by a soft ambient glow.

### Cards
The cornerstone of the interface. Cards are built as frosted glass containers with heavy backdrop blurs, 1px inner highlights, and layered internal padding. They hold high-density data visualizations, metric readouts, and modular dashboard widgets effortlessly within the obsidian environment.

### Additional Components
- **Command Palettes / Spotlight Search:** Floating glass command bars with high-contrast typography and real-time emerald keycap highlights.
- **Data Visualizations / Charts:** Glowing vector lines and neon emerald gradient area fills floating atop dark grid matrices.
- **Metric Readouts:** Large-scale Space Grotesk numerals paired with micro-label descriptions and live status indicator rings.