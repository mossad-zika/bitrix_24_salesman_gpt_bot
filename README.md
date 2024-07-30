# bitrix_24_salesman_gpt_bot

### SQL list allowed users
```sql
SELECT * FROM allowed_users;
```

### SQL allow user
```sql
INSERT INTO allowed_users (user_id) VALUES (105013941);
```

### SQL remove user
```sql
DELETE FROM allowed_users WHERE user_id = 105013941;
```

### SQL balance change
```sql
insert into user_balances (user_id, balance, images_generated) VALUES (105013941, 100.0, 0)
```

### Bash example
```bash
psql -U $POSTGRES_USER \
-d $POSTGRES_DB \
-c "INSERT INTO allowed_users (user_id) VALUES (105013941);"
```

### Add user to allowed via curl
```bash
curl 'http://localhost:5005/allow' -v --location --data-raw 'user_id=105013941'
```

### Mentor notes
- Replace "Successfully **generated** an image" text with "Successfully **send** an image" in early versions
- Fix CMD to ENTRYPOINT in early versions
- Fix `logging.info() and logging.error()` to `logger.info() and logger.error()` in early versions
- Fix user-manager WORKDIR in early versions
- Update Python
- User-Manager: add 'app' dir like it is done with a bot
- Fix the "edited text" or "edited image command" bug with `if update.edited_message`
