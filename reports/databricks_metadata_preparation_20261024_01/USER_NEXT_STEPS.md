# Ready for the Databricks metadata key

The checker is prepared for https://dbc-899e438f-4c30.cloud.databricks.com only. No authenticated request or inference has been made. An empty credential file already exists; do not rerun the file-creation helper.

1. On the workspace's Settings > Developer > Access tokens page, generate a token named TERRA metadata check, with a short lifetime such as one day. If API scope selection is offered, select the model-serving scope needed for the serving-endpoint metadata APIs. Do not enable unrelated APIs or auto-scoping for this check. If that scope is unavailable, stop and describe the choices without sharing a token. The token's permissions may be broader than read-only; the collector itself implements only the approved GET operations.
2. Press Win+R and run:

   `notepad "F:\TERRA -Copy\.env.terra-databricks.local"`

   Paste the token after the existing `DATABRICKS_TOKEN=`. Use one line, without quotation marks, and press Ctrl+S. Do not paste the token into chat or any report. The existing file avoids an accidental .txt suffix.
3. Tell Codex: **Saved — run the read-only check.** That requests the bounded metadata check only, not a model invocation or paid smoke/study.

The file is ignored by the repository's .env.* pattern. Inheritance is disabled; access verified for the human profile user, the setup sandbox owner, and SYSTEM. Windows administrators and privileged processes are not prevented by an absolute security guarantee. No credential value was supplied or read during preparation.

## Exact authorized collector scope when requested

- GET `/api/2.0/serving-endpoints`, followed by at most four GET details for the fixed Gemma, Llama, Qwen and GPT-OSS candidate names if listed.
- No POST/PUT/PATCH/DELETE, inference, SQL, warehouses, model loading, endpoint creation/configuration changes or retries. Unexpected pagination stops for review rather than inventing another request.
- Verified HTTPS to the one pinned host; redirect is rejected. Thirty-second observed deadline/socket timeout per request; one MiB response bound. This is not a universal hard-interruption guarantee for every native/DNS stall.
- Fresh output folder under reports/databricks_metadata_... with sanitized report.json. Do not persist raw endpoint configs, environment variables, external credentials, creator identities, headers or provider error bodies. Exact token echoes in selected string fields are redacted. No claim of perfect Python memory zeroization.
- Unlisted candidates mean not listed with that credential, not proof of global absence. Metadata readiness is not an inference compatibility test, an authenticated returned model identity, or billing certification. Region, negotiated rates/credits and user spend caps may still need confirmation.

## Future local execution command (no secret in argv)

`& 'C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe' -I -S -B 'F:\TERRA -Copy\scripts\matched_baseline\inspect_databricks_metadata.py' --execute-read-only`

The user need not run it manually; Codex can execute after the user says the file is saved and requests the read-only check. This preparation did not read the credential placeholder or run that command.

Official references checked 24 October 2026:

- https://docs.databricks.com/api/model-serving/v1/serving-endpoint
- https://docs.databricks.com/aws/en/dev-tools/auth/pat
