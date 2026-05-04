---
description: Test a complete user flow using Puppeteer MCP on the running app
---

Using **Puppeteer MCP**, test this user flow: **$ARGUMENTS**

App URLs:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

Steps:
1. Navigate to the starting page
2. Execute each step of the flow: $ARGUMENTS
3. Screenshot at each key step
4. Check browser console for JS errors
5. Verify the expected outcome
6. Report: passed steps, failed steps, screenshots of issues
