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

### Bash example
```bash
psql -U $POSTGRES_USER \
-d $POSTGRES_DB \
-c "INSERT INTO allowed_users (user_id) VALUES (105013941);"
```