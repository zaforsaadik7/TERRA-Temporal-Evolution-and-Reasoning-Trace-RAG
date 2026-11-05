# Codex-0116: corrected acquisition inventory accepted for user decision

14 October 2026, Asia/Dhaka. Reviewed Antigravity-0098 and official pinned Llama/Gemma tree listings. No acquisition, credential access, tokenizer execution or code change.

The corrected Gemma filename list and approximate size envelope are consistent with the official tree. Both proposed options are reasonable bounds, not measured exact totals. Recommend the smaller four-file fast-tokenizer subset (38,000,000 bytes); tokenizer.model is unused by the selected JSON backend and 'sibling fidelity' is not a demonstrated requirement. Alternatively, the user may choose the five-file set at 45,000,000 bytes. Llama three-file set at 22,000,000 bytes is reasonable.

Minor metadata corrections, not another acquisition-plan blocker: official pinned Llama listing displays special_tokens_map.json as 68 bytes and tokenizer_config.json as 55.4 kB, not 444 bytes/56.0 kB. The exact 17,209,920-byte claim was not independently authenticated by this tree read. Use approximate displayed values until actual files or upstream exact metadata are checked. A JSON chat-template file must be parsed/extracted, not passed as raw JSON to a Jinja renderer. Its content and relation to tokenizer_config remain to be inspected after lawful staging.

User decision requested: manual downloads of three Llama files and four Gemma files, capped per role at 22,000,000 and 38,000,000 bytes, respectively; isolated fresh staging only. Filenames: Llama tokenizer.json, tokenizer_config.json, special_tokens_map.json; Gemma tokenizer.json, tokenizer_config.json, special_tokens_map.json, chat_template.json. Pinned revisions remain those in Antigravity-0098.

Do not infer approval from this recommendation. No automated acquisition, local HF token access, validator coding/execution, canonical admission, real-data preflight or API calls is authorized. After user pathway/scope approval, provide simple exact browser instructions, preserve official URLs/download evidence and verify staged identities separately. Existing public files and eight-entry manifest remain untouched. No Databricks key needed.
