"""Validate a complete regular-mode snapshot and sync modding rows without committing."""

MOD_TYPES = {
    'ItemPropertiesWeaponMod', 'ItemPropertiesScope', 'ItemPropertiesMagazine',
    'ItemPropertiesBarrel',
}

# Fixed identifiers only: no source values are interpolated into SQL identifiers.
COLUMNS = {
    'item_ballistics': 'item_id,properties_type,center_of_impact,deviation_curve,deviation_max,velocity_raw,initial_speed_mps',
    'item_categories': 'id,parent_id,name_key,name_en,name_ko,name_ja,normalized_name',
    'item_category_memberships': 'item_id,category_id,sort_order',
    'item_slots': 'item_id,slot_id,name_id,name_key,name_en,name_ko,name_ja,required,sort_order',
    'item_slot_item_filters': 'item_id,slot_id,filter_type,target_item_id,sort_order',
    'item_slot_category_filters': 'item_id,slot_id,filter_type,category_id,sort_order',
    'item_conflicting_items': 'item_id,conflicting_item_id,sort_order',
    'item_conflicting_slots': 'item_id,conflicting_slot_id,sort_order',
    'item_conflicting_categories': 'item_id,category_id,sort_order',
    'item_mod_properties': 'item_id,properties_type,ergonomics,recoil_modifier,accuracy_modifier,zoom_levels,ergonomics_modifier,item_recoil_modifier,item_accuracy_modifier',
    'item_presets': 'preset_item_id,base_item_id,is_default,ergonomics,recoil_vertical,recoil_horizontal,moa',
    'weapon_preset_links': 'weapon_item_id,preset_item_id,is_listed,is_default_reference,sort_order',
    'item_preset_components': 'preset_item_id,component_index,item_id,quantity,attributes',
}
MASTERS = {
    'item_ballistics': 'item_id', 'item_categories': 'id', 'item_mod_properties': 'item_id',
    'item_presets': 'preset_item_id',
}


def _array(obj, key):
    value = obj[key]  # Missing fields must not erase previously collected relationships.
    if not isinstance(value, list):
        raise ValueError(f'{key} must be an array')
    return value


def _ref(value, master, label):
    if value not in master:
        raise ValueError(f'Unresolved {label}: {value}')
    return value


