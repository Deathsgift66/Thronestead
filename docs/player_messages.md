# Player Messages

The `player_messages` table stores direct player-to-player private mail. Each row represents a single message from one user to another.

## Table Structure

| Column | Usage |
| --- | --- |
| `message_id` | Unique message ID (PK) |
| `user_id` | Who sent the message (FK to `users.user_id`, `ON DELETE SET NULL`) |
| `recipient_id` | Who received the message (FK to `users.user_id`, `ON DELETE SET NULL`) |
| `message` | Message text |
| `sent_at` | When the message was sent |
| `is_read` | Whether the recipient has read it |

## Usage

### Sending a message
```sql
INSERT INTO public.player_messages (user_id, recipient_id, message)
VALUES ('SENDER-UUID', 'RECIPIENT-UUID', 'Hello there!');
```

### Listing inbox
```sql
SELECT * FROM public.player_messages
WHERE recipient_id = 'RECIPIENT-UUID'
ORDER BY sent_at DESC
LIMIT 50;
```

### Listing sent messages
```sql
SELECT * FROM public.player_messages
WHERE user_id = 'SENDER-UUID'
ORDER BY sent_at DESC
LIMIT 50;
```

### Marking as read
```sql
UPDATE public.player_messages
SET is_read = true
WHERE message_id = ?;
```

Messages should never be hard deleted so moderation can review disputes if needed.
