"""
Set verification status untuk pengguna uji identitas AI.
"""
from extensions import db
from models import User, VerificationRequest
from app import create_app

app = create_app()
with app.app_context():
    # Set approved for ident.approved
    user_appr = User.query.filter_by(email="ident.approved.1794305263@example.com").first()
    if user_appr and user_appr.business_profile:
        # Remove existing verifications if any
        VerificationRequest.query.filter_by(business_profile_id=user_appr.business_profile.id).delete()
        vr = VerificationRequest(
            business_profile_id=user_appr.business_profile.id,
            status="approved",
        )
        db.session.add(vr)
        db.session.commit()
        print(f"Set approved for {user_appr.business_profile.business_name} (ID={user_appr.business_profile.id})")

    # Set rejected for ident.rejected
    user_rej = User.query.filter_by(email="ident.rejected.1794305263@example.com").first()
    if user_rej and user_rej.business_profile:
        VerificationRequest.query.filter_by(business_profile_id=user_rej.business_profile.id).delete()
        vr = VerificationRequest(
            business_profile_id=user_rej.business_profile.id,
            status="rejected",
            rejection_reason="Dokumen tidak lengkap untuk uji coba",
        )
        db.session.add(vr)
        db.session.commit()
        print(f"Set rejected for {user_rej.business_profile.business_name} (ID={user_rej.business_profile.id})")

    # Verify final state
    for email in ["ident.approved.1794305263@example.com", "ident.rejected.1794305263@example.com"]:
        u = User.query.filter_by(email=email).first()
        if u and u.business_profile:
            vr = VerificationRequest.query.filter_by(business_profile_id=u.business_profile.id).order_by(VerificationRequest.submitted_at.desc()).first()
            print(f"  {email}: bp={u.business_profile.business_name}, verification={vr.status if vr else None}")