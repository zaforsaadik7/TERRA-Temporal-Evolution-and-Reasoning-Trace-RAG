"""Pure cohort contracts and injected control loops; no assets or native calls."""
from dataclasses import asdict, replace
from hashlib import sha256
import io
import json
import unittest
from unittest.mock import Mock

from scripts.matched_baseline import offline_cohort_contracts as c
from scripts.matched_baseline import offline_cohort_controls as control


def fixture_spec():
    rows = []
    for prefix, category, count in (('A','A_Factual',100),('B','B_Evolutionary',100),
            ('C','C_OutOfContext',75),('D','D_Adversarial',75)):
        rows.extend(c.QueryIdentity(f'{prefix}{i:03d}', sha256(f'text {prefix}{i}'.encode()).hexdigest(), category)
                    for i in range(count))
    return c.CohortSpec(tuple(rows))


def fixture_row(identity):
    metrics = {}
    for route in ('EASY','HARD'):
        row = {'route_name':route,'query_id':identity.query_id,'all_roles_passed':True,
               'router_fits':True,'router_prompt_tokens':1,'arm_t_structural_chars':1}
        for arm in ('h','t'):
            for key in ('gen_fits','verifier_fits','judge1_fits','judge2_fits'):
                row[f'arm_{arm}_{key}'] = True
            for key in ('admitted_count','evidence_tokens','prompt_tokens','verifier_tokens','judge1_tokens','judge2_tokens'):
                row[f'arm_{arm}_{key}'] = 1
        metrics[route] = row
    return {'mode':'SIMULATED','scope':c.SCOPE,'query_id':identity.query_id,
        'query_text_sha256':identity.text_sha256,'documents':20000,
        'dense_candidate_ids':[f'doc-{i}' for i in range(100)],
        'graph_seed_ids':['doc-0','doc-1'],'graph_audit':{'schema_valid':True,'total_nodes':20000},
        'hypothetical_route_metrics':metrics,'caveat':'Synthetic fixture, not actual cohort results.'}


