"""
Forensic Financial Analyzer Module

Detects accounting irregularities, fraud indicators, and aggressive accounting tactics.
Implements multiple forensic analysis techniques including Benford's Law, quality of earnings,
revenue recognition red flags, and working capital manipulation detection.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal


# Benford's Law expected first-digit frequencies
BENFORD_EXPECTED = {
    '1': 0.301, '2': 0.176, '3': 0.125, '4': 0.097,
    '5': 0.079, '6': 0.067, '7': 0.058, '8': 0.051, '9': 0.046
}


def extract_first_digits(numbers: List[float]) -> List[str]:
    """Extract first significant digits from a list of numbers."""
    first_digits = []
    for num in numbers:
        if num and num > 0:
            # Convert to string, remove decimal point, find first non-zero digit
            num_str = str(abs(num)).replace('.', '').lstrip('0')
            if num_str and num_str[0].isdigit():
                first_digits.append(num_str[0])
    return first_digits


def benford_law_analysis(numbers: List[float], label: str = "Financial Figures") -> Dict[str, Any]:
    """
    Perform Benford's Law analysis on financial figures.
    
    Returns:
        - observed_distribution: Actual digit frequencies
        - expected_distribution: Benford's Law expected frequencies
        - chi_square_statistic: Statistical test result
        - p_value: Probability (approximation)
        - verdict: 'PASS', 'MONITOR', or 'RED_FLAG'
        - deviation_score: How far from expected (0-100)
    """
    if len(numbers) < 30:
        return {
            'label': label,
            'sample_size': len(numbers),
            'verdict': 'INSUFFICIENT_DATA',
            'message': 'Need at least 30 data points for Benford\'s Law analysis'
        }
    
    first_digits = extract_first_digits(numbers)
    if len(first_digits) < 30:
        return {
            'label': label,
            'sample_size': len(first_digits),
            'verdict': 'INSUFFICIENT_DATA',
            'message': 'Not enough valid numbers after filtering'
        }
    
    # Calculate observed frequencies
    digit_counts = Counter(first_digits)
    total = len(first_digits)
    observed = {d: digit_counts.get(d, 0) / total for d in '123456789'}
    
    # Chi-square test
    chi_square = 0.0
    max_deviation = 0.0
    deviations = {}
    
    for digit in '123456789':
        expected_freq = BENFORD_EXPECTED[digit]
        observed_freq = observed[digit]
        
        # Chi-square contribution
        expected_count = expected_freq * total
        observed_count = observed_freq * total
        if expected_count > 0:
            chi_square += ((observed_count - expected_count) ** 2) / expected_count
        
        # Track deviations
        deviation = abs(observed_freq - expected_freq)
        deviations[digit] = deviation
        max_deviation = max(max_deviation, deviation)
    
    # Rough p-value approximation (8 degrees of freedom)
    # Critical values: 15.51 (p=0.05), 20.09 (p=0.01)
    if chi_square < 15.51:
        verdict = 'PASS'
        risk_level = '🟢 Normal'
    elif chi_square < 20.09:
        verdict = 'MONITOR'
        risk_level = '🟡 Monitor'
    else:
        verdict = 'RED_FLAG'
        risk_level = '🔴 Red Flag'
    
    # Deviation score (0-100)
    deviation_score = min(100, (chi_square / 30.0) * 100)
    
    return {
        'label': label,
        'sample_size': total,
        'chi_square_statistic': round(chi_square, 2),
        'verdict': verdict,
        'risk_level': risk_level,
        'deviation_score': round(deviation_score, 1),
        'observed_distribution': {k: round(v, 3) for k, v in observed.items()},
        'expected_distribution': {k: round(v, 3) for k, v in BENFORD_EXPECTED.items()},
        'largest_deviations': sorted(deviations.items(), key=lambda x: x[1], reverse=True)[:3],
        'interpretation': _interpret_benford_result(chi_square, max_deviation)
    }


def _interpret_benford_result(chi_square: float, max_deviation: float) -> str:
    """Provide forensic interpretation of Benford's Law results."""
    if chi_square < 15.51:
        return "Distribution matches Benford's Law. No evidence of manipulation."
    elif chi_square < 20.09:
        return "Slight deviation from expected distribution. May warrant closer examination."
    else:
        return "Significant deviation from Benford's Law. Possible evidence of rounding, estimation errors, or intentional manipulation."


