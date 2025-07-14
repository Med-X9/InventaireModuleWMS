# Fix for 'NoneType' object has no attribute 'name' Error

## Problem Description

The error occurred during import operations in the Django admin interface when using the `django-import-export` library. The specific error was:

```
AttributeError: 'NoneType' object has no attribute 'name'
```

This happened in the `LocationResource` class in `apps/masterdata/admin.py` when trying to import location data.

## Root Cause

The issue was in the field definitions of the `LocationResource` class:

```python
# PROBLEMATIC CODE (before fix)
location_type_name = fields.Field(column_name='location type', attribute='location_type__name', widget=widgets.CharWidget())
sous_zone_name = fields.Field(column_name='sous zone', attribute='sous_zone__sous_zone_name', widget=widgets.CharWidget())
```

The problem was that:
1. The `attribute='location_type__name'` and `attribute='sous_zone__sous_zone_name'` were trying to access the `name` attribute on potentially `None` objects
2. During import, if the foreign key relationships (`location_type` or `sous_zone`) were `None`, the Django import-export library would try to access the `name` attribute on a `None` object
3. This caused the `AttributeError: 'NoneType' object has no attribute 'name'`

## Solution

The fix involved changing the field definitions to use proper `ForeignKeyWidget` widgets instead of trying to access nested attributes directly:

```python
# FIXED CODE (after fix)
location_type_name = fields.Field(column_name='location type', attribute='location_type', widget=widgets.ForeignKeyWidget(LocationType, 'name'))
sous_zone_name = fields.Field(column_name='sous zone', attribute='sous_zone', widget=widgets.ForeignKeyWidget(SousZone, 'sous_zone_name'))
```

### Additional Changes Made

1. **Updated `before_import_row` method**: Changed from setting IDs to setting actual model instances:
   ```python
   # Before
   row['location type'] = location_type_obj.id
   row['sous zone'] = sous_zone_obj.id
   
   # After
   row['location type'] = location_type_obj
   row['sous zone'] = sous_zone_obj
   ```

2. **Updated `save_instance` method**: Changed from using `_id` fields to using the actual foreign key fields:
   ```python
   # Before
   if hasattr(instance, 'location_type_id'):
       existing_location.location_type_id = instance.location_type_id
   
   # After
   if hasattr(instance, 'location_type'):
       existing_location.location_type = instance.location_type
   ```

3. **Fixed `RessourceResource`**: Applied the same fix to the `RessourceResource` class for consistency.

## Benefits of the Fix

1. **Prevents NoneType errors**: The `ForeignKeyWidget` properly handles `None` values and doesn't try to access attributes on `None` objects
2. **Better error handling**: The widgets provide better error messages when foreign key lookups fail
3. **Consistent approach**: All foreign key fields now use the same pattern across the codebase
4. **Maintains functionality**: The import/export functionality continues to work as expected

## Testing

A test script (`test_import_fix.py`) has been created to verify that the fix works correctly. The test:
- Creates test data (warehouse, zone, sous-zone, location type)
- Tests the `before_import_row` method
- Tests creating and saving location instances
- Cleans up test data

## Files Modified

- `apps/masterdata/admin.py`: Fixed `LocationResource` and `RessourceResource` classes
- `test_import_fix.py`: Test script to verify the fix
- `IMPORT_FIX_SUMMARY.md`: This documentation

## Prevention

To prevent similar issues in the future:
1. Always use `ForeignKeyWidget` for foreign key fields in import-export resources
2. Avoid using `attribute='model__field'` patterns that can cause NoneType errors
3. Ensure all dehydrate methods have proper null checks (`if obj.field else ''`)
4. Test import functionality with various data scenarios including missing foreign key references 