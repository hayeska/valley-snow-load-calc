#!/usr/bin/env python3
"""
Valley Snow Load Calculator - Data Merge Utilities
Intelligent merging of partial data from multiple backup sources

Usage:
    python data_merge_utilities.py --merge state.backup.json auto_backups/2025-12-31_13-45-53/
    python data_merge_utilities.py --analyze state.backup.json auto_backups/2025-12-31_13-45-53/
    python data_merge_utilities.py --resolve-conflicts merged_data.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import difflib
import logging

class DataMergeUtilities:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    def merge_backup_sources(self, primary_source: str, secondary_sources: List[str],
                           output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Merge data from multiple backup sources with conflict resolution

        Args:
            primary_source: Path to primary backup (highest priority)
            secondary_sources: List of secondary backup paths
            output_file: Optional output file path

        Returns:
            Merged data dictionary
        """
        merged_data = {}
        merge_report = {
            "sources": [],
            "conflicts_resolved": 0,
            "data_preserved": 0,
            "merge_timestamp": datetime.now().isoformat()
        }

        # Load primary source
        primary_data = self.load_backup_data(primary_source)
        if primary_data:
            merged_data.update(primary_data)
            merge_report["sources"].append({
                "path": primary_source,
                "type": "primary",
                "data_points": self.count_data_points(primary_data)
            })

        # Merge secondary sources
        for source_path in secondary_sources:
            source_data = self.load_backup_data(source_path)
            if source_data:
                conflicts = self.merge_with_conflict_resolution(merged_data, source_data, primary_override=True)
                merge_report["conflicts_resolved"] += len(conflicts)
                merge_report["sources"].append({
                    "path": source_path,
                    "type": "secondary",
                    "data_points": self.count_data_points(source_data),
                    "conflicts": len(conflicts)
                })

        merge_report["data_preserved"] = self.count_data_points(merged_data)

        # Add merge metadata
        merged_data["_merge_info"] = merge_report

        # Save merged data if output file specified
        if output_file:
            self.save_merged_data(merged_data, output_file)
            print(f"✅ Merged data saved to: {output_file}")

        return merged_data

    def load_backup_data(self, source_path: str) -> Optional[Dict[str, Any]]:
        """Load backup data from various formats"""
        path = Path(source_path)

        try:
            if path.is_file() and path.suffix == '.json':
                # Direct JSON file
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)

            elif path.is_dir():
                # Directory with multiple files
                data = {}
                for file_path in path.glob("*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_data = json.load(f)
                        # Merge file data into combined data
                        self.merge_dict_recursive(data, file_data, primary_override=False)
                    except Exception as e:
                        self.logger.warning(f"Could not load {file_path}: {e}")
                return data if data else None

            else:
                self.logger.error(f"Unsupported backup source: {source_path}")
                return None

        except Exception as e:
            self.logger.error(f"Error loading backup data from {source_path}: {e}")
            return None

    def merge_with_conflict_resolution(self, target: Dict[str, Any], source: Dict[str, Any],
                                     primary_override: bool = True) -> List[Dict[str, Any]]:
        """
        Merge dictionaries with intelligent conflict resolution

        Returns list of conflicts that were resolved
        """
        conflicts = []

        for key, source_value in source.items():
            if key not in target:
                # No conflict - add new data
                target[key] = source_value
            else:
                target_value = target[key]

                # Check for conflicts
                conflict = self.detect_conflict(key, target_value, source_value)
                if conflict:
                    # Resolve conflict
                    resolved_value = self.resolve_conflict(conflict, primary_override)
                    target[key] = resolved_value

                    conflicts.append({
                        "key": key,
                        "target_value": target_value,
                        "source_value": source_value,
                        "resolution": "primary_override" if primary_override else "latest_wins",
                        "resolved_value": resolved_value
                    })

                elif isinstance(target_value, dict) and isinstance(source_value, dict):
                    # Recursive merge for nested dictionaries
                    sub_conflicts = self.merge_with_conflict_resolution(target_value, source_value, primary_override)
                    conflicts.extend(sub_conflicts)

                elif isinstance(target_value, list) and isinstance(source_value, list):
                    # Merge lists intelligently
                    merged_list = self.merge_lists(target_value, source_value)
                    if merged_list != target_value:
                        target[key] = merged_list

        return conflicts

    def detect_conflict(self, key: str, value1: Any, value2: Any) -> Optional[Dict[str, Any]]:
        """Detect if two values conflict"""
        if value1 == value2:
            return None  # No conflict

        # Check if values are different but compatible
        if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            # Numeric values - small differences might not be conflicts
            diff = abs(value1 - value2)
            if diff < 0.01:  # Tolerance for floating point
                return None
        elif isinstance(value1, str) and isinstance(value2, str):
            # String values - check similarity
            similarity = difflib.SequenceMatcher(None, value1, value2).ratio()
            if similarity > 0.9:  # Very similar strings
                return None

        # Values are different enough to be considered a conflict
        return {
            "key": key,
            "value1": value1,
            "value2": value2,
            "type": self.get_conflict_type(value1, value2)
        }

    def get_conflict_type(self, value1: Any, value2: Any) -> str:
        """Determine the type of conflict"""
        if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            return "numeric_difference"
        elif isinstance(value1, str) and isinstance(value2, str):
            return "string_difference"
        elif isinstance(value1, bool) and isinstance(value2, bool):
            return "boolean_difference"
        elif isinstance(value1, list) and isinstance(value2, list):
            return "list_difference"
        elif isinstance(value1, dict) and isinstance(value2, dict):
            return "dict_difference"
        else:
            return "type_difference"

    def resolve_conflict(self, conflict: Dict[str, Any], primary_override: bool) -> Any:
        """Resolve a conflict based on strategy"""
        if primary_override:
            # Keep the primary (target) value
            return conflict["value1"]
        else:
            # Use the newer (source) value
            return conflict["value2"]

    def merge_lists(self, list1: List[Any], list2: List[Any]) -> List[Any]:
        """Intelligently merge two lists"""
        # For now, use simple union while preserving order
        merged = list1.copy()

        for item in list2:
            if item not in merged:
                merged.append(item)

        return merged

    def merge_dict_recursive(self, target: Dict[str, Any], source: Dict[str, Any],
                           primary_override: bool = False):
        """Recursively merge dictionaries"""
        for key, value in source.items():
            if key not in target:
                target[key] = value
            elif isinstance(target[key], dict) and isinstance(value, dict):
                self.merge_dict_recursive(target[key], value, primary_override)
            elif not primary_override:
                target[key] = value

    def count_data_points(self, data: Dict[str, Any]) -> int:
        """Count the number of data points in a dictionary"""
        count = 0
        for key, value in data.items():
            if key.startswith('_'):  # Skip metadata
                continue
            count += 1
            if isinstance(value, dict):
                count += self.count_data_points(value)
            elif isinstance(value, list):
                count += len(value)
        return count

    def analyze_backup_sources(self, *sources: str) -> Dict[str, Any]:
        """Analyze backup sources for compatibility and merge potential"""
        analysis = {
            "sources": [],
            "compatibility_score": 0,
            "recommended_merge_strategy": "none",
            "potential_conflicts": 0,
            "data_coverage": {}
        }

        loaded_sources = []
        for source_path in sources:
            data = self.load_backup_data(source_path)
            if data:
                source_info = {
                    "path": source_path,
                    "data_points": self.count_data_points(data),
                    "data_keys": list(data.keys()),
                    "timestamp": self.extract_timestamp(data)
                }
                loaded_sources.append(source_info)
                analysis["sources"].append(source_info)

        if len(loaded_sources) >= 2:
            # Analyze compatibility
            analysis["compatibility_score"] = self.calculate_compatibility_score(loaded_sources)
            analysis["potential_conflicts"] = self.estimate_conflicts(loaded_sources)
            analysis["recommended_merge_strategy"] = self.recommend_merge_strategy(loaded_sources)
            analysis["data_coverage"] = self.analyze_data_coverage(loaded_sources)

        return analysis

    def calculate_compatibility_score(self, sources: List[Dict[str, Any]]) -> float:
        """Calculate compatibility score between sources (0-1)"""
        if len(sources) < 2:
            return 1.0

        # Compare key sets
        key_sets = [set(source["data_keys"]) for source in sources]
        common_keys = set.intersection(*key_sets)
        total_keys = set.union(*key_sets)

        if not total_keys:
            return 0.0

        return len(common_keys) / len(total_keys)

    def estimate_conflicts(self, sources: List[Dict[str, Any]]) -> int:
        """Estimate number of potential conflicts"""
        # Simple estimation based on overlapping keys
        key_counts = {}
        for source in sources:
            for key in source["data_keys"]:
                key_counts[key] = key_counts.get(key, 0) + 1

        # Keys that appear in multiple sources could conflict
        return sum(1 for count in key_counts.values() if count > 1)

    def recommend_merge_strategy(self, sources: List[Dict[str, Any]]) -> str:
        """Recommend merge strategy based on source analysis"""
        if len(sources) < 2:
            return "none"

        # Check timestamps to determine which is newer
        timestamps = [source.get("timestamp") for source in sources if source.get("timestamp")]
        if timestamps and len(set(str(t) for t in timestamps)) > 1:
            return "timestamp_priority"

        # Default to primary override
        return "primary_override"

    def analyze_data_coverage(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data coverage across sources"""
        coverage = {}

        # Collect all unique keys
        all_keys = set()
        for source in sources:
            all_keys.update(source["data_keys"])

        # Check which sources have each key
        for key in all_keys:
            coverage[key] = []
            for i, source in enumerate(sources):
                if key in source["data_keys"]:
                    coverage[key].append(i)

        return coverage

    def extract_timestamp(self, data: Dict[str, Any]) -> Optional[datetime]:
        """Extract timestamp from backup data"""
        # Try various timestamp fields
        timestamp_fields = [
            "timestamp", "created_at", "updated_at",
            ["project_info", "auto_saved"],
            ["project_info", "created"]
        ]

        for field in timestamp_fields:
            if isinstance(field, list):
                # Nested field
                value = data
                for key in field:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = None
                        break
            else:
                value = data.get(field)

            if value:
                try:
                    if isinstance(value, str):
                        return datetime.fromisoformat(value.replace('Z', '+00:00'))
                    elif isinstance(value, (int, float)):
                        return datetime.fromtimestamp(value)
                except:
                    continue

        return None

    def resolve_conflicts_interactive(self, merged_data: Dict[str, Any]) -> Dict[str, Any]:
        """Interactive conflict resolution for merged data"""
        print("🔧 Interactive Conflict Resolution")
        print("=" * 40)

        conflicts = merged_data.get("_merge_conflicts", [])
        if not conflicts:
            print("✅ No conflicts found in merged data")
            return merged_data

        print(f"Found {len(conflicts)} conflicts to resolve:")

        for i, conflict in enumerate(conflicts, 1):
            print(f"\n{i}. Key: {conflict['key']}")
            print(f"   Option A: {conflict['value_a']}")
            print(f"   Option B: {conflict['value_b']}")

            while True:
                choice = input("Choose A, B, or 'skip': ").strip().upper()
                if choice == 'A':
                    # Apply value_a (already in merged data)
                    break
                elif choice == 'B':
                    # Apply value_b
                    self.set_nested_value(merged_data, conflict['key'].split('.'), conflict['value_b'])
                    break
                elif choice == 'SKIP':
                    print("Skipped this conflict")
                    break
                else:
                    print("Invalid choice. Please enter A, B, or 'skip'")

        # Remove conflict metadata
        if "_merge_conflicts" in merged_data:
            del merged_data["_merge_conflicts"]

        return merged_data

    def set_nested_value(self, data: Dict[str, Any], keys: List[str], value: Any):
        """Set a value in nested dictionary using key path"""
        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]
        data[keys[-1]] = value

    def save_merged_data(self, data: Dict[str, Any], output_file: str):
        """Save merged data to file with metadata"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Add merge completion timestamp
        if "_merge_info" in data:
            data["_merge_info"]["completion_timestamp"] = datetime.now().isoformat()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"💾 Merged data saved to: {output_path}")
        print(f"📊 Total data points: {self.count_data_points(data)}")

def main():
    parser = argparse.ArgumentParser(description='Data Merge Utilities for Valley Snow Load Calculator')
    parser.add_argument('sources', nargs='+', help='Backup source paths')
    parser.add_argument('--output', '-o', help='Output file for merged data')
    parser.add_argument('--analyze', action='store_true', help='Analyze sources without merging')
    parser.add_argument('--resolve-conflicts', action='store_true', help='Interactive conflict resolution')
    parser.add_argument('--primary-override', action='store_true', default=True,
                       help='Primary source takes precedence in conflicts')

    args = parser.parse_args()

    util = DataMergeUtilities()

    if args.analyze:
        # Analyze sources
        analysis = util.analyze_backup_sources(*args.sources)
        print(json.dumps(analysis, indent=2, default=str))

    elif args.resolve_conflicts:
        # Interactive conflict resolution
        if not args.output:
            print("❌ --output required for conflict resolution")
            sys.exit(1)

        # Load existing merged data
        try:
            with open(args.output, 'r') as f:
                merged_data = json.load(f)
        except FileNotFoundError:
            print(f"❌ File not found: {args.output}")
            sys.exit(1)

        resolved_data = util.resolve_conflicts_interactive(merged_data)
        util.save_merged_data(resolved_data, args.output)

    else:
        # Perform merge
        if len(args.sources) < 1:
            print("❌ At least one source required")
            sys.exit(1)

        primary = args.sources[0]
        secondary = args.sources[1:] if len(args.sources) > 1 else []

        merged_data = util.merge_backup_sources(
            primary, secondary, args.output
        )

        # Show merge summary
        merge_info = merged_data.get("_merge_info", {})
        print(f"✅ Merge completed:")
        print(f"   Sources merged: {len(merge_info.get('sources', []))}")
        print(f"   Conflicts resolved: {merge_info.get('conflicts_resolved', 0)}")
        print(f"   Data points preserved: {merge_info.get('data_preserved', 0)}")

        if not args.output:
            print("\n📋 Merged data preview:")
            print(json.dumps(merged_data, indent=2, default=str)[:1000] + "...")

if __name__ == "__main__":
    main()
