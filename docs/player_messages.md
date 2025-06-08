# Player Messages

The `player_messages` table stores direct player-to-player private mail. Each row represents a single message from one user to another.

## Table Structure

| Column | Usage |
| --- | --- |
| `message_id` | Unique message ID (PK) |
| `user_id` | Who sent the message (FK to `users.user_id`, `ON DELETE SET NULL`) |
| `recipient_id` | Who received the message (FK to `users.user_id`, `ON DELETE SET NULL`) |
| `subject` | Optional subject line |
| `message` | Message text |
| `sent_at` | When the message was sent |
| `is_read` | Whether the recipient has read it |
| `deleted_by_sender` | Soft-delete flag for sender |
| `deleted_by_recipient` | Soft-delete flag for recipient |
| `last_updated` | Timestamp of last update |

## Usage

### Sending a message
```sql
INSERT INTO public.player_messages (user_id, recipient_id, subject, message)
VALUES ('SENDER-UUID', 'RECIPIENT-UUID', 'Hello', 'Hello there!');
```

### Listing inbox
```sql
SELECT * FROM public.player_messages
WHERE recipient_id = 'RECIPIENT-UUID'
  AND deleted_by_recipient = false
ORDER BY sent_at DESC
LIMIT 50;
```

### Listing sent messages
```sql
SELECT * FROM public.player_messages
WHERE user_id = 'SENDER-UUID'
  AND deleted_by_sender = false
ORDER BY sent_at DESC
LIMIT 50;
```

### Marking as read
```sql
UPDATE public.player_messages
SET is_read = true
WHERE message_id = ?;
```

Messages should never be hard deleted. Use the deleted flags so players can recover messages and moderation can review disputes.
