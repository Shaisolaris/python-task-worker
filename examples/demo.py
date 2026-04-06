"""
Demo: Submit tasks without Redis (shows task structure).
Run: python examples/demo.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tasks.email_tasks import send_email, send_template_email
from tasks.data_tasks import generate_report, aggregate_metrics
from tasks.notification_tasks import send_push, send_sms
from tasks.cleanup_tasks import health_check

def main():
    print("⚡ Task Worker Demo (direct execution, no Redis needed)")
    print("=" * 55)

    # Email tasks
    print("\n📧 Email Tasks:")
    result = send_email("user@example.com", "Welcome!", "Hello World")
    print(f"   send_email: {result}")

    result = send_template_email("user@example.com", "welcome", {"name": "Sarah", "appName": "MyApp", "link": "https://example.com"})
    print(f"   send_template_email: {result}")

    # Data tasks
    print("\n📊 Data Tasks:")
    result = generate_report("sales", {"quarter": "Q1"})
    print(f"   generate_report: {result}")

    result = aggregate_metrics("revenue", "monthly")
    print(f"   aggregate_metrics: {result}")

    # Notification tasks
    print("\n🔔 Notification Tasks:")
    result = send_push("user123", "New message", "You have a new message")
    print(f"   send_push: {result}")

    result = send_sms("+1234567890", "Your code is 1234")
    print(f"   send_sms: {result}")

    # Health check
    print("\n💚 Health Check:")
    result = health_check()
    print(f"   {result}")

if __name__ == "__main__":
    main()
