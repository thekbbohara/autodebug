# Custom Scan Phases

AutoDebug's scan phases are defined in `skills/autodebug.md`. You can customize them to fit your needs.

## Adding a New Phase

1. Open `skills/autodebug.md`
2. Find the `## SCAN PHASES` section
3. Add a new `### Phase N: YOUR_PHASE` block following this template:

```
### Phase N: PHASE_NAME
- `tool_name` → what to scan
- `search_text` for: patterns to look for
- Write findings immediately
- Skip if $FOCUS is not relevant
```

4. Update the `## FOCUS MODE PHASE MAP` table to include your phase in the relevant focus modes
5. Update the phase number in Phase 10 (REGRESSION CHECK) so it loops correctly

## Removing a Phase

1. Delete the phase block from the skill file
2. Renumber subsequent phases
3. Update the focus mode table
4. Update the regression phase number

## Example: Adding a Docker Scan Phase

```
### Phase 9.5: DOCKER
- `search_text` for: `latest`, `ADD .`, `sudo`, `chmod 777`
- `get_file_content` for Dockerfiles and docker-compose files
- Check for: running as root, no health checks, untagged images, exposed ports
- Write each finding as a separate .md file with `category: security`
- Skip if $FOCUS is `dead-code` or `performance`
```

## Example: Adding a API Contract Phase

```
### Phase 9.5: API_CONTRACT
- `search_text` for: `@route`, `@app.route`, `router.`, `app.get`, `app.post`
- `get_symbol_source` on route handler functions
- Check for: missing input validation, missing auth decorators, no rate limiting
- Check for: inconsistent response shapes, missing error responses
- Write findings
- Skip if $FOCUS is `dead-code` or `db`
```

## Testing Your Changes

After modifying the skill file, run the validation script:

```bash
python3 scripts/test_skill.py
```

This checks that the skill file parses correctly and all required sections are present. You may need to update `test_skill.py` to include your new phase in the `required_sections` list.
