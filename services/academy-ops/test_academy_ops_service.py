from __future__ import annotations

import importlib.util
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.academy import AcademyEnrollment, AcademyPackage
from shared.models.invoice import Invoice
from services.commerce.billing import InvoiceRecord, InvoiceState

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/academy-ops/service.py"
_service_spec = importlib.util.spec_from_file_location("academy_ops_test_module", MODULE_PATH)
if _service_spec is None or _service_spec.loader is None:
    raise RuntimeError("Unable to load academy-ops module")
_service_module = importlib.util.module_from_spec(_service_spec)
sys.modules[_service_spec.name] = _service_module
_service_spec.loader.exec_module(_service_module)

AcademyOpsService = _service_module.AcademyOpsService
AttendanceRecord = _service_module.AttendanceRecord
Batch = _service_module.Batch
Branch = _service_module.Branch
FeePayment = _service_module.FeePayment
RevenueShareAgreement = _service_module.RevenueShareAgreement
TeacherAssignment = _service_module.TeacherAssignment
TeacherPerformanceSnapshot = _service_module.TeacherPerformanceSnapshot
TimetableSlot = _service_module.TimetableSlot
UnifiedStudentProfile = _service_module.UnifiedStudentProfile


def test_branch_batch_teacher_timetable_and_attendance_workflow() -> None:
    service = AcademyOpsService()
    service.register_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_1",
            student_id="learner_1",
            display_name="Ari Ops",
            email="ari@example.edu",
            country_code="US",
            segment_id="academy",
        )
    )

    service.upsert_branch(
        Branch(
            tenant_id="tenant_1",
            branch_id="branch_nyc",
            academy_id="academy_1",
            name="NYC Campus",
            timezone="America/New_York",
        )
    )
    service.create_batch(
        Batch(
            tenant_id="tenant_1",
            branch_id="branch_nyc",
            batch_id="batch_1",
            academy_id="academy_1",
            title="Python Evening",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 6, 30),
            learner_ids=("learner_1",),
        )
    )
    service.assign_teacher(
        TeacherAssignment(
            tenant_id="tenant_1",
            branch_id="branch_nyc",
            batch_id="batch_1",
            teacher_id="teacher_1",
        )
    )

    start = datetime(2026, 4, 2, 17, 0, 0)
    slot = service.publish_timetable_slot(
        TimetableSlot(
            tenant_id="tenant_1",
            branch_id="branch_nyc",
            batch_id="batch_1",
            slot_id="slot_1",
            teacher_id="teacher_1",
            start_at=start,
            end_at=start + timedelta(hours=2),
            room="R-12",
        )
    )

    service.register_batch_enrollment(
        AcademyEnrollment(
            tenant_id="tenant_1",
            academy_id="academy_1",
            cohort_id="batch_1",
            learner_id="learner_1",
            package=AcademyPackage.PRO,
        )
    )

    attendance = service.record_attendance(
        AttendanceRecord(
            tenant_id="tenant_1",
            branch_id="branch_nyc",
            batch_id="batch_1",
            learner_id="learner_1",
            slot_id=slot.slot_id,
            present=True,
        )
    )

    assert attendance.present is True


def test_fee_tracking_integrates_system_of_record_ledger() -> None:
    service = AcademyOpsService()
    service.register_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_2",
            student_id="learner_2",
            display_name="Fee Student",
            email="fee@example.edu",
            country_code="US",
            segment_id="academy",
        )
    )

    service.record_fee_invoice(learner_id="learner_2", invoice=Invoice.issued("inv_1", "tenant_2", Decimal("120.00")))
    service.record_fee_invoice(learner_id="learner_2", invoice=Invoice.issued("inv_2", "tenant_2", Decimal("30.00")))
    service.record_fee_payment(
        FeePayment(
            tenant_id="tenant_2",
            learner_id="learner_2",
            payment_id="pay_1",
            amount=Decimal("50.00"),
        )
    )

    assert service.learner_fee_balance(tenant_id="tenant_2", learner_id="learner_2") == Decimal("100.00")
    assert service._sor.get_student_balance(tenant_id="tenant_2", student_id="learner_2") == Decimal("150.00")

    commerce_invoice = InvoiceRecord(
        invoice_id="inv_3",
        order_id="order_3",
        tenant_id="tenant_2",
        amount=Decimal("20.00"),
        currency="USD",
        state=InvoiceState.ISSUED,
        invoice_type="one_time",
    )
    service.ingest_commerce_invoice(learner_id="learner_2", invoice_record=commerce_invoice)
    assert service.learner_fee_balance(tenant_id="tenant_2", learner_id="learner_2") == Decimal("120.00")


def test_qc_fix_prevents_learning_core_overlap() -> None:
    service = AcademyOpsService()

    assert service.has_learning_core_overlap() is False
    assert service.is_single_source_of_truth() is True


def test_teacher_economy_batches_revenue_share_and_performance_tracking() -> None:
    service = AcademyOpsService()
    service.register_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_eco",
            student_id="learner_eco_1",
            display_name="Eco Learner",
            email="eco@example.edu",
            country_code="US",
            segment_id="academy",
        )
    )
    service.upsert_branch(
        Branch(
            tenant_id="tenant_eco",
            branch_id="branch_la",
            academy_id="academy_eco",
            name="LA Campus",
            timezone="America/Los_Angeles",
        )
    )
    service.create_batch(
        Batch(
            tenant_id="tenant_eco",
            branch_id="branch_la",
            batch_id="batch_eco_1",
            academy_id="academy_eco",
            title="Data Systems",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 7, 31),
            learner_ids=("learner_eco_1",),
        )
    )
    service.assign_teacher(
        TeacherAssignment(
            tenant_id="tenant_eco",
            branch_id="branch_la",
            batch_id="batch_eco_1",
            teacher_id="teacher_eco_1",
        )
    )

    teacher_batches = service.teacher_batches(tenant_id="tenant_eco", teacher_id="teacher_eco_1")
    assert tuple(batch.batch_id for batch in teacher_batches) == ("batch_eco_1",)

    service.configure_revenue_share(
        RevenueShareAgreement(
            tenant_id="tenant_eco",
            batch_id="batch_eco_1",
            teacher_id="teacher_eco_1",
            share_ratio=Decimal("0.30"),
        )
    )
    snapshot = service.record_teacher_performance(
        TeacherPerformanceSnapshot(
            tenant_id="tenant_eco",
            batch_id="batch_eco_1",
            teacher_id="teacher_eco_1",
            attendance_rate=Decimal("0.95"),
            completion_rate=Decimal("0.88"),
            learner_satisfaction=Decimal("0.90"),
        )
    )
    assert snapshot.score() == Decimal("0.9130")
    assert (
        service.latest_teacher_performance(
            tenant_id="tenant_eco",
            batch_id="batch_eco_1",
            teacher_id="teacher_eco_1",
        )
        == snapshot
    )

    commerce_invoice = InvoiceRecord(
        invoice_id="inv_eco_1",
        order_id="order_eco_1",
        tenant_id="tenant_eco",
        amount=Decimal("100.00"),
        currency="USD",
        state=InvoiceState.ISSUED,
        invoice_type="one_time",
    )
    service.ingest_commerce_invoice_for_batch(
        learner_id="learner_eco_1",
        batch_id="batch_eco_1",
        invoice_record=commerce_invoice,
    )
    payouts = service.teacher_payouts(tenant_id="tenant_eco", batch_id="batch_eco_1")
    assert len(payouts) == 1
    assert payouts[0].payout_amount == Decimal("30.00")
