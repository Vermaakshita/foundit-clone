---
description: Create a new fully functional React TypeScript page for the Foundit clone
---

Create a new fully functional React TypeScript page called **$ARGUMENTS** for the Foundit.in clone.

Requirements:
- Use Tailwind CSS with exact Foundit brand colors (primary: #f04e23, navy: #1a1a2e)
- Include Navbar and Footer from components/layout/
- Fully responsive — mobile (320px) + tablet (768px) + desktop (1280px)
- Connect to FastAPI backend via src/api/ axios client (apiClient from src/api/client.ts)
- Use TanStack Query (useQuery/useMutation) for all data fetching
- Use AuthContext from src/context/AuthContext.tsx for auth state — do NOT use Zustand
- Add route in App.tsx router
- Handle loading states with Spinner and error states with error message
- Match Foundit.in UI for this page type exactly

File location rules:
- Top-level pages (Home, Jobs, Login etc.) → frontend/src/pages/$ARGUMENTS.tsx
- Seeker pages (Dashboard, Profile, SavedJobs etc.) → frontend/src/pages/seeker/$ARGUMENTS.tsx
- Employer pages (PostJob, MyJobs, Applicants etc.) → frontend/src/pages/employer/$ARGUMENTS.tsx
