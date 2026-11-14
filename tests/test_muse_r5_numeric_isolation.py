"""Independent regressions through the documented evaluate() entry point."""
from __future__ import annotations
import copy
from decimal import (Context, DecimalException, DefaultContext, Inexact,
                     ROUND_UP, ROUND_DOWN, localcontext)
from fractions import Fraction
import random
import unittest
from muse_presets.specialist_extensions import evaluate


CAPACITY = {'demand_rps':'900','per_instance_rps':'250','target_utilization':'0.6',
            'instances':4,'reserve_instances':1}
SLO = {'good_events':2,'total_events':3,'target':'0.9','window_minutes':60}


class NumericIsolationTests(unittest.TestCase):
    def safe_evaluate(self, name, data):
        try:
            return evaluate(name, data)
        except DecimalException as exc:
            self.fail(f'Valid public input depended on ambient Decimal policy: {type(exc).__name__}')

    def test_repeating_ratios_ignore_host_inexact_trap(self):
        expected=evaluate('service-objectives',SLO)
        with localcontext() as context:
            context.traps[Inexact]=True
            self.assertEqual(self.safe_evaluate('service-objectives',SLO),expected)

    def test_capacity_division_ignores_host_inexact_trap(self):
        data={**CAPACITY,'demand_rps':'1','per_instance_rps':'3','target_utilization':'1'}
        expected=evaluate('capacity-planning',data)
        with localcontext() as context:
            context.traps[Inexact]=True
            self.assertEqual(self.safe_evaluate('capacity-planning',data),expected)

    def test_repeatable_ratio_text_ignores_host_rounding(self):
        expected=evaluate('service-objectives',SLO)
        for mode in (ROUND_UP,ROUND_DOWN):
            with self.subTest(mode=mode), localcontext() as context:
                context.rounding=mode
                self.assertEqual(self.safe_evaluate('service-objectives',SLO),expected)

    def test_capacity_ignores_host_exponent_limits(self):
        data={**CAPACITY,'demand_rps':'1000000'}
        expected=evaluate('capacity-planning',data)
        with localcontext() as context:
            context.Emin=-2;context.Emax=2;context.clamp=1
            self.assertEqual(self.safe_evaluate('capacity-planning',data),expected)

    def test_default_context_mutation_does_not_change_tool_policy(self):
        expected=evaluate('service-objectives',SLO)
        original=DefaultContext.copy()
        try:
            DefaultContext.rounding=ROUND_UP
            DefaultContext.traps[Inexact]=True
            with localcontext() as context:
                context.traps[Inexact]=True
                context.rounding=ROUND_DOWN
                self.assertEqual(self.safe_evaluate('service-objectives',SLO),expected)
        finally:
            for name in ('prec','rounding','Emin','Emax','capitals','clamp'):
                setattr(DefaultContext,name,getattr(original,name))
            DefaultContext.flags=dict(original.flags)
            DefaultContext.traps=dict(original.traps)

    def test_host_context_and_input_are_preserved(self):
        source=copy.deepcopy(CAPACITY)
        with localcontext(Context(prec=3,rounding=ROUND_UP,Emax=7)) as context:
            before=(context.prec,context.rounding,context.Emax,dict(context.flags),dict(context.traps))
            self.safe_evaluate('capacity-planning',source)
            after=(context.prec,context.rounding,context.Emax,dict(context.flags),dict(context.traps))
            self.assertEqual(after,before)
        self.assertEqual(source,CAPACITY)

    def test_existing_public_precision_guard_already_covers_upper_boundary(self):
        result=evaluate('capacity-planning',dict(demand_rps='1000000000000',
            per_instance_rps='999999999999.999999999999999999',
            target_utilization='1',instances=0,reserve_instances=0))
        self.assertEqual(result['required_serving_instances'],2)

    def test_public_capacity_matches_600_exact_rational_decisions(self):
        rng=random.Random(10275)
        def fixed(i):return f'{i//10**18}.{i%10**18:018d}'
        for case in range(600):
            n=rng.choice((1,2,3,7,10,999,99999))
            units=rng.randrange(10**21,10**30//n)
            demand=units*n+rng.choice((-1,0,1))
            inputs={**CAPACITY,'demand_rps':fixed(demand),'per_instance_rps':fixed(units),
                    'target_utilization':'1','reserve_instances':0,'instances':0}
            ratio=Fraction(inputs['demand_rps'])/Fraction(inputs['per_instance_rps'])
            expected=-(-ratio.numerator//ratio.denominator)
            with self.subTest(case=case):
                self.assertEqual(evaluate('capacity-planning',inputs)['required_instances'],expected)

    def test_no_traffic_and_result_limit_remain_enforced(self):
        self.assertEqual(evaluate('service-objectives',{**SLO,'good_events':0,'total_events':0})['status'],'no_traffic')
        with self.assertRaises(ValueError):
            evaluate('capacity-planning',{**CAPACITY,'demand_rps':'1000000000000',
                'per_instance_rps':'0.000000000000000001'})


class ExactThresholdTests(unittest.TestCase):
    def audit(self,minimum,foreground='#000000',background='#000000'):
        return evaluate('design-token-audit',{'tokens':{'ink':foreground,'paper':background},
            'pairs':[{'id':'text','foreground':'ink','background':'paper','minimum_ratio':minimum}]})

    def test_accepted_decimal_threshold_is_not_rounded_down_to_pass(self):
        result=self.audit('1.000000000000000001')
        self.assertEqual(result['status'],'fail')
        self.assertFalse(result['pairs'][0]['passed'])

    def test_exact_threshold_equality_is_still_accepted(self):
        self.assertTrue(self.audit('1')['pairs'][0]['passed'])
        self.assertTrue(self.audit('21','#000000','#ffffff')['pairs'][0]['passed'])

    def test_ordinary_color_examples_unchanged(self):
        result=self.audit('4.5','#000000','#ffffff')
        self.assertEqual(result['pairs'][0]['ratio'],21.0)
        self.assertFalse(result['conformance_certified'])
        self.assertFalse(result['rendered_ui_inspected'])
        self.assertEqual(self.audit('4.5','#aaaaaa','#ffffff')['status'],'fail')

    def test_bad_threshold_types_remain_refused(self):
        for value in (True,'NaN','21.000000000000000001','0.9',4.5):
            with self.subTest(value=value),self.assertRaises(ValueError):self.audit(value)

if __name__=='__main__':unittest.main()
