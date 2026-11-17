"""Membuat sesi Admin 102 via mekanisme resmi aplikasi (create_access_token).
Read-only terhadap DB: hanya SELECT user 102. Tidak mengubah password/data."""
import sys
sys.path.insert(0, '.')

from app import create_app
from extensions import db
from models.user import User
from utils.jwt_utils import create_access_token

app = create_app()
with app.app_context():
    user = db.session.get(User, 102)  # read-only
    if user is None or user.role != 'admin':
        raise SystemExit('user 102 bukan admin - dihentikan')
    token, expires_at, payload = create_access_token(user)
    open(r'C:\Users\faish\AppData\Local\Temp\opencode\admin_token.txt', 'w').write(token)
    print('sesi admin dibuat via create_access_token() resmi')
    print('user id :', payload['sub'], '| role:', payload['role'], '| type:', payload['type'])
    print('expired :', expires_at.strftime('%H:%M:%S UTC'), '(60 menit)')
    print('DB write: tidak ada (hanya SELECT)')
