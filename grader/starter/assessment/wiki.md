# User API Notes (Last updated: 2022)

- All users have a unique `id` in string format (UUID v4).
- Use `/users?team=xyz` to filter by team. Status filtering not supported.
- Inactive users = `isActive: false` in DB.
