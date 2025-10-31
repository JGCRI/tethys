"""
Test script to verify dynamic population functionality in Tethys.

This script compares outputs from two scenarios:
1. Static population: Uses only base year (2010) population for all years
2. Dynamic population: Uses multiple years (2010, 2020) with interpolation

The comparison demonstrates whether dynamic population is working correctly.
"""

import os
import yaml
import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path

import tethys
from tethys.model import Tethys


class DynamicPopulationTest:
    """Test framework for comparing static vs dynamic population scenarios."""
    
    def __init__(self, test_data_dir=None):
        """
        Initialize the test framework.
        
        :param test_data_dir: Path to test data directory. If None, uses default test data location.
        """
        if test_data_dir is None:
            self.test_data_dir = Path(__file__).parent / 'data'
        else:
            self.test_data_dir = Path(test_data_dir)
        
        self.base_config = None
        self.static_config_path = None
        self.dynamic_config_path = None
        self.static_csv_path = None
        self.dynamic_csv_path = None
        self.static_results = None
        self.dynamic_results = None
        
    def _load_base_config(self):
        """Load the base test configuration."""
        config_file = self.test_data_dir / 'config_test.yml'
        with open(config_file, 'r') as f:
            self.base_config = yaml.safe_load(f)
    
    def _create_extended_csv(self, years):
        """Create an extended CSV file with data for all specified years."""
        # Load original CSV
        original_csv = self.test_data_dir / 'data.csv'
        df = pd.read_csv(original_csv)
        
        # Get unique regions and sectors
        regions = df['region'].unique()
        sectors = df['sector'].unique()
        
        # Create extended data with all years
        extended_rows = []
        for region in regions:
            for sector in sectors:
                region_sector_data = df[(df['region'] == region) & (df['sector'] == sector)].sort_values('year')
                
                if len(region_sector_data) > 0:
                    # Interpolate/extrapolate for missing years
                    existing_years = region_sector_data['year'].values
                    existing_values = region_sector_data['value'].values
                    
                    for year in years:
                        if year in existing_years:
                            # Use existing value
                            value = float(region_sector_data[region_sector_data['year'] == year]['value'].iloc[0])
                        else:
                            # Linear interpolation/extrapolation
                            if year < existing_years[0]:
                                # Extrapolate backward
                                value = existing_values[0]
                            elif year > existing_years[-1]:
                                # Extrapolate forward (linear trend)
                                if len(existing_years) >= 2:
                                    # Use last two points for trend
                                    slope = (existing_values[-1] - existing_values[-2]) / (existing_years[-1] - existing_years[-2])
                                    value = existing_values[-1] + slope * (year - existing_years[-1])
                                else:
                                    value = existing_values[-1]
                            else:
                                # Interpolate between existing years
                                idx = np.searchsorted(existing_years, year)
                                y1, y2 = existing_years[idx-1], existing_years[idx]
                                v1, v2 = existing_values[idx-1], existing_values[idx]
                                if y2 != y1:
                                    value = v1 + (v2 - v1) * (year - y1) / (y2 - y1)
                                else:
                                    value = v1
                        
                        extended_rows.append({
                            'region': region,
                            'sector': sector,
                            'year': year,
                            'value': value
                        })
        
        extended_df = pd.DataFrame(extended_rows)
        return extended_df
    
    def _create_static_config(self):
        """Create a configuration file for static population scenario."""
        # Create config file in test data directory so relative paths work
        self.static_config_path = self.test_data_dir / 'config_static_temp.yml'
        self.static_csv_path = self.test_data_dir / 'data_static_temp.csv'
        
        # Create extended CSV with all years
        extended_df = self._create_extended_csv([2010, 2015, 2020, 2025, 2030])
        extended_df.to_csv(self.static_csv_path, index=False)
        
        # Copy base config and modify for static population
        config = self.base_config.copy()
        config['years'] = [2010, 2015, 2020, 2025, 2030]  # Multiple years to test
        config['csv'] = str(self.static_csv_path.name)  # Use extended CSV
        config['proxy_files'] = {
            'population_{year}.tif': {
                'variables': 'Population',
                'years': [2010]  # Only base year
            }
        }
        
        with open(self.static_config_path, 'w') as f:
            yaml.dump(config, f)
        
        return str(self.static_config_path)
    
    def _create_dynamic_config(self):
        """Create a configuration file for dynamic population scenario."""
        self.dynamic_config_path = self.test_data_dir / 'config_dynamic_temp.yml'
        self.dynamic_csv_path = self.test_data_dir / 'data_dynamic_temp.csv'
        
        # Create extended CSV with all years
        extended_df = self._create_extended_csv([2010, 2015, 2020, 2025, 2030])
        extended_df.to_csv(self.dynamic_csv_path, index=False)
        
        # Copy base config and modify for dynamic population
        config = self.base_config.copy()
        config['years'] = [2010, 2015, 2020, 2025, 2030]  # Multiple years to test
        config['csv'] = str(self.dynamic_csv_path.name)  # Use extended CSV
        config['proxy_files'] = {
            'population_{year}.tif': {
                'variables': 'Population',
                'years': [2010, 2020]  # Multiple years for interpolation (2030 will use 2020 as nearest endpoint)
            }
        }
        
        with open(self.dynamic_config_path, 'w') as f:
            yaml.dump(config, f)
        
        return str(self.dynamic_config_path)
    
    def run_static_scenario(self):
        """Run Tethys with static population configuration."""
        print("=" * 70)
        print("Running STATIC population scenario (only 2010 population)")
        print("=" * 70)
        
        if self.static_config_path is None:
            self._create_static_config()
        
        # Use absolute path for config file
        config_path = os.path.abspath(self.static_config_path)
        model = Tethys(config_file=config_path)
        model.run_model()
        self.static_results = model.outputs
        
        print("Static scenario completed.\n")
        return self.static_results
    
    def run_dynamic_scenario(self):
        """Run Tethys with dynamic population configuration."""
        print("=" * 70)
        print("Running DYNAMIC population scenario (2010 and 2020 population)")
        print("=" * 70)
        
        if self.dynamic_config_path is None:
            self._create_dynamic_config()
        
        # Use absolute path for config file
        config_path = os.path.abspath(self.dynamic_config_path)
        model = Tethys(config_file=config_path)
        model.run_model()
        self.dynamic_results = model.outputs
        
        print("Dynamic scenario completed.\n")
        return self.dynamic_results
    
    def compare_outputs(self):
        """Compare outputs from static and dynamic scenarios."""
        if self.static_results is None or self.dynamic_results is None:
            raise ValueError("Both scenarios must be run before comparison.")
        
        print("=" * 70)
        print("COMPARING STATIC vs DYNAMIC POPULATION OUTPUTS")
        print("=" * 70)
        
        # Get the Municipal sector output (should use Population proxy)
        sector = 'Municipal'
        
        if sector not in self.static_results.data_vars:
            # Try to find the sector in the outputs
            available_sectors = list(self.static_results.data_vars.keys())
            if available_sectors:
                sector = available_sectors[0]
                print(f"Warning: 'Municipal' not found, using '{sector}' instead.")
            else:
                raise ValueError("No sectors found in outputs.")
        
        static_da = self.static_results[sector]
        dynamic_da = self.dynamic_results[sector]
        
        # Ensure same coordinates
        static_da = static_da.reindex_like(dynamic_da, fill_value=0)
        
        # Calculate differences
        diff = dynamic_da - static_da
        abs_diff = np.abs(diff)
        
        # Calculate statistics per year
        years = static_da.year.values if hasattr(static_da, 'year') else None
        
        comparison_stats = {}
        
        if years is not None:
            for year in years:
                static_year = static_da.sel(year=year, drop=True)
                dynamic_year = dynamic_da.sel(year=year, drop=True)
                diff_year = diff.sel(year=year, drop=True)
                abs_diff_year = abs_diff.sel(year=year, drop=True)
                
                # Calculate totals
                static_total = float(static_year.sum().values)
                dynamic_total = float(dynamic_year.sum().values)
                
                # Calculate differences
                total_diff = float(diff_year.sum().values)
                total_abs_diff = float(abs_diff_year.sum().values)
                max_abs_diff = float(abs_diff_year.max().values)
                mean_abs_diff = float(abs_diff_year.mean().values)
                
                # Calculate relative difference
                if static_total != 0:
                    rel_diff_pct = (total_diff / static_total) * 100
                else:
                    rel_diff_pct = np.nan
                
                comparison_stats[int(year)] = {
                    'static_total': static_total,
                    'dynamic_total': dynamic_total,
                    'total_difference': total_diff,
                    'total_abs_difference': total_abs_diff,
                    'max_abs_difference': max_abs_diff,
                    'mean_abs_difference': mean_abs_diff,
                    'relative_difference_pct': rel_diff_pct
                }
        
        return comparison_stats, diff, abs_diff
    
    def generate_report(self, comparison_stats, diff, abs_diff, output_file=None):
        """Generate a detailed comparison report."""
        print("\n" + "=" * 70)
        print("COMPARISON REPORT: STATIC vs DYNAMIC POPULATION")
        print("=" * 70)
        
        # Summary table
        print("\nSUMMARY STATISTICS BY YEAR:")
        print("-" * 70)
        print(f"{'Year':<8} {'Static Total':<15} {'Dynamic Total':<15} {'Difference':<15} {'Rel Diff %':<12}")
        print("-" * 70)
        
        for year in sorted(comparison_stats.keys()):
            stats = comparison_stats[year]
            print(f"{year:<8} {stats['static_total']:<15.2f} {stats['dynamic_total']:<15.2f} "
                  f"{stats['total_difference']:<15.2f} {stats['relative_difference_pct']:<12.2f}")
        
        print("-" * 70)
        
        # Detailed statistics
        print("\nDETAILED STATISTICS:")
        print("-" * 70)
        for year in sorted(comparison_stats.keys()):
            stats = comparison_stats[year]
            print(f"\nYear {year}:")
            print(f"  Total difference: {stats['total_difference']:.6f}")
            print(f"  Total absolute difference: {stats['total_abs_difference']:.6f}")
            print(f"  Maximum absolute difference: {stats['max_abs_difference']:.6f}")
            print(f"  Mean absolute difference: {stats['mean_abs_difference']:.6f}")
            print(f"  Relative difference: {stats['relative_difference_pct']:.2f}%")
        
        # Validation checks
        print("\n" + "=" * 70)
        print("VALIDATION CHECKS:")
        print("=" * 70)
        
        validation_results = {}
        
        # Check 1: 2010 should be identical (baseline year)
        if 2010 in comparison_stats:
            diff_2010 = abs(comparison_stats[2010]['total_difference'])
            if diff_2010 < 1e-6:
                print("✓ PASS: Year 2010 outputs are identical (baseline year)")
                validation_results['baseline_identical'] = True
            else:
                print(f"✗ FAIL: Year 2010 outputs differ by {diff_2010:.6f}")
                validation_results['baseline_identical'] = False
        
        # Check 2: 2015 should differ (interpolation test)
        if 2015 in comparison_stats:
            diff_2015 = abs(comparison_stats[2015]['total_difference'])
            if diff_2015 > 1e-6:
                print(f"✓ PASS: Year 2015 outputs differ by {diff_2015:.6f} (interpolation working)")
                validation_results['interpolation_working'] = True
            else:
                print(f"✗ FAIL: Year 2015 outputs are identical (interpolation may not be working)")
                validation_results['interpolation_working'] = False
        
        # Check 3: 2020 should differ (future year test)
        if 2020 in comparison_stats:
            diff_2020 = abs(comparison_stats[2020]['total_difference'])
            if diff_2020 > 1e-6:
                print(f"✓ PASS: Year 2020 outputs differ by {diff_2020:.6f} (future year being used)")
                validation_results['future_year_used'] = True
            else:
                print(f"✗ FAIL: Year 2020 outputs are identical (future year may not be used)")
                validation_results['future_year_used'] = False
        
        # Check 4: 2025 should differ (will use 2020 as nearest endpoint since no 2030 data)
        if 2025 in comparison_stats:
            diff_2025 = abs(comparison_stats[2025]['total_difference'])
            if diff_2025 > 1e-6:
                print(f"✓ PASS: Year 2025 outputs differ by {diff_2025:.6f} (using 2020 as nearest endpoint)")
                validation_results['interpolation_2025_working'] = True
            else:
                print(f"✗ FAIL: Year 2025 outputs are identical (may not be using 2020 endpoint)")
                validation_results['interpolation_2025_working'] = False
        
        # Check 5: 2030 should differ (will use 2020 as nearest endpoint since no 2030 data)
        if 2030 in comparison_stats:
            diff_2030 = abs(comparison_stats[2030]['total_difference'])
            if diff_2030 > 1e-6:
                print(f"✓ PASS: Year 2030 outputs differ by {diff_2030:.6f} (using 2020 as nearest endpoint)")
                validation_results['extended_future_year_used'] = True
            else:
                print(f"✗ FAIL: Year 2030 outputs are identical (may not be using 2020 endpoint)")
                validation_results['extended_future_year_used'] = False
        
        # Overall assessment
        print("\n" + "=" * 70)
        print("OVERALL ASSESSMENT:")
        print("=" * 70)
        
        if all(validation_results.values()):
            print("✓✓✓ DYNAMIC POPULATION IS WORKING CORRECTLY ✓✓✓")
            print("   - Baseline year (2010) is identical")
            print("   - Interpolated year (2015) shows differences")
            print("   - Future year (2020) shows differences")
            print("   - Extended interpolated year (2025) shows differences")
            print("   - Extended future year (2030) shows differences")
        else:
            failed_checks = [k for k, v in validation_results.items() if not v]
            print("✗✗✗ DYNAMIC POPULATION MAY NOT BE WORKING AS EXPECTED ✗✗✗")
            print(f"   Failed checks: {', '.join(failed_checks)}")
        
        # Save to file if requested
        if output_file:
            self._save_report_to_file(comparison_stats, validation_results, output_file)
        
        return validation_results
    
    def _save_report_to_file(self, comparison_stats, validation_results, output_file):
        """Save comparison report to a file."""
        with open(output_file, 'w') as f:
            f.write("DYNAMIC POPULATION TEST REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write("SUMMARY STATISTICS BY YEAR:\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'Year':<8} {'Static Total':<15} {'Dynamic Total':<15} {'Difference':<15} {'Rel Diff %':<12}\n")
            f.write("-" * 70 + "\n")
            
            for year in sorted(comparison_stats.keys()):
                stats = comparison_stats[year]
                f.write(f"{year:<8} {stats['static_total']:<15.2f} {stats['dynamic_total']:<15.2f} "
                       f"{stats['total_difference']:<15.2f} {stats['relative_difference_pct']:<12.2f}\n")
            
            f.write("\nVALIDATION RESULTS:\n")
            f.write("-" * 70 + "\n")
            for check, result in validation_results.items():
                f.write(f"{check}: {'PASS' if result else 'FAIL'}\n")
        
        print(f"\nReport saved to: {output_file}")
    
    def cleanup(self):
        """Clean up temporary config and CSV files."""
        files_to_remove = [
            self.static_config_path,
            self.dynamic_config_path,
            self.static_csv_path,
            self.dynamic_csv_path
        ]
        
        removed = False
        for file_path in files_to_remove:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                removed = True
        
        if removed:
            print("Cleaned up temporary config and CSV files.")


def main():
    """Main function to run the dynamic population test."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test dynamic population functionality in Tethys')
    parser.add_argument('--test-data-dir', type=str, default=None,
                       help='Path to test data directory (default: tests/data)')
    parser.add_argument('--output-report', type=str, default=None,
                       help='Path to save comparison report (optional)')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Keep temporary files after test')
    
    args = parser.parse_args()
    
    # Initialize test framework
    test = DynamicPopulationTest(test_data_dir=args.test_data_dir)
    
    try:
        # Load base config
        test._load_base_config()
        
        # Create config files
        test._create_static_config()
        test._create_dynamic_config()
        
        # Run both scenarios
        test.run_static_scenario()
        test.run_dynamic_scenario()
        
        # Compare outputs
        comparison_stats, diff, abs_diff = test.compare_outputs()
        
        # Generate report
        validation_results = test.generate_report(comparison_stats, diff, abs_diff, 
                                                  output_file=args.output_report)
        
        # Return exit code based on validation
        if all(validation_results.values()):
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if not args.no_cleanup:
            test.cleanup()


if __name__ == '__main__':
    import sys
    sys.exit(main())

