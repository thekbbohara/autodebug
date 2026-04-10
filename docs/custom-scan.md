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
5. Update the phase number in Phase 12 (REGRESSION CHECK) so it loops correctly
6. Update `scripts/repo_audit.py` `init_audit` to include the new phase
7. Update `scripts/test_skill.py` `test_required_sections` to include the new phase name

## Removing a Phase

1. Delete the phase block from the skill file
2. Renumber subsequent phases
3. Update the focus mode table
4. Update the regression phase number
5. Update `scripts/repo_audit.py` and `scripts/test_skill.py`

## Current Phase List

| Phase | Name |
|-------|------|
| 1 | RECON |
| 2 | DEAD CODE |
| 3 | HOTSPOTS |
| 4 | DEPENDENCIES |
| 5 | SECURITY SCAN |
| 6 | LOGIC BUGS |
| 7 | TYPE SAFETY |
| 8 | PERFORMANCE |
| 9 | DB SCAN |
| 10 | API CONTRACT SCAN |
| 11 | DOCKER SCAN |
| 12 | REGRESSION CHECK |
| 13 | WRITE TEST CASES |

## Example: Adding a Kubernetes Scan Phase

```
### Phase 11.5: KUBERNETES SCAN
- `search_text` for: `apiVersion:|kind:|metadata:|spec:` in *.yaml files
- `get_file_content` for kubernetes manifest files
- Check for: running as root, no resource limits, hostPath mounts, privileged containers
- Check for: no liveness/readiness probes, latest image tags, no network policies
- Write findings with `category: docker`
- Skip if $FOCUS is `performance`, `dead-code`, or `db`
```

## Testing Your Changes

After modifying the skill file, run the validation script:

```bash
python3 scripts/test_skill.py
```

This checks that the skill file parses correctly and all required sections are present. You may need to update `test_skill.py` to include your new phase in the `required_sections` list and update `repo_audit.py` to include the new phase in `init_audit`.
