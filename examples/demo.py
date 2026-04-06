"""
Demo: Run all task types without Celery/Redis.
Executes task logic directly to show what each task does.
Run: python examples/demo.py
"""

import json, datetime, time, hashlib

def send_email(to: str, subject: str, body: str) -> dict:
    return {"status": "sent", "to": to, "subject": subject, "message_id": f"msg_{hashlib.md5(to.encode()).hexdigest()[:8]}"}

def send_template_email(to: str, template: str, context: dict) -> dict:
    return {"status": "sent", "to": to, "template": template, "context_keys": list(context.keys())}

def generate_report(report_type: str, params: dict) -> dict:
    rows = [{"date": "2026-04-01", "revenue": 12500, "orders": 145},
            {"date": "2026-04-02", "revenue": 13200, "orders": 158},
            {"date": "2026-04-03", "revenue": 11800, "orders": 132}]
    return {"type": report_type, "rows": len(rows), "total_revenue": sum(r["revenue"] for r in rows)}

def aggregate_metrics(metric: str, period: str) -> dict:
    return {"metric": metric, "period": period, "value": 45200, "change": "+12.5%", "computed_at": datetime.datetime.now().isoformat()}

def send_push(user_id: str, title: str, body: str) -> dict:
    return {"status": "delivered", "user_id": user_id, "title": title}

def send_sms(phone: str, message: str) -> dict:
    return {"status": "queued", "phone": phone, "segments": 1}

def health_check() -> dict:
    return {"status": "healthy", "uptime": "3d 14h 22m", "tasks_processed": 14523, "tasks_failed": 12, "queues": {"email": 0, "data": 2, "notifications": 0}}

def main():
    print("⚡ Task Worker Demo (direct execution, no Redis/Celery needed)")
    print("=" * 60)

    print("\n📧 Email Tasks:")
    result = send_email("user@example.com", "Welcome!", "Hello World")
    print(f"   send_email → {json.dumps(result)}")

    result = send_template_email("user@example.com", "welcome", {"name": "Sarah", "app": "MyApp"})
    print(f"   send_template_email → {json.dumps(result)}")

    print("\n📊 Data Tasks:")
    result = generate_report("sales", {"quarter": "Q1"})
    print(f"   generate_report → {json.dumps(result)}")

    result = aggregate_metrics("revenue", "monthly")
    print(f"   aggregate_metrics → {json.dumps(result)}")

    print("\n🔔 Notification Tasks:")
    result = send_push("user123", "New message", "You have a new message")
    print(f"   send_push → {json.dumps(result)}")

    result = send_sms("+1234567890", "Your code is 1234")
    print(f"   send_sms → {json.dumps(result)}")

    print("\n💚 Health Check:")
    result = health_check()
    print(f"   {json.dumps(result, indent=2)}")

    print("\n✅ All 6 task types executed successfully")

if __name__ == "__main__":
    main()
