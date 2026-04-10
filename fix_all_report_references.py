"""
Fix all broken column/measure references in Power BI report visual JSON files.

This script updates field references from old all-caps names to proper English display names
to match the renamed columns/measures in the semantic model.
"""

from pathlib import Path
import json

# Complete mapping of old field names → new display names
# Organized by table for clarity
FIELD_MAPPINGS = {
    # DIM_SRE_PROPERTY columns
    "PROPERTY_NAME": "Property Name",
    "MAIN_BUILDING_SEGMENT": "Main Building Segment",
    "LOCATION": "Location",
    "POSTAL_AREA": "Postal Area",
    "CONSTRUCTED_YEAR": "Constructed Year",

    # DIM_SRE_PRODUCT columns
    "PORTFOLIO_ID": "Portfolio ID",
    "SUB_PORTFOLIO_ID": "Sub-Portfolio ID",

    # DIM_SRE_ENOVA_CERTIFICATE columns
    "BUILDING_CATEGORY": "Building Category",
    "ENERGY_CHARACTER": "Energy Character",
    "HEATING_CHARACTER": "Heating Character",
    "CERT_DATE": "Certification Date",

    # DIM_SRE_BREEAM_CERTIFICATE columns
    "RATING": "Rating",
    "CERT_UNTIL_DATE_CALC": "Calculated Valid Until Date",

    # FACT_SRE_BUILDING columns
    "AREA_GFA": "Gross Floor Area (m²)",
    "VALUATION_NOK": "Valuation (NOK)",

    # FACT_SRE_BREEAM_CERTIFICATE columns/measures
    "CERTIFIED_VALUE": "Certified Building Value",
    "HEATED_AREA_INUSE": "Heated Area In-Use (m²)",
    "HEATED_AREA_NOR": "Heated Area NOR (m²)",
    "SCORE": "BREEAM Score",
    "TOTAL_BUILDING_CATEGORY_HEATED_AREA": "Total Building Category Heated Area (m²)",
}

# Table mappings for queryRef and metadata updates
TABLE_MAPPINGS = {
    "PROPERTY_NAME": "DIM_SRE_PROPERTY",
    "MAIN_BUILDING_SEGMENT": "DIM_SRE_PROPERTY",
    "LOCATION": "DIM_SRE_PROPERTY",
    "POSTAL_AREA": "DIM_SRE_PROPERTY",
    "CONSTRUCTED_YEAR": "DIM_SRE_PROPERTY",
    "PORTFOLIO_ID": "DIM_SRE_PRODUCT",
    "SUB_PORTFOLIO_ID": "DIM_SRE_PRODUCT",
    "BUILDING_CATEGORY": "DIM_SRE_BREEAM_CERTIFICATE",
    "ENERGY_CHARACTER": "DIM_SRE_ENOVA_CERTIFICATE",
    "HEATING_CHARACTER": "DIM_SRE_ENOVA_CERTIFICATE",
    "CERT_DATE": "DIM_SRE_BREEAM_CERTIFICATE",
    "RATING": "DIM_SRE_BREEAM_CERTIFICATE",
    "CERT_UNTIL_DATE_CALC": "DIM_SRE_BREEAM_CERTIFICATE",
    "AREA_GFA": "FACT_SRE_BUILDING",
    "VALUATION_NOK": "FACT_SRE_BUILDING",
    "CERTIFIED_VALUE": "FACT_SRE_BREEAM_CERTIFICATE",
    "HEATED_AREA_INUSE": "FACT_SRE_BREEAM_CERTIFICATE",
    "HEATED_AREA_NOR": "FACT_SRE_BREEAM_CERTIFICATE",
    "SCORE": "FACT_SRE_BREEAM_CERTIFICATE",
    "TOTAL_BUILDING_CATEGORY_HEATED_AREA": "FACT_SRE_BREEAM_CERTIFICATE",
}


def fix_report_references():
    """Fix all field references in Power BI report visual JSON files."""

    report_dir = Path("storebrand_real_estate_semantic_model.Report/definition/pages")
    visual_files = list(report_dir.glob("*/visuals/*/visual.json"))

    # Also check page.json files which may have field references
    page_files = list(report_dir.glob("*/page.json"))

    all_files = visual_files + page_files
    files_modified = 0
    total_replacements = 0

    for file_path in all_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        modified_content = original_content
        file_replacements = 0

        # Replace each old field name with new display name
        for old_name, new_name in FIELD_MAPPINGS.items():
            table_name = TABLE_MAPPINGS.get(old_name, "")

            # Replace in Property fields
            old_property = f'"Property": "{old_name}"'
            new_property = f'"Property": "{new_name}"'
            if old_property in modified_content:
                count = modified_content.count(old_property)
                modified_content = modified_content.replace(old_property, new_property)
                file_replacements += count

            # Replace in queryRef fields (includes table name)
            if table_name:
                old_queryref = f'"queryRef": "{table_name}.{old_name}"'
                new_queryref = f'"queryRef": "{table_name}.{new_name}"'
                if old_queryref in modified_content:
                    count = modified_content.count(old_queryref)
                    modified_content = modified_content.replace(old_queryref, new_queryref)
                    file_replacements += count

                # Replace in metadata fields
                old_metadata = f'"metadata": "{table_name}.{old_name}"'
                new_metadata = f'"metadata": "{table_name}.{new_name}"'
                if old_metadata in modified_content:
                    count = modified_content.count(old_metadata)
                    modified_content = modified_content.replace(old_metadata, new_metadata)
                    file_replacements += count

        # Write back if modified
        if modified_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            files_modified += 1
            total_replacements += file_replacements
            print(f"[OK] {file_path.relative_to(report_dir.parent.parent)}: {file_replacements} replacements")

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Files modified: {files_modified}")
    print(f"  Total field reference replacements: {total_replacements}")
    print(f"{'='*60}")

    return files_modified, total_replacements


if __name__ == "__main__":
    print("Fixing Power BI report field references...")
    print(f"{'='*60}\n")

    try:
        files_modified, total_replacements = fix_report_references()

        if files_modified == 0:
            print("\n[OK] No broken references found - all reports are up to date!")
        else:
            print(f"\n[OK] Successfully fixed {total_replacements} field references in {files_modified} files")
            print("\nNext steps:")
            print("  1. Verify changes with: git diff storebrand_real_estate_semantic_model.Report/")
            print("  2. Test the report in Power BI Desktop")
            print("  3. Commit changes if everything works correctly")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        exit(1)