class CohortContractTests(unittest.TestCase):
    def test_spec_has_distinct_scope_and_fixed_root_benchmark(self):
        spec = fixture_spec().validate()
        raw = spec.request_bytes()
        self.assertLess(len(raw),1024**2)
        self.assertNotIn(b'gold',raw)
        for bad in (replace(spec,scope='ONE_QUERY_OFFLINE_SMOKE'),
                    replace(spec,benchmark_path='F:\\TERRA -Copy\\dataset_20k_cap\\terra_350_benchmark.json'),
                    replace(spec,benchmark_sha256='0'*64), replace(spec,batch_size=True),
                    replace(spec,queries=spec.queries[:-1])):
            with self.assertRaises(ValueError): bad.validate()

    def test_duplicate_identity_and_wrong_distribution_rejected(self):
        spec = fixture_spec()
        for rows in ((spec.queries[0],)+spec.queries[:-1],
                (replace(spec.queries[0],category='D_Adversarial'),)+spec.queries[1:]):
            with self.assertRaises(ValueError): replace(spec,queries=rows).validate()

    def test_resources_reject_boolean_or_unreviewed_changes(self):
        policy = c.ProposedResources()
        with self.assertRaises(ValueError): replace(policy,child_seconds=1).validate(reviewed=policy)
        bad = replace(policy,child_seconds=True)
        with self.assertRaises(ValueError): bad.validate(reviewed=bad)

    def test_report_350_combined_rows_means_700_route_rows(self):
        spec = fixture_spec(); builder = c.CohortReportBuilder(spec,c.ProposedResources(),expected_mode='SIMULATED')
        for identity in spec.queries: builder.add(fixture_row(identity))
        report = json.loads(builder.finish())
        self.assertEqual(report['query_count'],350)
        self.assertEqual(report['route_record_count'],700)
        self.assertTrue(report['complete'])
        with self.assertRaises(ValueError): builder.add(fixture_row(spec.queries[0]))

    def test_incomplete_and_wrong_order_cannot_pass(self):
        spec = fixture_spec(); builder = c.CohortReportBuilder(spec,c.ProposedResources(),expected_mode='SIMULATED')
        with self.assertRaises(ValueError): builder.finish()
        with self.assertRaises(ValueError): builder.add(fixture_row(spec.queries[1]))
        self.assertFalse(json.loads(builder.partial())['complete'])

    def test_per_query_cap_combines_both_routes_and_does_not_truncate(self):
        spec = fixture_spec(); builder = c.CohortReportBuilder(spec,c.ProposedResources(),expected_mode='SIMULATED')
        row = fixture_row(spec.queries[0]); row['caveat'] = 'x'*32768
        with self.assertRaises(ValueError): builder.add(row)
        self.assertEqual(len(builder.rows),0)

    def test_extra_gold_field_wrong_population_or_mode_rejected(self):
        spec = fixture_spec()
        for key, value in (('gold_answer','secret'),('documents',19999),('mode','AUTHENTIC_OFFLINE_FEASIBILITY')):
            row = fixture_row(spec.queries[0]);row[key] = value
            with self.assertRaises(ValueError):
                c.CohortReportBuilder(spec,c.ProposedResources(),expected_mode='SIMULATED').add(row)

    def test_input_mutation_does_not_change_stored_row(self):
        spec=fixture_spec();builder=c.CohortReportBuilder(spec,c.ProposedResources(),expected_mode='SIMULATED')
        row=fixture_row(spec.queries[0]);builder.add(row);row['dense_candidate_ids'].clear()
        self.assertEqual(len(builder.rows[0]['dense_candidate_ids']),100)

    def test_approval_binds_order_resources_scope_and_single_attempt(self):
        spec=fixture_spec();policy=c.ProposedResources()
        record={'approval_id':'FIXTURE_ONLY','approval_date':'2026-10-23','scope':c.SCOPE,
            'request_sha256':sha256(spec.request_bytes()).hexdigest(),'resources':asdict(policy),
            'rule_name':'TERRA_Cohort_FIXTURE_01','owner_tag':'TERRA_COHORT_FIXTURE_01',
            'max_attempts':1,'allow_api_calls':False,'allow_manuscript_changes':False,
            'launch_binding_sha256':'a'*64}
        raw=c.encode(record,65536)
        self.assertEqual(c.verify_cohort_approval(raw,expected_sha256=sha256(raw).hexdigest(),
            reviewed_record=record,spec=spec,resources=policy,reviewed_launch_binding_sha256='a'*64),record)
        for key,value in (('scope','ONE_QUERY_OFFLINE_SMOKE'),('max_attempts',True),('allow_api_calls',True)):
            bad={**record,key:value};blob=c.encode(bad,65536)
            with self.assertRaises(ValueError): c.verify_cohort_approval(blob,
                expected_sha256=sha256(blob).hexdigest(),reviewed_record=bad,spec=spec,resources=policy,
                reviewed_launch_binding_sha256='a'*64)
        with self.assertRaises(ValueError):c.verify_cohort_approval(raw,
            expected_sha256=sha256(raw).hexdigest(),reviewed_record=record,spec=spec,resources=policy,
            reviewed_launch_binding_sha256='b'*64)


