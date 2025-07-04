# Content Moderation Overview

Thronestead enforces a strict content policy. The `services/moderation.py` module contains helper functions used by the API to flag or reject user supplied text. Detection covers the following categories:

- **Hate Speech / Discriminatory Content**
- **Sexually Explicit or Inappropriate Content**
- **Harassment / Bullying / Threats**
- **Profanity and Vulgarity**
- **Terrorism / Violent Extremism**
- **Impersonation / Deceptive Identity** (via `has_reserved_username`)
- **Illegal Content / Criminal Advocacy**
- **Spam / Malicious Links**
- **Personal Information** (emails or phone numbers)
- **User-Submitted Media** (avatars or uploads)
- **Child Protection** (COPPA/GDPR-K compliance)

Personal information checks detect standard email formats and common phone number
patterns (with or without country codes). This helps prevent young players from
sharing contact details in violation of COPPA and GDPR-K regulations.

`classify_text(text)` returns a dictionary of flags for these categories. `is_clean(text)` returns `True` only when all checks pass. Helper functions `validate_clean_text` and `validate_username` raise `ValueError` when supplied text violates any rule. The frontend uses `Javascript/content_filter.js` to provide immediate feedback, while the backend routes validate message, signup and profile fields using the same utilities.

User reports can be filed via the `/api/reports` endpoint. These reports are stored for moderator review.
