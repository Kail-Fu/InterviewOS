"""
Assessment 3 Autograder Runner
Runs the autograder.py on a candidate submission and outputs JSON results
"""

import sys
import os
import subprocess
import json
import shutil
from pathlib import Path
import tempfile

def run_autograder(submission_dir):
    """
    Run autograder.py on the submission directory
    Returns a dict with test results
    """
    autograder_script = Path(__file__).parent / 'autograder.py'
    
    if not autograder_script.exists():
        return {
            'success': False,
            'error': 'Autograder script not found',
            'total_points': 0,
            'max_points': 100,
            'tests': []
        }
    
    try:
        # Run autograder
        result = subprocess.run(
            [sys.executable, str(autograder_script), submission_dir],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        # Look for grading_results.json in submission directory
        results_file = Path(submission_dir) / 'grading_results.json'
        
        if results_file.exists():
            with open(results_file, 'r') as f:
                grading_data = json.load(f)
            
            # Convert to our expected format
            tests = []
            for test in grading_data.get('tests', []):
                tests.append({
                    'name': test['name'],
                    'status': test['status'].lower(),
                    'score': test['points'],
                    'maxScore': test['max_points'],
                    'input': f"Test: {test['name']}",
                    'expected': f"{test['max_points']} points",
                    'output': f"{test['points']} points - {test['status']}"
                })
            
            return {
                'success': True,
                'total_points': grading_data['total_points'],
                'max_points': grading_data['max_points'],
                'percentage': grading_data['percentage'],
                'tests': tests,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        else:
            # Autograder failed to produce results
            return {
                'success': False,
                'error': 'Autograder did not produce results file',
                'total_points': 0,
                'max_points': 100,
                'tests': [],
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Autograder timed out after 10 minutes',
            'total_points': 0,
            'max_points': 100,
            'tests': []
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Autograder execution failed: {str(e)}',
            'total_points': 0,
            'max_points': 100,
            'tests': []
        }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: python3 assessment3_autograder.py <submission_directory>'
        }))
        sys.exit(1)
    
    submission_dir = sys.argv[1]
    
    if not os.path.exists(submission_dir):
        print(json.dumps({
            'success': False,
            'error': f'Submission directory not found: {submission_dir}'
        }))
        sys.exit(1)
    
    # Run autograder
    results = run_autograder(submission_dir)
    
    # Output results as JSON
    print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)

if __name__ == '__main__':
    main()

