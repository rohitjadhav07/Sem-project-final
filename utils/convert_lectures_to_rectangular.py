#!/usr/bin/env python3
"""
Bulk Conversion Utility
Convert circular geofences to rectangular boundaries for multiple lectures
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app, db
from models.lecture import Lecture
from utils.rectangular_geofence import RectangularBoundary
import json


def convert_lecture_to_rectangular(lecture, dry_run=False):
    """
    Convert a single lecture from circular to rectangular
    
    Args:
        lecture: Lecture object
        dry_run: If True, don't save changes
    
    Returns:
        dict: Conversion result
    """
    try:
        if lecture.geofence_type == 'rectangular':
            return {
                'lecture_id': lecture.id,
                'title': lecture.title,
                'status': 'skipped',
                'reason': 'Already rectangular'
            }
        
        if not lecture.latitude or not lecture.longitude or not lecture.geofence_radius:
            return {
                'lecture_id': lecture.id,
                'title': lecture.title,
                'status': 'failed',
                'reason': 'Missing circular geofence data'
            }
        
        # Create rectangular boundary from circular
        boundary = RectangularBoundary.from_circular(
            lecture.latitude,
            lecture.longitude,
            lecture.geofence_radius
        )
        
        # Calculate areas for comparison
        circular_area = 3.14159 * (lecture.geofence_radius ** 2)
        rectangular_area = boundary.calculate_area()
        
        result = {
            'lecture_id': lecture.id,
            'title': lecture.title,
            'status': 'success' if not dry_run else 'dry_run',
            'original': {
                'type': 'circular',
                'center': (lecture.latitude, lecture.longitude),
                'radius': lecture.geofence_radius,
                'area_sqm': circular_area
            },
            'converted': {
                'type': 'rectangular',
                'corners': boundary.to_dict()['corners'],
                'area_sqm': rectangular_area,
                'perimeter_m': boundary.calculate_perimeter()
            }
        }
        
        if not dry_run:
            # Save the rectangular boundary
            ne = boundary.ne
            nw = boundary.nw
            se = boundary.se
            sw = boundary.sw
            
            lecture.set_rectangular_boundary(
                ne, nw, se, sw,
                gps_threshold=20,
                tolerance=2.0
            )
        
        return result
        
    except Exception as e:
        return {
            'lecture_id': lecture.id,
            'title': lecture.title,
            'status': 'error',
            'error': str(e)
        }


def convert_all_lectures(lecture_ids=None, dry_run=False):
    """
    Convert multiple lectures to rectangular boundaries
    
    Args:
        lecture_ids: List of lecture IDs to convert (None = all)
        dry_run: If True, don't save changes
    
    Returns:
        dict: Conversion report
    """
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("BULK LECTURE CONVERSION TO RECTANGULAR BOUNDARIES")
        print("="*60 + "\n")
        
        if dry_run:
            print("🔍 DRY RUN MODE - No changes will be saved\n")
        
        # Get lectures to convert
        if lecture_ids:
            lectures = Lecture.query.filter(Lecture.id.in_(lecture_ids)).all()
            print(f"Converting {len(lectures)} specified lectures...\n")
        else:
            lectures = Lecture.query.filter_by(geofence_type='circular').all()
            print(f"Converting all {len(lectures)} circular geofence lectures...\n")
        
        results = {
            'total': len(lectures),
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'details': []
        }
        
        for i, lecture in enumerate(lectures, 1):
            print(f"[{i}/{len(lectures)}] Processing: {lecture.title} (ID: {lecture.id})")
            
            result = convert_lecture_to_rectangular(lecture, dry_run)
            results['details'].append(result)
            
            if result['status'] == 'success' or result['status'] == 'dry_run':
                results['success'] += 1
                print(f"  ✅ Converted successfully")
                print(f"     Original: {result['original']['area_sqm']:.1f} m² (circular)")
                print(f"     New: {result['converted']['area_sqm']:.1f} m² (rectangular)")
            elif result['status'] == 'skipped':
                results['skipped'] += 1
                print(f"  ⏭️  Skipped: {result['reason']}")
            elif result['status'] == 'failed':
                results['failed'] += 1
                print(f"  ⚠️  Failed: {result['reason']}")
            elif result['status'] == 'error':
                results['errors'] += 1
                print(f"  ❌ Error: {result['error']}")
            
            print()
        
        # Print summary
        print("="*60)
        print("CONVERSION SUMMARY")
        print("="*60)
        print(f"Total lectures processed: {results['total']}")
        print(f"✅ Successfully converted: {results['success']}")
        print(f"⏭️  Skipped: {results['skipped']}")
        print(f"⚠️  Failed: {results['failed']}")
        print(f"❌ Errors: {results['errors']}")
        print("="*60 + "\n")
        
        if dry_run:
            print("This was a DRY RUN. No changes were saved.")
            print("Run without --dry-run to apply changes.\n")
        
        return results


def generate_conversion_report(results, output_file='conversion_report.json'):
    """Generate a JSON report of the conversion"""
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"📄 Detailed report saved to: {output_file}\n")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert lectures to rectangular boundaries')
    parser.add_argument('--lecture-ids', nargs='+', type=int, help='Specific lecture IDs to convert')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without saving')
    parser.add_argument('--report', type=str, help='Output report file path')
    
    args = parser.parse_args()
    
    # Run conversion
    results = convert_all_lectures(
        lecture_ids=args.lecture_ids,
        dry_run=args.dry_run
    )
    
    # Generate report if requested
    if args.report:
        generate_conversion_report(results, args.report)
    
    # Exit with appropriate code
    if results['errors'] > 0 or results['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
