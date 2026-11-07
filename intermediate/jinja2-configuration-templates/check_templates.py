#!/usr/bin/env python3
"""
Test Jinja2 templates with sample data
Catch errors before deployment
"""

from jinja2 import Environment, FileSystemLoader, TemplateError
import yaml

def test_template(template_name, test_data_file):
    """
    Test template with sample data
    """
    print(f"\nTesting: {template_name}")
    print("-" * 50)

    # Setup environment
    env = Environment(
        loader=FileSystemLoader('templates'),
        trim_blocks=True,
        lstrip_blocks=True
    )

    try:
        # Load template
        template = env.get_template(template_name)

        # Load test data
        with open(test_data_file) as f:
            data = yaml.safe_load(f)

        # Render template
        config = template.render(data)

        # Basic validation
        if len(config) == 0:
            print("✗ FAIL: Generated config is empty")
            return False

        # Check for common Cisco config patterns
        if 'hostname' not in config:
            print("⚠ WARNING: Config doesn't contain hostname")

        print(f"✓ PASS: Generated {len(config):,} bytes")
        print("\nPreview (first 300 characters):")
        print(config[:300])

        return True

    except TemplateError as e:
        print(f"✗ FAIL: Template error")
        print(f"  Error: {e}")
        return False

    except Exception as e:
        print(f"✗ FAIL: Unexpected error")
        print(f"  Error: {e}")
        return False

def main():
    """Main function"""
    print("=" * 70)
    print("TEMPLATE TESTING")
    print("=" * 70)

    tests = [
        ('router_config.j2', 'test_data/router_test.yaml'),
        ('switch_config.j2', 'test_data/switch_test.yaml'),
        ('vlan_config.j2', 'test_data/vlan_test.yaml')
    ]

    results = []
    for template, test_data in tests:
        result = test_template(template, test_data)
        results.append((template, result))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed

    for template, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {template}")

    print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed}")

if __name__ == "__main__":
    main()
