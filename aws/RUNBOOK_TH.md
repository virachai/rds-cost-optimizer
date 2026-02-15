# คู่มือการติดตั้งบน AWS: RDS Cost Optimizer (ทีละขั้นตอน)

คู่มือนี้จะอธิบายขั้นตอนการตั้งค่า **Hybrid RDS Cost Optimizer** โดยใช้ AWS Management Console

---

## ขั้นตอนที่ 1: การตั้งค่า IAM Role

- **ชื่อ Role:** `RDSCostOptimizerLambdaRole`
- **ชื่อ Policy:** `RDSCostOptimizerPolicy`

1. ไปที่ **IAM Console** > **Roles** > **Create role**
2. เลือก **AWS service** และเลือก Use case เป็น **Lambda**
3. ข้ามหน้า "Add permissions" ไปก่อนแล้วคลิก **Next**
4. ตั้งชื่อ Role ว่า **`RDSCostOptimizerLambdaRole`**
5. เมื่อสร้างเสร็จแล้ว ให้เลือก Role นั้น แล้วคลิก **Add permissions** > **Create inline policy**
6. เปลี่ยนไปที่แถบ **JSON** แล้ววางเนื้อหาจากไฟล์ `aws/iam-policy.json`
7. บันทึก Policy ในชื่อ **`RDSCostOptimizerPolicy`**

---

## ขั้นตอนที่ 2: การตั้งค่า VPC Flow Logs

- **ชื่อ Log Group:** `/aws/vpc/rds-flow-logs`
- **ชื่อ Role:** `VPCFlowLogToCWLRole`

1. ไปที่ **VPC Console** > **Your VPCs**
2. เลือก VPC ที่ RDS ของคุณติดตั้งอยู่
3. คลิกแถบ **Flow logs** > **Create flow log**
4. การตั้งค่า:
   - **Filter:** All
   - **Destination:** Send to CloudWatch Logs
   - **Log Group:** `/aws/vpc/rds-flow-logs`
   - **IAM Role:** ตรวจสอบให้แน่ใจว่า Role มีสิทธิ์ในการเขียนลง CloudWatch (ดูรายละเอียดใน `aws/flow-log-iam-policy.json`)

---

## ขั้นตอนที่ 3: การติดตั้ง Lambda Functions

คุณต้องสร้าง Lambda function ทั้งหมด 2 ฟังก์ชัน

### ฟังก์ชัน A: Auto-Stop (หยุดอัตโนมัติ)

- **ชื่อ:** `RDSCostOptimizer-IdleStop`

1. ไปที่ **Lambda Console** > **Create function**
2. ชื่อ: **`RDSCostOptimizer-IdleStop`**
3. Runtime: **Python 3.x**
4. Permissions: เลือก **Use an existing role** และเลือก `RDSCostOptimizerLambdaRole`
5. วางโค้ดจากไฟล์ `src/idle_detection.py`
6. **Environment Variables**:
   - `RDS_INSTANCE_ID`: ID ของ RDS Instance ของคุณ
   - `IDLE_MINUTES`: `60`
7. **Timeout**: ไปที่ **Configuration** > **General configuration** > ตั้งค่า Timeout เป็น **1 นาที**

### ฟังก์ชัน B: Wake-on-Traffic (ปลุกเมื่อมีการใช้งาน)

- **ชื่อ:** `RDSCostOptimizer-WakeOnTraffic`

1. ไปที่ **Lambda Console** > **Create function**
2. ชื่อ: **`RDSCostOptimizer-WakeOnTraffic`**
3. Permissions: เลือก `RDSCostOptimizerLambdaRole`
4. วางโค้ดจากไฟล์ `src/wake_on_traffic.py`
5. **Environment Variables**:
   - `RDS_INSTANCE_ID`: ID ของ RDS Instance ของคุณ
6. **Timeout**: ตั้งค่าเป็น **1 นาที**

---

## ขั้นตอนที่ 4: การตั้งค่า Triggers

### Schedule (สำหรับ Auto-Stop)

- **ชื่อ EventBridge Rule:** `RDSCostOptimizer-HourlyCheck`

1. ในฟังก์ชัน **RDSCostOptimizer-IdleStop** คลิก **Add trigger**
2. เลือก **EventBridge (CloudWatch Events)**
3. ชื่อ: **`RDSCostOptimizer-HourlyCheck`**
4. Rule type: **Schedule expression**
5. Schedule: `cron(0 * * * ? *)` (ตรวจสอบทุกต้นชั่วโมง)

### Traffic Alarm (สำหรับ Wake-on-Traffic)

- **ชื่อ Metric Filter:** `RDSConnectionAttempt`
- **ชื่อ CloudWatch Alarm:** `RDSCostOptimizer-TrafficDetected`

1. ไปที่ **CloudWatch Console** > **Logs** > **Log Groups** > `/aws/vpc/rds-flow-logs`
2. คลิก **Actions** > **Create metric filter**
3. **Filter pattern**:
   `[version, account, eni, source, dest, srcport, destport="5432", protocol="6", packets, bytes, start, end, action, status]`
   _(เปลี่ยน 5432 เป็น 3306 หากใช้ MySQL)_
4. ตั้งชื่อ Metric ว่า `RDSConnectionAttempt`
5. คลิก **Create Alarm** จาก filter นี้:
   - ชื่อ: **`RDSCostOptimizer-TrafficDetected`**
   - **Threshold**: `Static`, `Greater than or equal to 1`
   - **Period**: `1 minute`
6. ตั้งค่า Alarm action:
   - การแจ้งเตือน (Notification): เลือก **None** (ไม่จำเป็น)
   - ไปที่ Lambda **RDSCostOptimizer-WakeOnTraffic** > **Add trigger** > **CloudWatch Alarm** > เลือก Alarm ที่เพิ่งสร้าง

---

## ขั้นตอนที่ 5: การตรวจสอบ (Verification)

1. ตรวจสอบ CloudWatch Logs ของฟังก์ชัน `RDS-Idle-Stop` เพื่อดูว่ามีการดึง Metric หรือไม่
2. ทดลองเชื่อมต่อกับ Endpoint ในขณะที่ DB ปิดอยู่: `nc -zv <endpoint> 5432`
3. สังเกต Log ของ `RDS-Wake-on-Traffic` เพื่อดูว่ามีการสั่งเปิด Database หรือไม่
