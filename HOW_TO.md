# คู่มือการใช้งานระบบประหยัดไฟ RDS (Idle-Aware Strategy)

คู่มือนี้จะสอนวิธีการติดตั้งระบบ **RDS Auto Start-Stop** ที่รองรับทั้งการปิดเมื่อไม่มีการใช้งาน (Idle) และ **การเปิดอัตโนมัติเมื่อมีคนพยายามเชื่อมต่อ (Wake-on-Traffic)**

---

## ฟีเจอร์หลัก (Key Features)

- **Auto-Stop**: ปิดเองเมื่อ Idle ครบ 60 นาที (เช็คทุกชั่วโมง)
- **Wake-on-Traffic**: เปิดเองทันทีที่มีคนพยายาม Connect (ใช้ VPC Flow Logs)
- **Manual Control**: เปิดเองผ่าน Script เมื่อต้องการ

## 1. วิธีการปิดอัตโนมัติ (Auto-Stop via Lambda)

เราใช้ **AWS Lambda** คอยตรวจสอบว่ามีคนต่อ Database หรือไม่ผ่าน CloudWatch Metrics

- **Logic**: ถ้าไม่มีการเชื่อมต่อ (0 Connections) ติดต่อกัน 60 นาที ระบบจะสั่ง Stop ทันที
- **Schedule (Cron)**: ตั้งค่า EventBridge ให้รันทุกชั่วโมง ตลอด 24 ชม. ทุกวัน:
  ```text
  cron(0 * * * ? *)
  ```

---

## 2. วิธีการเปิดใช้งาน (Manual Wake-up)

เนื่องจาก RDS ไม่รองรับการเปิดเองเมื่อมี Traffic เข้ามา คุณต้องเรียกคำสั่ง "ปลุก" (Wake-up) ก่อนเริ่มงาน:

### ผ่าน Command Line (CLI):

```bash
# ใช้ Script ที่เตรียมไว้ให้
./scripts/wake-up.sh [ชื่อ-db-ของคุณ]
```

### ผ่าน AWS CLI โดยตรง:

```bash
aws rds start-db-instance --db-instance-identifier YOUR_DB_ID --region ap-southeast-1
```

---

## 3. นโยบายความปลอดภัย (IAM Policy)

ใช้สิทธิ์ให้น้อยที่สุด (Least Privilege) ตามไฟล์ [aws/iam-policy.json](aws/iam-policy.json) ซึ่งจะเข้าถึงได้เฉพาะ:

1. การสั่ง Start/Stop/Describe RDS
2. การอ่านค่า Metric จาก CloudWatch

---

## สรุปข้อดี

- ประหยัดค่า Compute ได้สูงสุดถึง **70%**
- ไม่ต้องกังวลเรื่องลืมปิดตอนเลิกงาน
- DB Endpoint ยังคงเดิม ไม่เปลี่ยนแปลง
