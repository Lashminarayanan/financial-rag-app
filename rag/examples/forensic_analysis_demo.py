"""
Example script demonstrating Forensic Financial Analyzer usage

This script shows how to run forensic analysis directly or test individual components.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.financial_repository import query_comprehensive_forensic_data
from app.forensic_analyzer import (
    comprehensive_forensic_analysis,
    format_forensic_report,
    benford_law_analysis,
    revenue_quality_analysis,
    cash_flow_quality_analysis
)


def example_comprehensive_analysis():
    """
    Example: Run full forensic analysis on Eicher Motors
    """
    print("=" * 80)
    print("COMPREHENSIVE FORENSIC ANALYSIS - EICHER MOTORS")
    print("=" * 80)
    print()
    
    # Fetch comprehensive financial data
    print("[1/3] Fetching comprehensive financial data...")
    financial_data = query_comprehensive_forensic_data(
        company_ticker='EICHERMOT',
        limit=10
    )
    
    print(f"      Retrieved {len(financial_data)} years of data")
    print()
    
    # Run forensic analysis
    print("[2/3] Running forensic analysis...")
    forensic_results = comprehensive_forensic_analysis(financial_data)
    
    print(f"      Overall Risk Score: {forensic_results['overall_risk_score']:.1f}/100")
    print(f"      Verdict: {forensic_results['verdict_display']}")
    print()
    
    # Display formatted report
    print("[3/3] Generating forensic report...")
    print()
    report = format_forensic_report(forensic_results)
    print(report)
    
    return forensic_results


def example_benford_law():
    """
    Example: Test Benford's Law on sample financial figures
    """
    print("\n" + "=" * 80)
    print("BENFORD'S LAW ANALYSIS - SAMPLE DATA")
    print("=" * 80)
    print()
    
    # Fetch data
    financial_data = query_comprehensive_forensic_data(company_ticker='EICHERMOT', limit=10)
    
    # Extract all numeric values
    all_numbers = []
    for period in financial_data:
        for key, value in period.items():
            if isinstance(value, (int, float)) and value and value > 0:
                all_numbers.append(float(value))
    
    print(f"Analyzing {len(all_numbers)} financial figures...")
    print()
    
    # Run Benford's Law analysis
    results = benford_law_analysis(all_numbers, "All Financial Metrics")
    
    # Display results
    print(f"Sample Size: {results['sample_size']}")
    print(f"Chi-Square Statistic: {results['chi_square_statistic']}")
    print(f"Verdict: {results['risk_level']}")
    print(f"Deviation Score: {results['deviation_score']}/100")
    print()
    print(f"Interpretation: {results['interpretation']}")
    print()
    
    print("Top 3 Digit Deviations:")
    for digit, deviation in results['largest_deviations']:
        expected = results['expected_distribution'][digit]
        observed = results['observed_distribution'][digit]
        print(f"  Digit {digit}: Expected {expected:.3f}, Observed {observed:.3f}, Deviation: {deviation:.3f}")
    
    return results


def example_revenue_quality():
    """
    Example: Analyze revenue quality metrics
    """
    print("\n" + "=" * 80)
    print("REVENUE QUALITY ANALYSIS")
    print("=" * 80)
    print()
    
    financial_data = query_comprehensive_forensic_data(company_ticker='EICHERMOT', limit=5)
    
    print(f"Analyzing {len(financial_data)} years of revenue data...")
    print()
    
    results = revenue_quality_analysis(financial_data)
    
    print(f"Verdict: {results['risk_level']}")
    print(f"{results['summary']}")
    print()
    
    if results.get('metrics'):
        print("Metrics by Year:")
        print("-" * 80)
        for metric in results['metrics']:
            print(f"  FY{metric['fiscal_year']}:")
            print(f"    Revenue Growth: {metric['revenue_growth_pct']:.2f}%")
            print(f"    DSO: {metric['dso_days']:.1f} days (Change: {metric['dso_change_days']:+.1f} days)")
        print()
    
    if results.get('issues'):
        print("🔴 CRITICAL ISSUES:")
        for issue in results['issues']:
            print(f"  • {issue['detail']}")
        print()
    
    if results.get('warnings'):
        print("🟡 WARNINGS:")
        for warning in results['warnings']:
            print(f"  • {warning['detail']}")
    
    return results


def example_cash_flow_quality():
    """
    Example: Analyze cash flow quality
    """
    print("\n" + "=" * 80)
    print("CASH FLOW QUALITY ANALYSIS")
    print("=" * 80)
    print()
    
    financial_data = query_comprehensive_forensic_data(company_ticker='EICHERMOT', limit=5)
    
    print(f"Analyzing {len(financial_data)} years of cash flow data...")
    print()
    
    results = cash_flow_quality_analysis(financial_data)
    
    print(f"Verdict: {results['risk_level']}")
    print(f"{results['summary']}")
    print()
    
    if results.get('metrics'):
        print("Cash-to-Earnings Ratio by Year:")
        print("-" * 80)
        for metric in results['metrics']:
            print(f"  FY{metric['fiscal_year']}:")
            print(f"    Net Profit: ₹{metric['net_profit']:.2f} Cr")
            print(f"    Operating Cash Flow: ₹{metric['operating_cash_flow']:.2f} Cr")
            print(f"    Ratio: {metric['cf_to_earnings_ratio']:.2f}x")
        print()
    
    if results.get('issues'):
        print("🔴 CRITICAL ISSUES:")
        for issue in results['issues']:
            print(f"  • {issue['detail']}")
    
    return results


def main():
    """
    Run all examples
    """
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "FORENSIC FINANCIAL ANALYZER - EXAMPLES" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")
    
    try:
        # Example 1: Comprehensive analysis
        comprehensive_results = example_comprehensive_analysis()
        
        # Example 2: Benford's Law
        benford_results = example_benford_law()
        
        # Example 3: Revenue quality
        revenue_results = example_revenue_quality()
        
        # Example 4: Cash flow quality
        cashflow_results = example_cash_flow_quality()
        
        print("\n" + "=" * 80)
        print("EXAMPLES COMPLETED SUCCESSFULLY ✓")
        print("=" * 80)
        print()
        print(f"Overall Forensic Risk Score: {comprehensive_results['overall_risk_score']:.1f}/100")
        print(f"Overall Verdict: {comprehensive_results['verdict_display']}")
        print()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
