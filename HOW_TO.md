# คู่มือการติดตั้งและใช้งาน (Step-by-Step Guide)

คู่มือนี้จะสอนวิธีการติดตั้งระบบ **RDS Auto Start-Stop** ตั้งแต่เริ่มต้นจนใช้งานได้จริง เพื่อลดค่าใช้จ่าย AWS สำหรับเครื่อง Dev/Test ในภูมิภาค Singapore (`ap-southeast-1`)

---

## ขั้นตอนที่ 1: เตรียมความพร้อม (Prerequisites)

1.  **สมัครบัญชี AWS**: และมีสิทธิ์ระดับ Administrator
2.  **ติดตั้งเครื่องมือ**:
    - **AWS CLI**: [วิธีติดตั้ง](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) และรัน `aws configure`
    - **Terraform**: [วิธีติดตั้ง](https://developer.hashicorp.com/terraform/downloads)
3.  **มี RDS Instance**: ตรวจสอบว่ามีฐานข้อมูล `db.t4g.micro` รันอยู่ใน `ap-southeast-1` และจดจำ **DB Instance Identifier** (เช่น `my-dev-db`)

---

## ขั้นตอนที่ 2: ดาวน์โหลดโปรเจกต์ (Cloning the Project)

เปิด Terminal หรือ PowerShell แล้วรันคำสั่ง:

```bash
git clone <url-of-this-repository>
cd rds-cost-optimizer
```

---

## ขั้นตอนที่ 3: ติดตั้ง Infrastructure ด้วย Terraform

1.  เข้าไปที่โฟลเดอร์ `terraform`:
    ```bash
    cd terraform
    ```
2.  สร้างไฟล์ชื่อ `terraform.tfvars` เพื่อกำหนดค่าเฉพาะของคุณ:
    ```hcl
    rds_instance_id = "ชื่อ-db-ของคุณ"
    # slack_webhook_url = "https://hooks.slack.com/services/..." (ใส่หรือไม่ก็ได้)
    ```
3.  รันคำสั่งติดตั้งตามลำดับ:
    ```bash
    terraform init    # เตรียมความพร้อม
    terraform plan    # ตรวจสอบความถูกต้อง
    terraform apply   # ติดตั้งจริง (พิมพ์ 'yes' เมื่อระบบถาม)
    ```

---

## ขั้นตอนที่ 4: ตรวจสอบผลการติดตั้ง (Verification)

1.  ไปที่ **AWS Console** > **Lambda**
2.  คุณจะเห็น Function ชื่อ `rds-auto-scheduler`
3.  ไปที่ **EventBridge** > **Rules**
4.  คุณจะเห็น 2 กฎ (Rules) คือ `rds-start-rule` (รันตอน 09:00น.) และ `rds-stop-rule` (รันตอน 18:00น.)

---

## ขั้นตอนที่ 5: การใช้งาน SSM Runbook (ทางเลือก)

หากคุณต้องการสั่ง Open/Close ด้วยตนเองผ่าน UI ที่สวยงามของ AWS:

1.  ที่ **AWS Console** ไปที่ **Systems Manager** > **Shared Resources** > **Documents**
2.  เลือก **Create Document** > **Automation**
3.  Copy เนื้อหาจากไฟล์ `aws/ssm-runbook.json` ไปวางในโหมด JSON
4.  รัน Document นี้ได้ทุกเมื่อที่ต้องการสั่ง Start หรือ Stop ทันที

---

## การจัดการกรณีพิเศษ (Manual Override)

หากทีมต้องทำงานล่วงเวลา (OT) และไม่อยากให้เครื่องปิดเองตอน 18:00น.:

1.  ไปที่ **Lambda** > `rds-auto-scheduler` > **Configuration** > **Environment variables**
2.  แก้ไข `MANUAL_OVERRIDE` เป็น `true`
3.  เมื่อทำงานเสร็จแล้ว อย่าลืมเปลี่ยนกลับเป็น `false` เพื่อเริ่มระบบประหยัดเงินอีกครั้ง

---

## สรุปค่าใช้จ่ายที่ลดได้ (Cost Optimization)

ด้วยระบบนี้ เครื่องจะรันเพียง 9 ชั่วโมงต่อวันในวันธรรมดา (45 ชม./สัปดาห์) แทนที่จะรัน 168 ชม.

- **ค่าใช้จ่ายเดิม**: ~$18.00 ต่อเดือน
- **ค่าใช้จ่ายใหม่**: ~$5.85 ต่อเดือน
- **ประหยัดเงินได้**: **~67%** หรือมากกว่า 400 บาทต่อเดือนต่อหนึ่งฐานข้อมูล!