def revenue_quality_analysis(financial_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze revenue quality indicators:
    - Days Sales Outstanding (DSO) trends
    - Revenue growth vs. cash collection
    - Unbilled revenue accumulation
    """
    if len(financial_data) < 2:
        return {'verdict': 'INSUFFICIENT_DATA', 'message': 'Need at least 2 periods'}
    
    issues = []
    warnings = []
    metrics = []
    
    # Sort by fiscal year
    sorted_data = sorted(financial_data, key=lambda x: x.get('fiscal_year', 0))
    
    for i in range(len(sorted_data) - 1):
        current = sorted_data[i + 1]
        previous = sorted_data[i]
        
        fy_current = current.get('fiscal_year')
        fy_prev = previous.get('fiscal_year')
        
        # Revenue growth rate
        sales_current = current.get('sales', 0) or 0
        sales_prev = previous.get('sales', 0) or 0
        
        if sales_prev > 0:
            revenue_growth = ((sales_current - sales_prev) / sales_prev) * 100
            
            # Calculate DSO if receivables available
            receivables_current = current.get('receivables', 0) or 0
            receivables_prev = previous.get('receivables', 0) or 0
            
            if sales_current > 0:
                dso_current = (receivables_current / sales_current) * 365
                dso_prev = (receivables_prev / sales_prev) * 365 if sales_prev > 0 else 0
                dso_change = dso_current - dso_prev if dso_prev > 0 else 0
                
                metrics.append({
                    'fiscal_year': fy_current,
                    'revenue_growth_pct': round(revenue_growth, 2),
                    'dso_days': round(dso_current, 1),
                    'dso_change_days': round(dso_change, 1)
                })
                
                # Red flag: DSO growing faster than revenue
                if dso_change > 15 and revenue_growth > 0:
                    issues.append({
                        'type': 'DSO_SPIKE',
                        'severity': '🔴 Red Flag',
                        'year': fy_current,
                        'detail': f"DSO increased by {round(dso_change, 1)} days while revenue grew {round(revenue_growth, 1)}%. Possible channel stuffing or collection issues.",
                        'dso_days': round(dso_current, 1),
                        'revenue_growth': round(revenue_growth, 1)
                    })
                elif dso_change > 10:
                    warnings.append({
                        'type': 'DSO_INCREASE',
                        'severity': '🟡 Monitor',
                        'year': fy_current,
                        'detail': f"DSO increased by {round(dso_change, 1)} days to {round(dso_current, 1)} days.",
                        'dso_days': round(dso_current, 1)
                    })
    
    # Overall verdict
    if len(issues) > 0:
        verdict = 'RED_FLAG'
        risk_level = '🔴 Red Flag'
    elif len(warnings) > 0:
        verdict = 'MONITOR'
        risk_level = '🟡 Monitor'
    else:
        verdict = 'PASS'
        risk_level = '🟢 Normal'
    
    return {
        'verdict': verdict,
        'risk_level': risk_level,
        'issues': issues,
        'warnings': warnings,
        'metrics': metrics,
        'summary': f"Analyzed {len(sorted_data)} periods. Found {len(issues)} red flags and {len(warnings)} warnings."
    }


def cash_flow_quality_analysis(financial_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze quality of earnings by comparing accrual earnings to cash flows.
    High-quality earnings have strong cash flow backing.
    """
    if len(financial_data) < 1:
        return {'verdict': 'INSUFFICIENT_DATA'}
    
    issues = []
    warnings = []
    metrics = []
    
    for period in financial_data:
        fy = period.get('fiscal_year')
        net_profit = period.get('net_profit', 0) or 0
        operating_cash_flow = period.get('operating_cash_flow', 0) or 0
        
        if net_profit > 0 and operating_cash_flow is not None:
            # Cash flow to earnings ratio
            cf_to_earnings = (operating_cash_flow / net_profit) if net_profit != 0 else 0
            
            metrics.append({
                'fiscal_year': fy,
                'net_profit': round(net_profit, 2),
                'operating_cash_flow': round(operating_cash_flow, 2),
                'cf_to_earnings_ratio': round(cf_to_earnings, 2)
            })
            
            # Red flags
            if cf_to_earnings < 0.5:
                issues.append({
                    'type': 'LOW_CASH_CONVERSION',
                    'severity': '🔴 Red Flag',
                    'year': fy,
                    'detail': f"Operating cash flow ({round(operating_cash_flow, 1)} Cr) is only {round(cf_to_earnings * 100, 1)}% of net profit ({round(net_profit, 1)} Cr). Earnings may be of low quality.",
                    'ratio': round(cf_to_earnings, 2)
                })
            elif cf_to_earnings < 0.8:
                warnings.append({
                    'type': 'MODERATE_CASH_CONVERSION',
                    'severity': '🟡 Monitor',
                    'year': fy,
                    'detail': f"Cash flow to earnings ratio is {round(cf_to_earnings, 2)}. Ideal is > 0.8.",
                    'ratio': round(cf_to_earnings, 2)
                })
    
    # Verdict
    if len(issues) > 0:
        verdict = 'RED_FLAG'
        risk_level = '🔴 Red Flag'
    elif len(warnings) > 0:
        verdict = 'MONITOR'
        risk_level = '🟡 Monitor'
    else:
        verdict = 'PASS'
        risk_level = '🟢 Normal'
    
    return {
        'verdict': verdict,
        'risk_level': risk_level,
        'issues': issues,
        'warnings': warnings,
        'metrics': metrics,
        'summary': f"Analyzed {len(metrics)} periods. Cash-to-earnings conversion quality assessed."
    }


def working_capital_manipulation_check(financial_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect working capital manipulation indicators:
    - Sudden inventory buildup relative to sales
    - Receivables growth exceeding revenue growth
    - Payables stretching patterns
    """
    if len(financial_data) < 2:
        return {'verdict': 'INSUFFICIENT_DATA', 'message': 'Need at least 2 periods'}
    
    issues = []
    warnings = []
    metrics = []
    
    sorted_data = sorted(financial_data, key=lambda x: x.get('fiscal_year', 0))
    
    for i in range(len(sorted_data) - 1):
        current = sorted_data[i + 1]
        previous = sorted_data[i]
        
        fy = current.get('fiscal_year')
        
        # Get metrics
        sales_current = current.get('sales', 0) or 0
        sales_prev = previous.get('sales', 0) or 0
        
        inventory_current = current.get('inventory', 0) or 0
        inventory_prev = previous.get('inventory', 0) or 0
        
        receivables_current = current.get('receivables', 0) or 0
        receivables_prev = previous.get('receivables', 0) or 0
        
        if sales_prev > 0 and sales_current > 0:
            revenue_growth = ((sales_current - sales_prev) / sales_prev) * 100
            
            # Inventory growth
            if inventory_prev > 0:
                inventory_growth = ((inventory_current - inventory_prev) / inventory_prev) * 100
                
                metrics.append({
                    'fiscal_year': fy,
                    'revenue_growth_pct': round(revenue_growth, 2),
                    'inventory_growth_pct': round(inventory_growth, 2),
                    'inventory_to_sales_ratio': round((inventory_current / sales_current) * 100, 2)
                })
                
                # Red flag: Inventory growing much faster than sales
                if inventory_growth > revenue_growth + 20:
                    issues.append({
                        'type': 'INVENTORY_BUILDUP',
                        'severity': '🔴 Red Flag',
                        'year': fy,
                        'detail': f"Inventory grew {round(inventory_growth, 1)}% while revenue grew only {round(revenue_growth, 1)}%. Possible obsolescence or channel stuffing preparation.",
                        'inventory_growth': round(inventory_growth, 1),
                        'revenue_growth': round(revenue_growth, 1)
                    })
                elif inventory_growth > revenue_growth + 10:
                    warnings.append({
                        'type': 'INVENTORY_INCREASE',
                        'severity': '🟡 Monitor',
                        'year': fy,
                        'detail': f"Inventory growth ({round(inventory_growth, 1)}%) exceeds revenue growth ({round(revenue_growth, 1)}%).",
                        'inventory_growth': round(inventory_growth, 1)
                    })
            
            # Receivables growth
            if receivables_prev > 0:
                receivables_growth = ((receivables_current - receivables_prev) / receivables_prev) * 100
                
                if receivables_growth > revenue_growth + 15:
                    issues.append({
                        'type': 'RECEIVABLES_SPIKE',
                        'severity': '🔴 Red Flag',
                        'year': fy,
                        'detail': f"Receivables grew {round(receivables_growth, 1)}% while revenue grew {round(revenue_growth, 1)}%. Collection issues or aggressive revenue recognition.",
                        'receivables_growth': round(receivables_growth, 1),
                        'revenue_growth': round(revenue_growth, 1)
                    })
    
    # Verdict
    if len(issues) > 0:
        verdict = 'RED_FLAG'
        risk_level = '🔴 Red Flag'
    elif len(warnings) > 0:
        verdict = 'MONITOR'
        risk_level = '🟡 Monitor'
    else:
        verdict = 'PASS'
        risk_level = '🟢 Normal'
    
    return {
        'verdict': verdict,
        'risk_level': risk_level,
        'issues': issues,
        'warnings': warnings,
        'metrics': metrics,
        'summary': f"Analyzed {len(sorted_data)} periods for working capital manipulation."
    }


def expense_capitalization_analysis(financial_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect aggressive expense capitalization:
    - Sudden changes in depreciation relative to fixed assets
    - Capital WIP accumulation
    - Maintenance capex vs. growth capex patterns
    """
    if len(financial_data) < 2:
        return {'verdict': 'INSUFFICIENT_DATA', 'message': 'Need at least 2 periods'}
    
    issues = []
    warnings = []
    metrics = []
    
    sorted_data = sorted(financial_data, key=lambda x: x.get('fiscal_year', 0))
    
    for i in range(len(sorted_data) - 1):
        current = sorted_data[i + 1]
        previous = sorted_data[i]
        
        fy = current.get('fiscal_year')
        
        depreciation_current = current.get('depreciation', 0) or 0
        depreciation_prev = previous.get('depreciation', 0) or 0
        
        fixed_assets_current = current.get('net_fixed_assets', 0) or 0
        fixed_assets_prev = previous.get('net_fixed_assets', 0) or 0
        
        capwip_current = current.get('capital_wip', 0) or 0
        capwip_prev = previous.get('capital_wip', 0) or 0
        
        if fixed_assets_current > 0 and fixed_assets_prev > 0:
            # Depreciation as % of fixed assets
            depr_rate_current = (depreciation_current / fixed_assets_current) * 100
            depr_rate_prev = (depreciation_prev / fixed_assets_prev) * 100
            
            depr_rate_change = depr_rate_current - depr_rate_prev
            
            metrics.append({
                'fiscal_year': fy,
                'depreciation_rate_pct': round(depr_rate_current, 2),
                'depreciation_rate_change': round(depr_rate_change, 2),
                'capwip_to_fixed_assets_pct': round((capwip_current / fixed_assets_current) * 100, 2) if fixed_assets_current > 0 else 0
            })
            
            # Red flag: Depreciation rate suddenly drops
            if depr_rate_change < -2.0:
                issues.append({
                    'type': 'DEPRECIATION_SLOWDOWN',
                    'severity': '🔴 Red Flag',
                    'year': fy,
                    'detail': f"Depreciation rate dropped from {round(depr_rate_prev, 2)}% to {round(depr_rate_current, 2)}%. Possible useful life extension or aggressive capitalization.",
                    'rate_change': round(depr_rate_change, 2)
                })
            
            # CAPWIP accumulation warning
            if capwip_current > 0 and fixed_assets_current > 0:
                capwip_ratio = (capwip_current / fixed_assets_current) * 100
                if capwip_ratio > 20:
                    warnings.append({
                        'type': 'CAPWIP_ACCUMULATION',
                        'severity': '🟡 Monitor',
                        'year': fy,
                        'detail': f"Capital WIP is {round(capwip_ratio, 1)}% of net fixed assets. Prolonged projects or delayed asset recognition.",
                        'capwip_ratio': round(capwip_ratio, 1)
                    })
    
    # Verdict
    if len(issues) > 0:
        verdict = 'RED_FLAG'
        risk_level = '🔴 Red Flag'
    elif len(warnings) > 0:
        verdict = 'MONITOR'
        risk_level = '🟡 Monitor'
    else:
        verdict = 'PASS'
        risk_level = '🟢 Normal'
    
    return {
        'verdict': verdict,
        'risk_level': risk_level,
        'issues': issues,
        'warnings': warnings,
        'metrics': metrics,
        'summary': f"Analyzed capitalization policies across {len(sorted_data)} periods."
    }


def comprehensive_forensic_analysis(financial_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run comprehensive forensic analysis combining all detection methods.
    
    Args:
        financial_data: List of dicts containing combined P&L, balance sheet, cash flow data
        
    Returns:
        Comprehensive forensic report with overall risk score
    """
    results = {
        'benford_law': None,
        'revenue_quality': None,
        'cash_flow_quality': None,
        'working_capital': None,
        'expense_capitalization': None,
        'overall_risk_score': 0,
        'overall_verdict': 'PASS',
        'critical_issues': [],
        'all_warnings': []
    }
    
    # Extract all numeric values for Benford's Law
    all_numbers = []
    for period in financial_data:
        for key, value in period.items():
            if isinstance(value, (int, float, Decimal)) and value and value > 0:
                all_numbers.append(float(value))
    
    if len(all_numbers) >= 30:
        results['benford_law'] = benford_law_analysis(all_numbers, "All Financial Figures")
    
    # Revenue quality analysis
    results['revenue_quality'] = revenue_quality_analysis(financial_data)
    
    # Cash flow quality
    results['cash_flow_quality'] = cash_flow_quality_analysis(financial_data)
    
    # Working capital manipulation
    results['working_capital'] = working_capital_manipulation_check(financial_data)
    
    # Expense capitalization
    results['expense_capitalization'] = expense_capitalization_analysis(financial_data)
    
    # Calculate overall risk score (0-100)
    risk_components = []
    
    for analysis_name, analysis_result in results.items():
        if analysis_name in ['overall_risk_score', 'overall_verdict', 'critical_issues', 'all_warnings']:
            continue
        
        if analysis_result and isinstance(analysis_result, dict):
            verdict = analysis_result.get('verdict', 'PASS')
            
            if verdict == 'RED_FLAG':
                risk_components.append(30)
                # Collect critical issues
                if 'issues' in analysis_result:
                    results['critical_issues'].extend(analysis_result['issues'])
            elif verdict == 'MONITOR':
                risk_components.append(15)
                # Collect warnings
                if 'warnings' in analysis_result:
                    results['all_warnings'].extend(analysis_result['warnings'])
            elif verdict == 'PASS':
                risk_components.append(0)
            
            # Benford's Law adds its deviation score
            if analysis_name == 'benford_law' and 'deviation_score' in analysis_result:
                risk_components.append(analysis_result['deviation_score'] * 0.3)
    
    # Overall risk score
    if risk_components:
        results['overall_risk_score'] = min(100, sum(risk_components))
    
    # Overall verdict
    if results['overall_risk_score'] >= 60:
        results['overall_verdict'] = 'HIGH_RISK'
        results['verdict_display'] = '🔴 High Risk'
    elif results['overall_risk_score'] >= 30:
        results['overall_verdict'] = 'MODERATE_RISK'
        results['verdict_display'] = '🟡 Moderate Risk'
    else:
        results['overall_verdict'] = 'LOW_RISK'
        results['verdict_display'] = '🟢 Low Risk'
    
    return results


def format_forensic_report(forensic_results: Dict[str, Any]) -> str:
    """Format forensic analysis results into a readable report."""
    lines = []
    
    lines.append("=" * 80)
    lines.append("FORENSIC FINANCIAL ANALYSIS REPORT")
    lines.append("=" * 80)
    lines.append("")
    
    # Overall summary
    lines.append(f"Overall Risk Assessment: {forensic_results['verdict_display']}")
    lines.append(f"Risk Score: {round(forensic_results['overall_risk_score'], 1)}/100")
    lines.append(f"Critical Issues Found: {len(forensic_results['critical_issues'])}")
    lines.append(f"Warnings: {len(forensic_results['all_warnings'])}")
    lines.append("")
    
    # Critical issues
    if forensic_results['critical_issues']:
        lines.append("🔴 CRITICAL ISSUES:")
        lines.append("-" * 80)
        for issue in forensic_results['critical_issues']:
            lines.append(f"\n{issue['severity']} {issue['type']} (FY{issue.get('year', 'N/A')})")
            lines.append(f"  {issue['detail']}")
        lines.append("")
    
    # Benford's Law
    if forensic_results['benford_law']:
        bl = forensic_results['benford_law']
        if bl.get('verdict') != 'INSUFFICIENT_DATA':
            lines.append("📊 BENFORD'S LAW ANALYSIS:")
            lines.append("-" * 80)
            lines.append(f"Sample Size: {bl['sample_size']} figures")
            lines.append(f"Chi-Square Statistic: {bl['chi_square_statistic']}")
            lines.append(f"Verdict: {bl['risk_level']}")
            lines.append(f"Interpretation: {bl['interpretation']}")
            lines.append("")
    
    # Revenue quality
    if forensic_results['revenue_quality']:
        rq = forensic_results['revenue_quality']
        if rq.get('verdict') != 'INSUFFICIENT_DATA':
            lines.append("💰 REVENUE QUALITY ANALYSIS:")
            lines.append("-" * 80)
            lines.append(f"Verdict: {rq['risk_level']}")
            lines.append(f"{rq['summary']}")
            lines.append("")
    
    # Cash flow quality
    if forensic_results['cash_flow_quality']:
        cf = forensic_results['cash_flow_quality']
        if cf.get('verdict') != 'INSUFFICIENT_DATA':
            lines.append("💵 CASH FLOW QUALITY ANALYSIS:")
            lines.append("-" * 80)
            lines.append(f"Verdict: {cf['risk_level']}")
            lines.append(f"{cf['summary']}")
            lines.append("")
    
    # Working capital
    if forensic_results['working_capital']:
        wc = forensic_results['working_capital']
        if wc.get('verdict') != 'INSUFFICIENT_DATA':
            lines.append("📦 WORKING CAPITAL MANIPULATION CHECK:")
            lines.append("-" * 80)
            lines.append(f"Verdict: {wc['risk_level']}")
            lines.append(f"{wc['summary']}")
            lines.append("")
    
    # Warnings summary
    if forensic_results['all_warnings']:
        lines.append("🟡 WARNINGS REQUIRING MONITORING:")
        lines.append("-" * 80)
        for warning in forensic_results['all_warnings'][:5]:  # Top 5
            lines.append(f"  • {warning['type']} (FY{warning.get('year', 'N/A')}): {warning['detail']}")
        lines.append("")
    
    lines.append("=" * 80)
    lines.append("END OF FORENSIC ANALYSIS")
    lines.append("=" * 80)
    
    return "\n".join(lines)
