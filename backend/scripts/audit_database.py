import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path for direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.mongo import connect_to_mongo, close_mongo_connection, get_database
from app.config import get_settings


async def audit():
    print("=" * 65)
    print("ALLEN NEET System: Live Multi-Course Database & Artifact Audit")
    print("=" * 65)

    await connect_to_mongo()
    db = get_database()
    settings = get_settings()

    # 1. Tests Audit by Class
    tests = await db.tests.find().to_list(200)
    tests_12th = [t for t in tests if t.get("target_class") == "12th"]
    tests_11th = [t for t in tests if t.get("target_class") == "11th"]

    print(f"\n1. TESTS SUMMARY: Total {len(tests)} Tests in Database")
    print(f"   • Class 12th (Leader): {len(tests_12th)} tests")
    print(f"   • Class 11th (Nurture): {len(tests_11th)} tests")
    print("-" * 65)

    for target_class, class_tests in [("Class 12th (Leader)", tests_12th), ("Class 11th (Nurture)", tests_11th)]:
        print(f"\n--- {target_class} ({len(class_tests)} tests) ---")
        for t in class_tests:
            ext_id = t.get("external_test_id")
            name = t.get("name")
            status = t.get("status")
            mode = t.get("mode")
            has_syl = t.get("has_syllabus", False)
            has_qp = t.get("has_question_paper", False)

            storage_dir = Path(settings.LOCAL_STORAGE_DIR) / f"test_{ext_id}"
            syl_file = storage_dir / "syllabus.pdf"
            qp_file = storage_dir / "question_paper.pdf"

            syl_size = f"{syl_file.stat().st_size / 1024:.1f} KB" if syl_file.exists() else "Missing"
            qp_size = f"{qp_file.stat().st_size / 1024:.1f} KB" if qp_file.exists() else "None (Pending)"

            print(f"• [{ext_id}] {name}")
            print(f"    Mode: {mode} | Status: {status}")
            print(f"    Syllabus: {'✓' if has_syl else '✗'} ({syl_size}) | Question Paper: {'✓' if has_qp else '✗'} ({qp_size})")

    # 2. Topics by Subject & Class Audit
    topics = await db.topics.find().to_list(2000)
    by_subj = {"Physics": [], "Chemistry": [], "Biology": []}
    by_class = {"12th_only": 0, "11th_only": 0, "both": 0}
    anomalies = []

    for top in topics:
        subj = top.get("subject")
        name = top.get("name", "")
        classes = set(top.get("target_classes", []))

        if "12th" in classes and "11th" in classes:
            by_class["both"] += 1
        elif "11th" in classes:
            by_class["11th_only"] += 1
        elif "12th" in classes:
            by_class["12th_only"] += 1

        if subj in by_subj:
            by_subj[subj].append(top)
        else:
            by_subj.setdefault(subj, []).append(top)

        if any(name.upper().startswith(prefix) for prefix in ["BIOLOGY:", "CHEMISTRY:", "PHYSICS:"]):
            anomalies.append((subj, name))

    print(f"\n2. TOPIC CATALOG AUDIT: Total {len(topics)} Unique Canonical Topics")
    print(f"   • Class 12th only: {by_class['12th_only']} topics")
    print(f"   • Class 11th only: {by_class['11th_only']} topics")
    print(f"   • Shared (11th & 12th): {by_class['both']} topics")
    print("-" * 65)
    for subj in ["Physics", "Chemistry", "Biology"]:
        subj_topics = by_subj.get(subj, [])
        print(f"• {subj}: {len(subj_topics)} topics")
        print("    Top topics by test coverage:")
        sorted_subj = sorted(subj_topics, key=lambda x: x.get("test_count", 0), reverse=True)
        for sample in sorted_subj[:4]:
            t_classes = ",".join(sample.get("target_classes", [])) or "12th"
            print(f"      - {sample.get('name')} ({sample.get('test_count', 0)} tests) [{t_classes}]")

    # 3. Anomaly Check
    print(f"\n3. INTEGRITY & ANOMALY CHECK")
    print("-" * 65)
    if anomalies:
        print(f"⚠️ Found {len(anomalies)} topics with leaked subject prefixes:")
        for s, n in anomalies:
            print(f"   [{s}] {n}")
    else:
        print("✅ 100% CLEAN: Zero subject prefixes or title anomalies found in topic names!")

    # 4. Relationships Audit
    rel_count = await db.test_topics.count_documents({})
    print(f"\n4. BIDIRECTIONAL RELATIONSHIPS: {rel_count} Total Indexed Edges across all courses")
    print("=" * 65)

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(audit())
