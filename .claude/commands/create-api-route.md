---
description: Add a new fully functional FastAPI endpoint to the backend
---

Add a complete production-grade FastAPI endpoint for: **$ARGUMENTS**

Steps:
1. Add Pydantic request + response models in backend/app/models/
2. Create or update router in backend/app/routers/
3. Use Supabase Python client from app/services/supabase.py for all DB operations
4. Add JWT auth dependency (get_current_user) where authentication is required
5. Return proper HTTP status codes and error messages via HTTPException
6. Register router in backend/app/main.py if it is a new file
7. Follow patterns already in the codebase

Reference CLAUDE.md for exact table/column names.
