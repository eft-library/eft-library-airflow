BEGIN;

DELETE FROM tkl_user_icon
WHERE user_email IN (
    SELECT email FROM tkl_user_delete
    WHERE delete_end_time < NOW()
);

DELETE FROM tkl_user_quest
WHERE user_email IN (
    SELECT email FROM tkl_user_delete
    WHERE delete_end_time < NOW()
);

DELETE FROM tkl_user_delete
WHERE delete_end_time < NOW();

COMMIT;
