---
description: Screenshot current page, compare to Foundit.in and fix all differences
---

Fix the UI to exactly match Foundit.in for: **$ARGUMENTS**

Process:
1. Use Puppeteer MCP to screenshot the current page
2. Compare against Foundit.in design for this page
3. List every visual difference (spacing, colors, fonts, layout, missing elements)
4. Fix each difference in the React component
5. Screenshot again to verify the match
6. Repeat until it closely matches Foundit.in

Focus on: orange #f04e23 for CTAs, card layouts, typography sizes, padding and margins.
