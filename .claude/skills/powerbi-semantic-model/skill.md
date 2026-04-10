---
name: powerbi-semantic-model
description: Guide for refactoring Power BI semantic models using TMDL format - hiding technical columns, renaming columns to English, and maintaining relationships
---

# Power BI Semantic Model Refactoring Guide

This guide documents best practices for refactoring Power BI semantic models using TMDL (Tabular Model Definition Language) format. All display names should be in **English**.

## Table of Contents

1. [TMDL File Structure](#tmdl-file-structure)
2. [Hiding Columns](#hiding-columns)
3. [Renaming Columns](#renaming-columns)
4. [Updating Relationships](#updating-relationships)
5. [Column Naming Standards](#column-naming-standards)
6. [Common Patterns](#common-patterns)
7. [Testing and Verification](#testing-and-verification)

---

## TMDL File Structure

### Key Files

Power BI projects (.pbip) in TMDL format have this structure:

```
ProjectName.pbip
ProjectName.SemanticModel/
  definition/
    model.tmdl                    # Model-level settings
    database.tmdl                 # Database metadata
    relationships.tmdl            # All table relationships
    tables/
      TABLE_NAME.tmdl            # Individual table definitions
    cultures/
      nb-NO.tmdl                 # Culture/translation files
ProjectName.Report/              # Report layer (separate from semantic model)
```

### Table Definition Format

```tmdl
table TABLE_NAME
    lineageTag: <guid>

    column 'Display Name'
        dataType: <type>
        isHidden                           # Optional: hides from field list
        formatString: <format>             # Optional: number/date format
        lineageTag: <guid>
        summarizeBy: <method>              # none, sum, count, etc.
        sourceColumn: DATABASE_COLUMN_NAME # Maps to source data

        variation Variasjon                # Optional: for date hierarchies
            isDefault
            relationship: <relationship-guid>
            defaultHierarchy: LocalDateTable_*.Datohierarki

        annotation SummarizationSetBy = Automatic

    partition TABLE_NAME = m
        mode: import
        source = 
            let
                [Power Query M code]
            in
                [final step]
```

---

## Hiding Columns

### When to Hide Columns

Hide these types of columns from end users:

1. **Surrogate keys** - Columns prefixed with `s_` or `S_`
   - `S_PK_*` (Primary keys)
   - `S_FK_*` (Foreign keys)
   - `S_DK_*` (Degenerate keys)

2. **Natural/Integration keys** - Columns suffixed with `_ik` or `_IK`
   - `CURRENCY_IK`
   - `COUNTRY_IK`

3. **ETL metadata** - System columns
   - `DBT_LAST_LOADED_DATETIME`
   - `ORIGINATING_SYSTEM_NO`
   - `CREATED_DATE` (unless business-relevant)
   - `LAST_CHANGE_TS` (unless business-relevant)

### How to Hide Columns

Add the `isHidden` property immediately after `dataType`:

```tmdl
column S_PK_DIM_CURRENCY
    dataType: string
    isHidden                    # Add this line
    lineageTag: 027649de-9fd3-4b69-b7a7-35e73a17a259
    summarizeBy: none
    sourceColumn: S_PK_DIM_CURRENCY
```

### Hidden Columns with Relationships

✅ **Hidden columns can have relationships** - this is standard Power BI behavior:

```tmdl
column DBT_LAST_LOADED_DATETIME
    dataType: dateTime
    isHidden                    # Column is hidden
    formatString: General Date
    sourceColumn: DBT_LAST_LOADED_DATETIME

    variation Variasjon
        isDefault
        relationship: d139872c-8b96-4293-9a99-88e429a18d7d  # Relationship still works
        defaultHierarchy: LocalDateTable_*.Datohierarki
```

The relationship continues to function even though users can't see the column in the field list.

---

## Renaming Columns

### Display Name vs Source Column

**Two separate concepts:**

- **Display Name** (column name in TMDL): What users see in the field list
- **sourceColumn**: The actual column name from the database/Power Query

```tmdl
column 'Currency Code'              # Display name (user sees this)
    dataType: string
    sourceColumn: CURRENCY          # Database column (never changes)
```

### Rules for Renaming

1. **Always use English** for display names
2. **Always preserve** the `sourceColumn` value
3. **Use single quotes** when display name contains spaces or special characters
4. **Never change** `sourceColumn` (breaks the model)
5. **Update relationships** when renaming columns

### Naming Conventions

Use clear, business-friendly English names:

| Database Column | Display Name |
|----------------|--------------|
| `CURRENCY` | `'Currency Code'` |
| `CURRENCY_NAME` | `'Currency Name'` |
| `CURRENCY_NAME_LONG` | `'Currency - Full Name'` |
| `COUNTRY_CODE_ALFA2` | `'Country Code (2 letters)'` |
| `COUNTRY_NAME` | `'Country Name'` |
| `CREATED_DATE` | `'Created Date'` (if visible) |

### Examples

**Before:**
```tmdl
column CURRENCY
    dataType: string
    sourceColumn: CURRENCY
```

**After:**
```tmdl
column 'Currency Code'
    dataType: string
    sourceColumn: CURRENCY          # sourceColumn unchanged
```

**Before (Norwegian):**
```tmdl
column 'Valutakode'
    dataType: string
    sourceColumn: CURRENCY
```

**After (English):**
```tmdl
column 'Currency Code'
    dataType: string
    sourceColumn: CURRENCY
```

---

## Updating Relationships

### When Relationships Need Updates

When you **rename a column**, you must update any relationships that reference it.

### Relationship Format

Relationships are defined in `relationships.tmdl`:

```tmdl
relationship <relationship-guid>
    joinOnDateBehavior: datePartOnly        # Optional: for date columns
    fromColumn: TABLE_NAME.'Column Name'    # Uses display name (not sourceColumn!)
    toColumn: OTHER_TABLE.'Other Column'    # Uses display name
```

### Important: Relationships Use Display Names

❌ **Wrong** - Using sourceColumn:
```tmdl
fromColumn: DIM_CURRENCY.CURRENCY
```

✅ **Correct** - Using display name:
```tmdl
fromColumn: DIM_CURRENCY.'Currency Code'
```

### Example: Renaming a Column with Relationships

**Step 1:** Rename column in table definition:

```tmdl
# In DIM_CURRENCY.tmdl
column 'Currency Code'              # Renamed from CURRENCY
    dataType: string
    sourceColumn: CURRENCY
```

**Step 2:** Update relationship reference:

```tmdl
# In relationships.tmdl
relationship 4dce7459-ccba-5a12-dbae-a4302b2c0da2
    fromColumn: FACT_SRE_BUILDING.S_FK_DIM_CURRENCY_PRODUCT_CURRENCY
    toColumn: DIM_CURRENCY.'Currency Code'    # Updated to use new display name
```

### Finding Relationships to Update

Search `relationships.tmdl` for the table name:

```bash
grep "DIM_CURRENCY" relationships.tmdl
```

---

## Column Naming Standards

### Standard Column Patterns

| Pattern | Display Name Format | Hidden? | Example |
|---------|-------------------|---------|---------|
| `S_PK_*` | (keep as-is) | ✅ Yes | `S_PK_DIM_CURRENCY` |
| `S_FK_*` | (keep as-is) | ✅ Yes | `S_FK_DIM_CURRENCY` |
| `S_DK_*` | (keep as-is) | ✅ Yes | `S_DK_CURRENCY_IK` |
| `*_IK` | (keep as-is) | ✅ Yes | `CURRENCY_IK` |
| `*_NO` | English name | Sometimes | `'System Number'` |
| `*_CODE` | English name | ❌ No | `'Currency Code'` |
| `*_NAME` | English name | ❌ No | `'Currency Name'` |
| `*_NAME_LONG` | English name | ❌ No | `'Currency - Full Name'` |
| `CREATED_DATE` | (hide or rename) | ✅ Yes* | Hidden unless business-relevant |
| `LAST_CHANGE_TS` | (hide or rename) | ✅ Yes* | Hidden unless business-relevant |
| `DBT_*` | (keep as-is) | ✅ Yes | `DBT_LAST_LOADED_DATETIME` |
| `ORIGINATING_SYSTEM_*` | (keep as-is) | ✅ Yes | `ORIGINATING_SYSTEM_NO` |

*Hide timestamp columns unless they have business value for end users.

### User-Facing Columns

Only expose columns that have **business value** to report users:

✅ **Show:**
- Business identifiers (codes, names)
- Descriptive attributes
- Measures and calculations
- Business-relevant dates

❌ **Hide:**
- Technical keys and IDs
- ETL metadata
- System timestamps
- Natural/integration keys

---

## Common Patterns

### Pattern 1: Dimension Table Cleanup

**Goal:** Hide all technical columns, rename business columns to English

**Before:**
```tmdl
table DIM_CURRENCY
    column S_PK_DIM_CURRENCY
    column S_DK_CURRENCY_IK
    column CREATED_DATE
    column CURRENCY
    column CURRENCY_IK
    column CURRENCY_NAME
    column CURRENCY_NAME_LONG
    column LAST_CHANGE_TS
    column ORIGINATING_SYSTEM_NO
    column DBT_LAST_LOADED_DATETIME
```

**After:**
```tmdl
table DIM_CURRENCY
    column S_PK_DIM_CURRENCY
        isHidden                              # Hidden
    column S_DK_CURRENCY_IK
        isHidden                              # Hidden
    column CREATED_DATE
        isHidden                              # Hidden
    column 'Currency Code'                    # Renamed, visible
        sourceColumn: CURRENCY
    column CURRENCY_IK
        isHidden                              # Hidden
    column 'Currency Name'                    # Renamed, visible
        sourceColumn: CURRENCY_NAME
    column 'Currency - Full Name'            # Renamed, visible
        sourceColumn: CURRENCY_NAME_LONG
    column LAST_CHANGE_TS
        isHidden                              # Hidden
    column ORIGINATING_SYSTEM_NO
        isHidden                              # Hidden
    column DBT_LAST_LOADED_DATETIME
        isHidden                              # Hidden
```

**Result:** Only 3 visible columns with clear English names.

### Pattern 2: Date Column with Auto Date Table

Date columns often have auto-generated LocalDateTable relationships:

```tmdl
column CREATED_DATE
    dataType: dateTime
    isHidden                    # Hidden but keeps relationship
    formatString: General Date
    sourceColumn: CREATED_DATE

    variation Variasjon         # Auto date hierarchy still works
        isDefault
        relationship: d195aee6-a6c2-46ff-bfea-495099ed8200
        defaultHierarchy: LocalDateTable_*.Datohierarki
```

**Relationship in relationships.tmdl:**
```tmdl
relationship d195aee6-a6c2-46ff-bfea-495099ed8200
    joinOnDateBehavior: datePartOnly
    fromColumn: DIM_CURRENCY.CREATED_DATE    # Uses column name (hidden but works)
    toColumn: LocalDateTable_*.Date
```

### Pattern 3: Fact Table Foreign Keys

Foreign key columns should be hidden:

```tmdl
table FACT_SRE_BUILDING
    column S_FK_DIM_CURRENCY_PRODUCT_CURRENCY
        dataType: string
        isHidden                              # Hidden
        sourceColumn: S_FK_DIM_CURRENCY_PRODUCT_CURRENCY
```

**Relationship:**
```tmdl
relationship 4dce7459-ccba-5a12-dbae-a4302b2c0da2
    fromColumn: FACT_SRE_BUILDING.S_FK_DIM_CURRENCY_PRODUCT_CURRENCY
    toColumn: DIM_CURRENCY.S_PK_DIM_CURRENCY  # Both columns hidden, works fine
```

---

## Testing and Verification

### Step 1: Open in Power BI Desktop

```
File → Open → Browse to Project.pbip
```

If the model doesn't open, check:
- ✅ Single quotes around names with spaces
- ✅ Relationship references match exact display names
- ✅ `sourceColumn` values unchanged
- ✅ Proper indentation (tabs, not spaces)

### Step 2: Verify Field List

In the Fields pane:

**Visible columns should:**
- Have clear English names
- Be business-relevant
- Not include technical IDs or metadata

**Hidden columns should:**
- Not appear in the field list
- Still function in relationships
- Be accessible via DAX formulas

### Step 3: Check Relationships

In Model view:
- All relationship lines should be intact
- Hidden columns can have relationships (this is normal)
- Cross-filtering should work in test visuals

### Step 4: Test Data Functionality

Create a test visual:
1. Add renamed columns to a table visual
2. Verify data displays correctly
3. Add measures from related fact tables
4. Confirm relationships work

### Step 5: Verify Row Counts

Before and after refactoring, row counts should be identical:
- Use `COUNT()` measures
- Check each table
- Confirm no data loss

---

## TMDL Syntax Rules

### Critical Syntax Rules

1. **Indentation:** Use **tabs** (not spaces)
2. **Column names with spaces:** Wrap in **single quotes**
   ```tmdl
   column 'Currency Code'        # Correct
   column "Currency Code"        # Wrong (use single quotes)
   column Currency Code          # Wrong (missing quotes)
   ```
3. **Relationship references:** Use **display name**, not sourceColumn
   ```tmdl
   fromColumn: DIM_CURRENCY.'Currency Code'    # Correct (display name)
   fromColumn: DIM_CURRENCY.CURRENCY          # Wrong (sourceColumn)
   ```
4. **Case sensitivity:** Column names are case-sensitive
5. **Property order:** `isHidden` comes after `dataType`

### Common Errors

❌ **Error:** `Cannot resolve all the paths while de-serializing Database`
- **Cause:** Relationship references old column name
- **Fix:** Update relationship to use new display name

❌ **Error:** TMDL parsing error
- **Cause:** Missing quotes, wrong indentation, or syntax error
- **Fix:** Check syntax, use tabs for indentation

❌ **Error:** Column not found in source
- **Cause:** Changed `sourceColumn` value
- **Fix:** Restore original `sourceColumn` value

---

## Multi-Language Support

### Current Approach: English Only

All display names should be in **English** as the base language. This approach:
- ✅ Works internationally
- ✅ Requires no special configuration
- ✅ Simplifies maintenance

### Alternative: Power BI Service Translations

For multi-language support, use **Power BI Service metadata translations** (not TMDL):

1. Publish semantic model to Power BI Service
2. Open dataset settings
3. Use "Translations" feature to add other languages
4. This creates translation metadata that works across all reports

**Note:** TMDL `translation` syntax is not supported in Power BI Desktop March 2026 version.

---

## Checklist: Refactoring a Table

Use this checklist when refactoring a table:

### Planning Phase
- [ ] Read the table definition file (`TABLE_NAME.tmdl`)
- [ ] List all columns and categorize (visible vs. hidden)
- [ ] Identify columns with relationships (search `relationships.tmdl`)
- [ ] Plan English display names for visible columns

### Implementation Phase
- [ ] Add `isHidden` to technical columns (s_*, *_ik, ETL metadata)
- [ ] Rename visible columns to English (preserve `sourceColumn`)
- [ ] Update relationships to use new display names
- [ ] Verify syntax (tabs, single quotes, property order)

### Testing Phase
- [ ] Open model in Power BI Desktop (no errors)
- [ ] Check field list (only visible columns appear)
- [ ] Verify relationships in Model view (all lines intact)
- [ ] Create test visual (data displays correctly)
- [ ] Confirm row counts match pre-refactoring

### Documentation Phase
- [ ] Document column mapping (database → display name)
- [ ] Note any special considerations
- [ ] Update team documentation

---

## Best Practices

### Do's ✅

- **Do** hide all technical/metadata columns
- **Do** use clear, business-friendly English names
- **Do** preserve `sourceColumn` values
- **Do** update relationships when renaming columns
- **Do** test thoroughly before committing changes
- **Do** use version control (git) for TMDL files

### Don'ts ❌

- **Don't** change `sourceColumn` values
- **Don't** use abbreviations in display names
- **Don't** hide business-relevant columns
- **Don't** forget to update relationships
- **Don't** use double quotes for column names (use single quotes)
- **Don't** mix languages in display names

---

## Example: Complete Table Refactoring

### Before: DIM_CURRENCY.tmdl

```tmdl
table DIM_CURRENCY
    column S_PK_DIM_CURRENCY
        dataType: string
        sourceColumn: S_PK_DIM_CURRENCY
    
    column CURRENCY
        dataType: string
        sourceColumn: CURRENCY
    
    column CURRENCY_NAME
        dataType: string
        sourceColumn: CURRENCY_NAME
    
    column DBT_LAST_LOADED_DATETIME
        dataType: dateTime
        sourceColumn: DBT_LAST_LOADED_DATETIME
```

### After: DIM_CURRENCY.tmdl

```tmdl
table DIM_CURRENCY
    column S_PK_DIM_CURRENCY
        dataType: string
        isHidden                              # HIDDEN
        sourceColumn: S_PK_DIM_CURRENCY
    
    column 'Currency Code'                    # RENAMED
        dataType: string
        sourceColumn: CURRENCY                # sourceColumn preserved
    
    column 'Currency Name'                    # RENAMED
        dataType: string
        sourceColumn: CURRENCY_NAME           # sourceColumn preserved
    
    column DBT_LAST_LOADED_DATETIME
        dataType: dateTime
        isHidden                              # HIDDEN
        sourceColumn: DBT_LAST_LOADED_DATETIME
```

### Result

**Visible to users (2 columns):**
- Currency Code
- Currency Name

**Hidden from users (2 columns):**
- S_PK_DIM_CURRENCY
- DBT_LAST_LOADED_DATETIME

---

## Troubleshooting

### Model Won't Open

**Symptom:** Error when opening .pbip file

**Common causes:**
1. Relationship references wrong column name
2. Missing single quotes around display name
3. Syntax error in TMDL file

**Solution:**
1. Check error message for specific file/line
2. Verify relationship references match display names
3. Check single quotes around names with spaces
4. Validate indentation (tabs, not spaces)

### Columns Still Visible

**Symptom:** Hidden columns appear in field list

**Common causes:**
1. `isHidden` not added
2. `isHidden` in wrong position
3. Model not refreshed

**Solution:**
1. Verify `isHidden` property exists
2. Ensure `isHidden` comes after `dataType`
3. Close and reopen Power BI Desktop

### Relationships Broken

**Symptom:** Relationship lines missing in Model view

**Common causes:**
1. Relationship references old column name
2. Typo in display name
3. Missing single quotes

**Solution:**
1. Search `relationships.tmdl` for table name
2. Update `fromColumn`/`toColumn` to match display names
3. Ensure exact match (case-sensitive)

---

## Quick Reference

### Hide a Column
```tmdl
column COLUMN_NAME
    dataType: <type>
    isHidden              # Add this line
```

### Rename a Column
```tmdl
column 'New Display Name'
    sourceColumn: OLD_DATABASE_NAME
```

### Update a Relationship
```tmdl
relationship <guid>
    fromColumn: TABLE.'New Display Name'
```

### Files to Modify
- `definition/tables/TABLE_NAME.tmdl` - Column definitions
- `definition/relationships.tmdl` - Relationship references

### Files to Never Modify
- `definition/model.tmdl` - Auto-generated
- `definition/cultures/nb-NO.tmdl` - Linguistic metadata (auto-generated)
- Power Query partition source code (unless explicitly needed)

---

## Additional Resources

### Power BI TMDL Documentation
- TMDL format is used for semantic models in Power BI projects (.pbip)
- Enables version control and text-based editing
- Supported in Power BI Desktop with "TMDL in Dataset" preview feature

### Git Best Practices
- Commit TMDL files to version control
- Use descriptive commit messages
- Review diffs before pushing changes
- Keep table refactorings in separate commits

### Team Collaboration
- Document naming conventions
- Share column mapping tables
- Coordinate refactoring efforts
- Test thoroughly before merging
