# Noble Houses

This document outlines the table used to store player-created noble houses or families.
These groups are largely social, letting players band together under a shared banner.

## Table: `noble_houses`

| Column | Meaning |
| --- | --- |
| `house_id` | Primary key for the house |
| `name` | Display name |
| `motto` | Optional motto or catch phrase |
| `crest` | URL or identifier for the house crest |
| `region` | Home region or origin |
| `description` | Free text description |
| `created_at` | Timestamp when the house was founded |

### Usage
- Houses can be created via `/api/noble_houses`.
- The CRUD API allows listing, updating and deleting houses.