class CohortControlTests(unittest.TestCase):
    def setUp(self):
        self.time=0.0;self.events=[]
        self.policy=replace(c.ProposedResources(),child_seconds=2,outer_seconds=10,
            finalization_reserve_seconds=1,memory_bytes=100,capture_bytes=10,
            evidence_bytes=200,disposable_growth_bytes=30,termination_wait_seconds=1,
            free_space_floor_bytes=20)

    def pause(self,seconds): self.time+=seconds

    def state(self,**changes):
        return {'active_processes':1,'root_exited':False,'exit_code':None,
            'memory_limit_hit':False,'peak_memory_bytes':80,'output_bytes':0,
            'evidence_bytes':0,'disposable_bytes':100,**changes}

    def run_backend(self,states,*,confirmed=True,outer=0,child=0):
        backend=Mock();backend.state.side_effect=states;backend.wait_empty.return_value=confirmed
        boundary=Mock()
        result=control.CohortSupervisor(self.policy,clock=lambda:self.time,pause=self.pause,
            emit=self.events.append).run(backend,boundary,outer_started=outer,child_started=child,baseline_bytes=100)
        return result,backend,boundary

    def test_success_still_requires_report_audit_and_confirms_rule_cleanup(self):
        result,backend,boundary=self.run_backend([self.state(),
            self.state(active_processes=0,root_exited=True,exit_code=0)])
        self.assertEqual(result['status'],'PROCESS_SUCCESS_REQUIRES_REPORT_AND_INTEGRITY_AUDIT')
        boundary.remove_owned_rule.assert_called_once();backend.terminate.assert_not_called()
        backend.close.assert_called_once()

    def test_child_timeout_unconfirmed_tree_retains_rule(self):
        self.time=2
        result,backend,boundary=self.run_backend([],confirmed=False)
        self.assertEqual(result['failure_type'],'TimeoutError')
        backend.terminate.assert_called_once();boundary.remove_owned_rule.assert_not_called()
        boundary.retain_owned_rule_for_recovery.assert_called_once()

    def test_outer_reserve_prevents_more_computation(self):
        self.time=9
        result,backend,boundary=self.run_backend([],child=9)
        self.assertEqual(result['failure_type'],'TimeoutError')
        backend.state.assert_not_called();backend.terminate.assert_called_once()
        boundary.remove_owned_rule.assert_called_once()

    def test_observed_resource_overruns_fail_and_terminate(self):
        for changes in ({'memory_limit_hit':True},{'peak_memory_bytes':101},
                {'output_bytes':11},{'evidence_bytes':201},{'disposable_bytes':131}):
            with self.subTest(changes=changes):
                result,backend,boundary=self.run_backend([self.state(**changes)])
                self.assertEqual(result['status'],'FAIL');backend.terminate.assert_called_once()
                boundary.remove_owned_rule.assert_called_once()

    def test_unavailable_peak_is_null_not_zero(self):
        result,_,_=self.run_backend([self.state(active_processes=0,root_exited=True,
            exit_code=0,peak_memory_bytes=None)])
        self.assertIsNone(result['peak_memory_bytes'])
        self.assertFalse(self.events[0]['memory_measurement_available'])

    def test_nonzero_exit_and_missing_state_fail_closed(self):
        for state in ({},self.state(active_processes=0,root_exited=True,exit_code=1)):
            result,_,_=self.run_backend([state]);self.assertEqual(result['status'],'FAIL')

    def test_malformed_start_times_still_run_termination_and_recovery(self):
        result,backend,boundary=self.run_backend([],confirmed=False,child=float('nan'))
        self.assertEqual(result['status'],'FAIL');self.assertIsNone(result['elapsed_child_seconds'])
        backend.terminate.assert_called_once();boundary.retain_owned_rule_for_recovery.assert_called_once()

    def test_cleanup_failure_prevents_process_success(self):
        backend=Mock();backend.state.return_value=self.state(active_processes=0,root_exited=True,exit_code=0)
        boundary=Mock();boundary.remove_owned_rule.side_effect=RuntimeError('fixture')
        result=control.CohortSupervisor(self.policy,clock=lambda:0,pause=self.pause,emit=self.events.append).run(
            backend,boundary,outer_started=0,child_started=0,baseline_bytes=100)
        self.assertEqual(result['status'],'FAIL');backend.close.assert_called_once()

    def test_write_reservation_precedes_write_and_survives_partial_failure(self):
        budget=control.ByteBudget(4);sink=Mock(return_value=2)
        budget.write(b'ab',sink)
        with self.assertRaises(ValueError): budget.write(b'xyz',sink)
        self.assertEqual(sink.call_count,1)
        with self.assertRaises(IOError):budget.write(b'cd',lambda raw:1)
        self.assertEqual(budget.charged,4)

    def test_free_space_floor_is_pre_copy_check(self):
        control.check_free_space(resources=self.policy,free_bytes=20)
        for value in (None,True,19):
            with self.assertRaises(ValueError):control.check_free_space(resources=self.policy,free_bytes=value)

    def test_real_entry_stays_unconditionally_blocked(self):
        self.assertIs(control.COHORT_EXECUTION_ADMITTED,False)
        with unittest.mock.patch('sys.stdout',new=io.StringIO()): self.assertEqual(control.main(),2)

    def test_actual_stage_times_are_written_through_budget(self):
        sink=io.BytesIO();clock=Mock(side_effect=[10.0,12.5])
        telemetry=control.StageTelemetry(clock=clock,budget=control.ByteBudget(4096),sink=sink.write)
        with telemetry.measure('DENSE_BATCH',index=0):pass
        row=json.loads(sink.getvalue())
        self.assertEqual(row['elapsed_seconds'],2.5)
        self.assertTrue(row['timing_available'])

    def test_unavailable_stage_end_is_null_and_fails(self):
        sink=io.BytesIO();clock=Mock(side_effect=[10.0,float('nan')])
        telemetry=control.StageTelemetry(clock=clock,budget=control.ByteBudget(4096),sink=sink.write)
        with self.assertRaises(ValueError):
            with telemetry.measure('GRAPH_LOAD'):pass
        row=json.loads(sink.getvalue())
        self.assertFalse(row['timing_available']);self.assertIsNone(row['elapsed_seconds'])


if __name__=='__main__': unittest.main()
