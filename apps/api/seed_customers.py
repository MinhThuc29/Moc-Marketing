import sqlite3
import json
from datetime import datetime, timezone, timedelta

conn = sqlite3.connect('moc_healthy.db')
cursor = conn.cursor()

now = datetime.now(timezone.utc)
customers = [
    ('c-001', 'Nguyễn Văn An', '0912345678', 'an.nguyen@example.com', '12 Lê Duẩn, Q1, TP.HCM', 'ONLINE', 'VIP', 15, 3200000.0, 213333.3, 320, json.dumps(['thich_salad', 'gym_member', 'healthy_food']), (now - timedelta(days=2)).isoformat(), (now - timedelta(days=90)).isoformat(), now.isoformat()),
    ('c-002', 'Trần Thị Bích', '0987654321', 'bich.tran@example.com', '45 Nguyễn Thị Minh Khai, Q3', 'ONLINE', 'ACTIVE', 4, 650000.0, 162500.0, 65, json.dumps(['eat_clean', 'uong_detox']), (now - timedelta(days=5)).isoformat(), (now - timedelta(days=30)).isoformat(), now.isoformat()),
    ('c-003', 'Lê Hoàng Cường', '0933112233', 'cuong.le@example.com', '88 Nam Kỳ Khởi Nghĩa, Q1', 'WALK_IN', 'REPEAT', 3, 420000.0, 140000.0, 42, json.dumps(['van_phong', 'giao_tan_noi']), (now - timedelta(days=12)).isoformat(), (now - timedelta(days=40)).isoformat(), now.isoformat()),
    ('c-004', 'Phạm Thu Dung', '0901234567', 'dung.pham@example.com', '100 Hai Bà Trưng, Q1', 'ONLINE', 'NEW', 1, 110000.0, 110000.0, 11, json.dumps(['khach_moi']), (now - timedelta(days=1)).isoformat(), (now - timedelta(days=1)).isoformat(), now.isoformat()),
    ('c-005', 'Đỗ Minh Tuấn', '0944556677', 'tuan.do@example.com', '20 Pasteur, Q1', 'HOTLINE', 'AT_RISK', 6, 1150000.0, 191666.7, 115, json.dumps(['combo_tiet_kiem']), (now - timedelta(days=35)).isoformat(), (now - timedelta(days=120)).isoformat(), now.isoformat()),
    ('c-006', 'Hoàng Yến Nhi', '0955667788', 'nhi.hoang@example.com', '15 Thảo Điền, Q2, TP.Thủ Đức', 'GRAB', 'DORMANT', 2, 260000.0, 130000.0, 26, json.dumps(['sinh_to_bo']), (now - timedelta(days=68)).isoformat(), (now - timedelta(days=100)).isoformat(), now.isoformat()),
]

for c in customers:
    cursor.execute('''
        INSERT OR REPLACE INTO customers 
        (id, full_name, phone, email, default_address, source, segment, order_count, total_spent, average_order_value, loyalty_points, tags, last_order_at, first_order_at, created_at, updated_at, consent_marketing)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    ''', (c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10], c[11], c[12], c[13], c[14], c[14]))

cursor.execute('''
    INSERT OR REPLACE INTO loyalty_transactions
    (id, customer_id, transaction_type, points, balance_after, reason, created_at)
    VALUES ('tx-001', 'c-001', 'EARN', 320, 320, 'Tích lũy từ các đơn hàng mua sắm', ?)
''', (now.isoformat(),))

conn.commit()
print('Successfully seeded 6 demo customers!')