def build_modding_rows(data, translations=None):
    """Validate and map raw data before any database mutation; keep source scales/order."""
    translations = translations or {}
    items, categories = data['items'], data['itemCategories']
    if not isinstance(items, dict) or not items or not isinstance(categories, dict) or not categories:
        raise ValueError('A nonempty items/category snapshot is required')
    rows = {table: [] for table in COLUMNS}

    def names(key):
        return tuple(translations.get(lang, {}).get(key) for lang in ('en', 'ko', 'ja'))

    preset_ids = {key for key, x in items.items()
                  if (x.get('properties') or {}).get('propertiesType') == 'ItemPropertiesPreset'}
    for key, category in categories.items():
        if category['id'] != key:
            raise ValueError('Category key/id mismatch')
        parent = category['parent'] or None
        if parent is not None:
            _ref(parent, categories, 'category parent')
        name = category.get('name')
        rows['item_categories'].append((key, parent, name, *names(name), category.get('normalizedName')))

    for key, item in items.items():
        if item['id'] != key:
            raise ValueError('Item key/id mismatch')
        props = item['properties']
        if props is not None and not isinstance(props, dict):
            raise ValueError(f'Invalid properties: {key}')
        props = props or {}
        kind = props.get('propertiesType')
        if kind:
            rows['item_ballistics'].append((key, kind, props.get('centerOfImpact'),
                props.get('deviationCurve'), props.get('deviationMax'), item.get('velocity'), props.get('initialSpeed')))
        for index, category in enumerate(_array(item, 'categories')):
            rows['item_category_memberships'].append((key, _ref(category, categories, 'category'), index))
        if kind in MOD_TYPES or kind == 'ItemPropertiesWeapon':
            _array(props, 'slots')
        seen_slots = set()
        for index, slot in enumerate(props.get('slots', [])):
            sid = slot['id']
            if sid in seen_slots or not isinstance(slot['required'], bool):
                raise ValueError(f'Invalid/duplicate slot: {key}/{sid}')
            seen_slots.add(sid)
            name = slot.get('name')
            rows['item_slots'].append((key, sid, slot['nameId'], name, *names(name), slot['required'], index))
            filters = slot['filters']
            for source, table, typ, master in (
                ('allowedItems', 'item_slot_item_filters', 'allowed', items),
                ('excludedItems', 'item_slot_item_filters', 'excluded', items),
                ('allowedCategories', 'item_slot_category_filters', 'allowed', categories),
                ('excludedCategories', 'item_slot_category_filters', 'excluded', categories),
            ):
                for order, target in enumerate(_array(filters, source)):
                    rows[table].append((key, sid, typ, _ref(target, master, source), order))
        for source, table, master in (
            ('conflictingItems', 'item_conflicting_items', items),
            ('conflictingSlotIds', 'item_conflicting_slots', None),
            ('conflictingCategories', 'item_conflicting_categories', categories),
        ):
            for index, target in enumerate(_array(item, source)):
                if master is not None:
                    _ref(target, master, source)
                rows[table].append((key, target, index))
        if kind in MOD_TYPES or (kind and 'mods' in item.get('types', [])):
            rows['item_mod_properties'].append((
                key, kind, props.get('ergonomics'), props.get('recoilModifier'),
                props.get('accuracyModifier'), props.get('zoomLevels'),
                item.get('ergonomicsModifier'), item.get('recoilModifier'), item.get('accuracyModifier'),
            ))
        if kind == 'ItemPropertiesPreset':
            rows['item_presets'].append((
                key, _ref(props['baseItem'], items, 'preset base'), props.get('default'),
                props.get('ergonomics'), props.get('recoilVertical'), props.get('recoilHorizontal'), props.get('moa'),
            ))
            for index, component in enumerate(_array(item, 'containsItems')):
                quantity = component['count']
                if type(quantity) is not int or quantity <= 0:
                    raise ValueError('Invalid component quantity')
                attributes = component['attributes']
                if attributes is not None and not isinstance(attributes, dict):
                    raise ValueError('Invalid component attributes')
                rows['item_preset_components'].append((key, index, _ref(component['item'], items, 'component'), quantity, attributes))
        if kind == 'ItemPropertiesWeapon':
            default = props['defaultPreset']
            listed = _array(props, 'presets')
            if len(listed) != len(set(listed)):
                raise ValueError('Duplicate preset references cannot be represented')
            for index, preset in enumerate(listed):
                rows['weapon_preset_links'].append((key, _ref(preset, preset_ids, 'preset'), True, preset == default, index))
            if default and default not in listed:
                rows['weapon_preset_links'].append((key, _ref(default, preset_ids, 'default preset'), False, True, None))
    return rows


def sync_modding_rows(cursor, rows):
    """Caller owns transaction. Replace complete relationships; preserve master timestamps."""
    from psycopg2.extras import Json, execute_values

    # DELETE is transactional and does not cascade TRUNCATE into unrelated tables.
    for table in (
        'weapon_preset_links', 'item_preset_components', 'item_slot_item_filters',
        'item_slot_category_filters', 'item_category_memberships', 'item_conflicting_items',
        'item_conflicting_slots', 'item_conflicting_categories', 'item_slots',
    ):
        cursor.execute(f'DELETE FROM {table}')

    for table in COLUMNS:
        values = rows[table]
        if not values:
            continue
        columns = COLUMNS[table].split(',')
        json_columns = {'zoom_levels', 'attributes'}
        values = [tuple(Json(v) if col in json_columns and v is not None else v
                        for col, v in zip(columns, row)) for row in values]
        suffix = ''
        if table in MASTERS:
            pk = MASTERS[table]
            # Preserve previous translations when the translation endpoint omits a key.
            updates = [
                f'{col}=COALESCE(excluded.{col},{table}.{col})'
                if col in ('name_en', 'name_ko', 'name_ja') else f'{col}=excluded.{col}'
                for col in columns if col != pk
            ]
            suffix = f" ON CONFLICT ({pk}) DO UPDATE SET " + ','.join(updates + ['collected_at=now()', 'update_time=now()'])
        execute_values(cursor, f'INSERT INTO {table} ({COLUMNS[table]}) VALUES %s{suffix}', values, page_size=1000)

    # Links/components have already been replaced, so obsolete masters can now be removed.
    for table in ('item_ballistics', 'item_mod_properties', 'item_presets', 'item_categories'):
        pk = MASTERS[table]
        ids = [row[0] for row in rows[table]]
        cursor.execute(f'DELETE FROM {table} WHERE NOT ({pk} = ANY(%s::text[]))', (ids,))
