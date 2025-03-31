# MTG Database Management

## Overview
This project uses generated JSON files for MTG rules and card data. These files are large and not tracked in version control.

## Database Generation

### Rules Database
1. Place the source text files in `app/db/`:
   - `MagicCompRules 20250207.txt`: Comprehensive rules text
   - `MTG_Glossary.txt`: Optional glossary terms

2. Run the rules converter:
   ```bash
   python app/db/rulesTxtToJson.py
   ```

3. Generated files:
   - `rules_db.json`: Rules database
   - `complete_rules_db.json`: Rules with glossary terms

### Card Database
1. Download card database:
   ```bash
   python app/db/download_data.py
   ```

2. Generated file:
   - `AllPrintings.json`: Comprehensive card database

## Gitignore
Ensure the following are in your `.gitignore`:
```
# Large JSON databases
app/db/*.json
!app/db/.gitkeep
```

## Regenerating Databases
- Always regenerate databases after pulling changes
- Do not commit generated JSON files to the repository

## Troubleshooting
- Ensure source text files are up to date
- Check file paths match the script expectations
- Verify Python environment and dependencies