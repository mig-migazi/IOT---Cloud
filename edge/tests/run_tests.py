#!/usr/bin/env python3
"""
Test Runner for Edge GRM Service
Runs all relevant tests for the Edge Core WebSocket-based GRM service
"""
import asyncio
import sys
from pathlib import Path


def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")


async def run_all_tests():
    """Run all relevant tests"""
    print("🚀 Edge GRM Service Test Suite")
    print("=" * 60)
    
    tests = [
        ("Configuration Test", "tests/test_config.py"),
        ("Edge Core WebSocket Test", "tests/test_edge_core.py"),
        ("Periodic Update Filtering Test", "tests/test_periodic_update.py"),
        ("Temperature Fahrenheit Test", "tests/test_temperature_fahrenheit.py"),
        ("Async Service Test", "tests/test_async_service.py"),
    ]
    
    results = {}
    
    for test_name, test_file in tests:
        print_header(f"Running {test_name}")
        
        if not Path(test_file).exists():
            print(f"❌ Test file {test_file} not found")
            results[test_name] = False
            continue
        
        try:
            # Import and run the test
            if test_file == "test_config.py":
                # test_config.py is not async, run it differently
                import subprocess
                result = subprocess.run([sys.executable, test_file], capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Configuration test passed")
                    results[test_name] = True
                else:
                    print(f"❌ Configuration test failed: {result.stderr}")
                    results[test_name] = False
            else:
                # Async tests
                if test_file == "tests/test_edge_core.py":
                    from test_edge_core import main as test_main
                elif test_file == "tests/test_periodic_update.py":
                    from test_periodic_update import main as test_main
                elif test_file == "tests/test_temperature_fahrenheit.py":
                    from test_temperature_fahrenheit import main as test_main
                elif test_file == "tests/test_async_service.py":
                    from test_async_service import main as test_main
                
                await test_main()
                results[test_name] = True
                
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n📊 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The Edge GRM Service is ready to run.")
        print("\n💡 Next Steps:")
        print("1. Run the service: python3 -m grm_service.main_async")
        print("2. Monitor logs: tail -f logs/grm_service.log")
        print("3. Check Edge Core for resource updates")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
    
    return passed == total


def main():
    """Main entry point"""
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
