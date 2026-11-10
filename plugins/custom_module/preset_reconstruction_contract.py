"""Validate inferred preset trees before publishing a complete static generation."""
from collections import Counter


def _tree(tree, components, base_item_id, complete):
    nodes=tree.get('nodes') if isinstance(tree,dict) else None
    if not isinstance(nodes,list) or not nodes or len(nodes)>200:
        raise ValueError('Invalid preset reconstruction nodes')
    rows={c['component_index']:c for c in components}
    if len(rows)!=len(components):
        raise ValueError('Duplicate preset component index')
    indexed={n.get('node_id'):n for n in nodes if isinstance(n,dict)}
    if len(indexed)!=len(nodes) or any(not isinstance(key,str) or not key for key in indexed):
        raise ValueError('Duplicate or invalid reconstruction node ID')
    roots=[n for n in nodes if n.get('parent_node_id') is None]
    if len(roots)!=1 or roots[0].get('item_id')!=base_item_id or roots[0].get('slot_id') is not None:
        raise ValueError('Invalid preset reconstruction root')
    counts=Counter();units=set();occupied=set()
    for node in nodes:
        index=node.get('source_component_index');unit=node.get('source_unit_index')
        if type(index) is not int or index not in rows or type(unit) is not int or not 0<=unit<rows[index]['quantity']:
            raise ValueError('Invalid reconstruction component instance')
        if (index,unit) in units:
            raise ValueError('Duplicate reconstruction component instance')
        units.add((index,unit));counts[index]+=1
        row=rows[index]
        if node.get('item_id')!=row['item']['id'] or node.get('attributes')!=row.get('attributes'):
            raise ValueError('Preset reconstruction changed component or attributes')
        parent=node.get('parent_node_id')
        if parent is not None:
            if parent not in indexed or not isinstance(node.get('slot_id'),str) or not node['slot_id']:
                raise ValueError('Unknown reconstruction parent or slot')
            key=(parent,node['slot_id'])
            if key in occupied:
                raise ValueError('Duplicate reconstruction parent slot')
            occupied.add(key)
        visited=set();current=node
        while current.get('parent_node_id') is not None:
            if current['node_id'] in visited:
                raise ValueError('Cyclic reconstruction tree')
            visited.add(current['node_id'])
            if current['parent_node_id'] not in indexed:
                raise ValueError('Unknown reconstruction ancestor')
            current=indexed[current['parent_node_id']]
    expected=Counter({c['component_index']:c['quantity'] for c in components})
    if complete and counts!=expected:
        raise ValueError('Incomplete reconstruction candidate')
    return counts


def validate_preset_reconstruction(detail):
    value=detail.get('reconstruction')
    if not isinstance(value,dict):
        raise ValueError('Missing preset reconstruction; deploy the new modding API first')
    if (value.get('method')!='inferred' or value.get('algorithm_version')!=1
            or value.get('is_source_tree') is not False or value.get('requires_confirmation') is not True
            or value.get('validation_scope')!='stored_slot_constraints'):
        raise ValueError('Invalid preset reconstruction provenance')
    status=value.get('status')
    if status not in ('unique','ambiguous','incomplete','unavailable','search_limited'):
        raise ValueError('Invalid reconstruction status')
    candidates=value.get('candidate_trees')
    if not isinstance(candidates,list) or len(candidates)>3 or type(value.get('can_import')) is not bool:
        raise ValueError('Invalid reconstruction candidates')
    if value['can_import']!=bool(candidates) or type(value.get('search_complete')) is not bool:
        raise ValueError('Invalid reconstruction import/proof flags')
    if type(value.get('solution_count_lower_bound')) is not int or value['solution_count_lower_bound']!=len(candidates):
        raise ValueError('Invalid reconstruction solution count')
    if status=='unique' and (len(candidates)!=1 or value.get('is_unique') is not True or not value['search_complete']):
        raise ValueError('Unproven unique reconstruction')
    if status=='ambiguous' and (len(candidates)<2 or value.get('is_unique') is not False):
        raise ValueError('Invalid ambiguous reconstruction')
    if status in ('incomplete','unavailable') and candidates:
        raise ValueError('Unavailable reconstruction has importable candidates')
    if status=='search_limited' and (value['search_complete'] or value.get('is_unique') is not None):
        raise ValueError('Limited reconstruction cannot prove uniqueness')
    components=detail['components'];base=detail['preset']['base_item_id']
    for tree in candidates:_tree(tree,components,base,True)
    partial=value.get('partial_tree')
    placed=_tree(partial,components,base,False) if partial is not None else Counter()
    unplaced=value.get('unplaced_components')
    if not isinstance(unplaced,list) or not isinstance(value.get('issues'),list):
        raise ValueError('Invalid reconstruction diagnostics')
    if candidates:
        if partial is not None or unplaced:
            raise ValueError('Complete candidate has unplaced components')
    else:
        expected={c['component_index']:c for c in components}
        seen=set()
        for row in unplaced:
            index=row.get('component_index')
            if index not in expected or index in seen:
                raise ValueError('Invalid unplaced component index')
            seen.add(index);original=expected[index]
            if (type(row.get('quantity')) is not int or row['quantity']<=0
                    or row.get('item_id')!=original['item']['id'] or row.get('attributes')!=original.get('attributes')):
                raise ValueError('Unplaced component data changed')
            placed[index]+=row['quantity']
        if placed!=Counter({c['component_index']:c['quantity'] for c in components}):
            raise ValueError('Reconstruction silently lost components')
    return value
