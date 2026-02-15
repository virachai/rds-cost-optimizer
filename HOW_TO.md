# คู่มือการติดตั้งและใช้งาน (GitHub Actions Step-by-Step)

คู่มือนี้จะสอนวิธีการติดตั้งระบบ **RDS Auto Start-Stop** โดยใช้ **GitHub Actions** ซึ่งเป็นวิธีที่ง่ายที่สุด ไม่ต้องใช้ Terraform หรือ Lambda

---

## ขั้นตอนที่ 1: เตรียมความพร้อม (Prerequisites)

1.  **สิทธิ์ AWS**: สร้าง IAM User และขอ **Access Key ID** และ **Secret Access Key**
2.  **นโยบาย (IAM Policy)**: ให้สิทธิ์ User ดังนี้:
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": [
            "rds:StartDBInstance",
            "rds:StopDBInstance",
            "rds:DescribeDBInstances"
          ],
          "Resource": "arn:aws:rds:ap-southeast-1:เลขบัญชี:db:ชื่อ-db-ของคุณ"
        }
      ]
    }
    ```
3.  **มี RDS Instance**: ตรวจสอบว่ามีฐานข้อมูล `db.t4g.micro` รันอยู่ใน `ap-southeast-1`

---

## ขั้นตอนที่ 2: ตั้งค่า GitHub Secrets

1.  ไปที่ Repository ของคุณใน GitHub
2.  เลือก **Settings** > **Secrets and variables** > **Actions**
3.  กด **New repository secret** และเพิ่มค่าดังนี้:
    - `AWS_ACCESS_KEY_ID`: (จากข้อ 1)
    - `AWS_SECRET_ACCESS_KEY`: (จากข้อ 1)
    - `RDS_INSTANCE_ID`: ชื่อ DB Instance ของคุณ (เช่น `my-dev-db`)

---

## ขั้นตอนที่ 3: ตรวจสอบการทำงาน

ระบบจะทำงานอัตโนมัติตามกำหนดเวลา (09:00น. และ 18:00น. วันจันทร์-ศุกร์) แต่คุณสามารถสั่งรันเองได้ทันที:

1.  ไปที่แถบ **Actions** ใน GitHub
2.  เลือก Workflow ชื่อ **RDS Auto Start-Stop**
3.  กด **Run workflow**
4.  เลือกคำสั่งที่ต้องการ (**START** หรือ **STOP**) แล้วกด **Run workflow**

---

## สรุปค่าใช้จ่ายที่ลดได้ (Cost Optimization)

ด้วยระบบนี้ เครื่องจะรันเพียง 9 ชั่วโมงต่อวันในวันธรรมดา (45 ชม./สัปดาห์) แทนที่จะรัน 168 ชม.

- **ค่าใช้จ่ายเดิม**: ~$18.00 ต่อเดือน
- **ค่าใช้จ่ายใหม่**: ~$5.85 ต่อเดือน
- **ประหยัดเงินได้**: **~67%** หรือมากกว่า 400 บาทต่อเดือนต่อหนึ่งฐานข้อมูล!
- **ค่าบริการ GitHub Actions**: **ฟรี (Free Tier)** สำหรับโปรเจกต์ทั่วไป
