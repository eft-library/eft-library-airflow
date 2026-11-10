import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugins'))
from custom_module.preset_reconstruction_contract import validate_preset_reconstruction


def detail():
    return {'preset':{'base_item_id':'gun'},'components':[
        {'component_index':0,'quantity':1,'item':{'id':'gun'},'attributes':{}},
        {'component_index':1,'quantity':1,'item':{'id':'sight'},'attributes':{'mode':[1,4]}},
    ],'reconstruction':{
        'method':'inferred','algorithm_version':1,'is_source_tree':False,'requires_confirmation':True,
        'validation_scope':'stored_slot_constraints','status':'unique','can_import':True,
        'is_unique':True,'search_complete':True,'solution_count_lower_bound':1,'states_examined':2,
        'candidate_trees':[{'nodes':[
            {'node_id':'root','item_id':'gun','parent_node_id':None,'slot_id':None,'attributes':{},'source_component_index':0,'source_unit_index':0},
            {'node_id':'sight','item_id':'sight','parent_node_id':'root','slot_id':'rail','attributes':{'mode':[1,4]},'source_component_index':1,'source_unit_index':0},
        ]}],'partial_tree':None,'unplaced_components':[],'issues':[],'issues_truncated':False,
    }}


class ReconstructionContractTest(unittest.TestCase):
    def test_valid_inferred_tree_is_preserved_without_mutation(self):
        value=detail();before=copy.deepcopy(value)
        self.assertIs(validate_preset_reconstruction(value),value['reconstruction'])
        self.assertEqual(value,before)

    def test_missing_result_or_false_source_or_proof_claim_is_rejected(self):
        value=detail();del value['reconstruction']
        with self.assertRaisesRegex(ValueError,'Missing preset reconstruction'):
            validate_preset_reconstruction(value)
        for change in ({'is_source_tree':True},{'search_complete':False},{'is_unique':False},{'can_import':False}):
            value=detail();value['reconstruction'].update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):
                validate_preset_reconstruction(value)

    def test_missing_or_changed_component_and_attributes_rejected(self):
        for change in ('remove','attributes','duplicate','parent','cycle','root','slot'):
            value=detail();nodes=value['reconstruction']['candidate_trees'][0]['nodes']
            if change=='remove':nodes.pop()
            elif change=='attributes':nodes[1]['attributes']={}
            elif change=='duplicate':nodes.append(copy.deepcopy(nodes[1]))
            elif change=='parent':nodes[1]['parent_node_id']='unknown'
            elif change=='cycle':nodes[1]['parent_node_id']='sight'
            elif change=='root':nodes[0]['item_id']='sight'
            else:nodes[1]['slot_id']=None
            with self.subTest(change=change),self.assertRaises(ValueError):
                validate_preset_reconstruction(value)

    def test_partial_result_must_account_for_all_unplaced_quantity(self):
        value=detail();r=value['reconstruction'];nodes=r['candidate_trees'][0]['nodes']
        r.update(status='incomplete',can_import=False,is_unique=None,solution_count_lower_bound=0,
                 candidate_trees=[],partial_tree={'nodes':[nodes[0]]},
                 unplaced_components=[{'component_index':1,'item_id':'sight','quantity':1,'attributes':{'mode':[1,4]}}])
        validate_preset_reconstruction(value)
        r['unplaced_components']=[]
        with self.assertRaisesRegex(ValueError,'lost components'):
            validate_preset_reconstruction(value)
