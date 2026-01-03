# PRD จดรายรับรายจ่าย
ด้านล่างคือ **PRD (Product Requirements Document)** แยก **Frontend + Backend** สำหรับแอป “จดรายรับรายจ่าย” (Python Flask + SQLite) แนวคิด **Local-First / Offline 100% / ไม่มีโฆษณา / ฟรี** และอิง UX จากภาพที่ส่งมา (ปุ่ม “รายรับ/รายจ่าย”, เลือกหมวด, ฟอร์มเพิ่มรายการ, รายการประจำ, รายงานงบประมาณ vs ใช้จริง)

* * *

PRD — จดรายรับรายจ่าย (Local-First Family Finance)
=========================================================

0) สรุปสินค้า
-------------

**Purpose:** แอปช่วยให้คนในบ้าน “จดเงินจริง” และ “คุมงบร่วมกัน” แบบง่ายที่สุด ใช้ได้ทุกวัน ลื่นไหล  
**Platform:** Android + Windows Desktop (ออฟไลน์ 100%)  
**Tech:** Python Flask (Local API + Serve UI) + SQLite (เข้ารหัสได้)  
**Principles:**

*   **Local-First:** ข้อมูลอยู่ในเครื่องเท่านั้น
*   **Fast Capture:** เพิ่มรายการภายใน 3–7 วินาที
*   **Budget Envelope:** งบรายหมวดเหมือน “ซองเงินดิจิทัล”
*   **Explainable:** ใช้ง่ายสำหรับทุกวัยในบ้าน
*   **Trust:** ไม่มีโฆษณา ไม่ส่งข้อมูลออก

* * *

1) เป้าหมาย (Goals) / ไม่ทำ (Non-Goals)
---------------------------------------

### Goals

1.  จดรายรับ–รายจ่ายได้ต่อเนื่อง (daily habit)
2.  เห็น “เหลืองบ/เกินงบ” ชัดเจนรายหมวด
3.  ทำรายการประจำ ลดงานกรอกซ้ำ
4.  สแกนบิลจากรูป/ไฟล์เพื่อช่วยกรอก (แก้ได้เสมอ)
5.  Backup/Restore/Rollback เพื่อความมั่นใจ
6.  ล็อกแอปด้วย PIN และรองรับ Biometric (ผ่านชั้น OS)

### Non-Goals (ระยะเริ่มต้น)

*   Cloud sync / แชร์ข้ามเครื่องอัตโนมัติ (ทำได้ในอนาคต แต่รุ่นนี้ “ในเครื่อง 100%”)
*   เชื่อมธนาคาร/ดึงสเตทเมนต์อัตโนมัติ
*   โฆษณา/ระบบสมาชิก/สมัครสมาชิก

* * *

2) ผู้ใช้เป้าหมาย (Personas)
----------------------------

1.  **พ่อ/แม่**: อยากรู้รายจ่ายบ้านเดือนนี้ เกินงบหมวดไหน
2.  **ลูกวัยเรียน**: อยากเห็นว่าตัวเองใช้เงินกับอะไร
3.  **คู่รัก/ครอบครัวเล็ก**: วางงบร่วมกันและลดทะเลาะเรื่องเงิน

* * *

3) ขอบเขตฟีเจอร์ (MVP → V1)
---------------------------

### MVP (ต้องมี)

*   เพิ่มรายรับ/รายจ่ายแบบเร็ว (ตามภาพ)
*   หมวดรายรับ/รายจ่าย + ไอคอน + สี
*   รายงานรายวัน/เดือน/ปี + ตามหมวด + กราฟ
*   ตั้งงบรายหมวด (Budget Envelope)
*   รายการประจำ (Recurring)
*   PIN Lock + (Optional) Biometric toggle
*   Backup / Restore / Rollback

### V1 (เสริม)

*   Scan Bill (รูป/ไฟล์/ถ่ายตอนนั้น) + OCR ออฟไลน์ + Suggest หมวด
*   Attachment เก็บรูปบิลแนบรายการ
*   สรุป “Top spenders/Top merchants” ในบ้าน
*   Export CSV/PDF (ในเครื่อง)

* * *

PRD — Frontend (UX/UI)
======================

4) Information Architecture (เมนูหลัก)
--------------------------------------

อิงจาก Bottom Nav ในภาพ:

1.  **หน้าหลัก** (รายการล่าสุด + ปุ่ม รายรับ/รายจ่าย)
2.  **รายการประจำ**
3.  **รายงาน**
4.  **หมวดบัญชี**
5.  **สมาชิก**
6.  **โปรไฟล์/ตั้งค่า**

> หมายเหตุ: “+” Floating Action Button ใช้เพิ่มรายการได้จากทุกหน้า

* * *

5) Screen Requirements (ตามภาพ + เพิ่มส่วนจำเป็น)
-------------------------------------------------

### 5.1 หน้าหลัก (Home / Ledger)

**จากภาพ:** มีปุ่มใหญ่ “รายรับ” สีเขียว, “รายจ่าย” สีแดง, เลือกเดือน, list รายการ, summary แถบล่าง  
**Components**

*   Month selector (มกราคม 2026)
*   Daily grouped list (วันที่ → รายการ)
*   Row: เวลา, รายละเอียด, หมวด (badge), จำนวนเงิน (สีตามประเภท)
*   Summary sticky/footer: รายรับรวม, รายจ่ายรวม, คงเหลือ

**Interactions**

*   กด “รายรับ” → เปิด **Category Picker รายรับ**
*   กด “รายจ่าย” → เปิด **Category Picker รายจ่าย**
*   กดรายการใน list → **Edit Transaction Modal**
*   Swipe row (optional): ลบ/ทำซ้ำ
*   Search (V1): ค้นหาคำ/หมวด/ช่วงวันที่

**Acceptance Criteria**

*   เปิดหน้าแล้ว scroll ลื่น 60fps (รายการ 5,000 แถวต้องยังไหวด้วย pagination)
*   เพิ่มรายการเสร็จแล้ว list อัปเดตทันที

* * *

### 5.2 Category Picker (เลือกรายรับ/รายจ่าย)

**จากภาพ:** modal “เลือกหมวดรายรับ/รายจ่าย” เป็น grid card มีไอคอน  
**Components**

*   Grid หมวด (2–4 คอลัมน์ตามจอ)
*   ปุ่มปิด (X)
*   (V1) ช่องค้นหาหมวด

**Acceptance Criteria**

*   กดหมวดแล้วไปฟอร์มเพิ่มรายการใน 1 tap

* * *

### 5.3 Add Transaction Modal (เพิ่มรายรับ/รายจ่าย)

**จากภาพ:** มี วันที่, เวลา, รายละเอียด, จำนวนเงิน, ปุ่มบันทึก  
**Fields**

*   Type: income/expense (pre-filled จากปุ่ม)
*   Category (pre-filled จาก picker)
*   Date (default วันนี้)
*   Time (default ตอนนี้)
*   Description (optional แต่แนะนำ)
*   Amount (required, numeric, รองรับทศนิยม 2 ตำแหน่ง)
*   Attachment (V1): แนบรูปบิล
*   Scan Bill (V1): ปุ่ม “สแกนบิล” (ถ่ายรูป/เลือกไฟล์)

**Validations**

*   amount > 0
*   ถ้าเกินงบหมวด: แสดง warning “เกินงบ X บาท” แต่ยังบันทึกได้ (ต้องตั้งค่านโยบายได้)

**Acceptance Criteria**

*   บันทึกสำเร็จ ≤ 150ms (บนเครื่องทั่วไป)
*   แตะช่องจำนวนเงินแล้วคีย์แพดตัวเลขขึ้นทันที

* * *

### 5.4 Edit Transaction Modal (แก้ไขรายการ)

**จากภาพ:** มี ประเภท, หมวด, วันที่, เวลา, รายละเอียด, จำนวน, ปุ่ม “ลบ/บันทึก”  
**Acceptance Criteria**

*   แก้แล้วรายงาน/งบต้อง recalculated ทันที
*   ลบต้องมี confirm (กันเผลอ)

* * *

### 5.5 Recurring (รายการประจำ)

**จากภาพ:** หน้า “รายการประจำ” และมีฟอร์ม “รายการประจำ” (ประเภท, หมวด, ความถี่, วันที่, รอบถัดไป ฯลฯ)  
**Core**

*   ความถี่: ทุกวัน/ทุกสัปดาห์/ทุกเดือน
*   ตั้ง “วันของเดือน” (เช่น วันที่ 1)
*   เริ่มต้น (start\_date)
*   รอบถัดไปคำนวณอัตโนมัติ (next\_run\_date)
*   ตั้ง “เตือนก่อนถึงกำหนด” (เช่น 3 วัน)
*   เมื่อถึงกำหนด: สร้าง transaction จริง 1 รายการ (และบันทึกว่า generated\_from\_recurring)

**Acceptance Criteria**

*   ถ้าวันที่ไม่มีในเดือนนั้น (เช่น 31) → rule: เลื่อนไปวันสุดท้ายของเดือน (กำหนดเป็น policy)

* * *

### 5.6 Reports (รายงาน)

**จากภาพ:** กราฟ “งบประมาณ vs ใช้จริง” และ list หมวด พร้อมงบ/ใช้จริง  
**Report Views**

*   Daily / Monthly / Yearly
*   By category
*   Budget vs actual (bar chart)
*   Trend 3–12 เดือน (V1)

**Interactions**

*   แตะหมวด → drill down ไปหน้ารายการของหมวดนั้น (เหมือนภาพ “เดินทาง”)

**Acceptance Criteria**

*   เปิดรายงานเดือนนี้ภายใน 300ms (ใช้ aggregate table/cache)

* * *

### 5.7 Category Detail (รายการตามหมวด)

**จากภาพ:** หน้า “เดินทาง” มี filter ประเภท + หมวด, list และ total  
**Acceptance Criteria**

*   Filter ช่วงวันที่ / ประเภท / คำค้น (V1)

* * *

### 5.8 Members (สมาชิกในบ้าน)

**Local only** แต่รองรับหลายคนในเครื่องเดียว (เช่น พ่อ/แม่/ลูก)

*   เพิ่มสมาชิก: ชื่อเล่น + icon/color
*   รายการสามารถเลือก “เจ้าของรายการ”
*   รายงานแยกตามสมาชิกได้ (optional toggle)

* * *

### 5.9 Profile/Settings

*   PIN lock: เปิด/ปิด, เปลี่ยน PIN
*   Biometric: เปิด/ปิด (ขึ้นกับอุปกรณ์)
*   ภาษา ไทย/อังกฤษ
*   Theme สี
*   Backup/Restore/Rollback
*   About / Privacy (ย้ำ “เก็บในเครื่อง 100%”)

* * *

6) Scan Bill UX (V1)
--------------------

### Flow

1.  ผู้ใช้กด “สแกนบิล” ใน Add Transaction
2.  เลือก:
    *   ถ่ายรูปตอนนี้
*   เลือกรูปจากเครื่อง
*   เลือกไฟล์ (PDF/รูป)
    3.  ระบบประมวลผลออฟไลน์:
    *   อ่าน “ยอดเงิน”, “วันที่”, “ชื่อร้าน/ผู้รับเงิน” (ถ้าพอทำได้)
    4.  เปิดหน้าตรวจทาน:
    *   Amount (suggest)
*   Date (suggest)
*   Merchant/Desc (suggest)
*   Category (suggest + confidence)
    5.  ผู้ใช้กดบันทึก → แนบรูปไว้กับรายการ

### Acceptance Criteria

*   ถ้า OCR พลาด ต้อง “กรอกมือได้ง่าย” และไม่ทำให้ช้า/ค้าง
*   ไม่มีการส่งรูปออกนอกเครื่อง

* * *

PRD — Backend (Flask + SQLite)
==============================

7) Architecture (Local-First)
-----------------------------

**รูปแบบแนะนำ**

*   **Flask = Local App Server**
    *   Serve UI (HTML/JS หรือ WebView/PWA)
    *   Expose REST API: `http://127.0.0.1:<port>/api/...`
*   **SQLite file** เก็บใน device storage (เข้ารหัสได้)
*   **Packaging**
    *   Windows: Bundle เป็น Desktop app (WebView2 wrapper) + run Flask background
    *   Android: WebView wrapper + run Flask embedded (หรือใช้ Python runtime packager)

> จุดสำคัญ: “Biometric” ต้องทำผ่าน native wrapper ของแพลตฟอร์ม แล้วค่อยปลดล็อก key ให้ Flask เปิด DB ได้

* * *

8) Data Model (SQLite Schema)
-----------------------------

ตารางหลัก (แนะนำ)

### 8.1 Core

*   `family` (id, name, created\_at)
*   `member` (id, family\_id, name, color, icon, is\_active)
*   `category` (id, type\[income|expense\], name\_th, name\_en, icon, color, sort\_order, is\_active)
*   `transaction`
    *   (id, family\_id, member\_id nullable, type, category\_id, amount, currency, occurred\_at, note, created\_at, updated\_at, deleted\_at nullable)
*   `budget`
    *   (id, family\_id, category\_id, month\_yyyymm, limit\_amount, rollover\_policy, created\_at)
*   `recurring_rule`
    *   (id, family\_id, member\_id nullable, type, category\_id, amount, note, freq\[daily|weekly|monthly\], day\_of\_week nullable, day\_of\_month nullable, start\_date, next\_run\_date, remind\_days, is\_active)

### 8.2 Attachments / OCR

*   `attachment` (id, transaction\_id, file\_path, mime\_type, sha256, created\_at)
*   `ocr_result` (id, attachment\_id, extracted\_json, engine, confidence, created\_at)

### 8.3 Safety / Ops

*   `snapshot` (id, created\_at, reason, db\_file\_path, checksum) ← สำหรับ rollback
*   `audit_log` (id, actor\_member\_id nullable, action, entity\_type, entity\_id, before\_json, after\_json, created\_at)

* * *

9) API Design (REST)
--------------------

Base: `/api/v1`

### 9.1 Transactions

*   `GET /transactions?from=&to=&type=&category_id=&q=&page=`
*   `POST /transactions`
*   `GET /transactions/{id}`
*   `PATCH /transactions/{id}`
*   `DELETE /transactions/{id}` (soft delete)

### 9.2 Categories

*   `GET /categories?type=income|expense`
*   `POST /categories` (admin-only ในแอป)
*   `PATCH /categories/{id}`

### 9.3 Budgets

*   `GET /budgets?month=YYYYMM`
*   `PUT /budgets/{category_id}?month=YYYYMM` (upsert)
*   `GET /reports/budget-vs-actual?month=YYYYMM`

### 9.4 Reports

*   `GET /reports/summary?from=&to=`
*   `GET /reports/by-category?month=YYYYMM&type=`
*   `GET /reports/trend?months=12` (V1)

### 9.5 Recurring

*   `GET /recurring`
*   `POST /recurring`
*   `PATCH /recurring/{id}`
*   `POST /recurring/run-due` (internal scheduler/manual)
*   `GET /recurring/history` (optional)

### 9.6 Backup / Restore / Rollback

*   `POST /maintenance/backup` → สร้างไฟล์ backup
*   `POST /maintenance/restore` → restore จากไฟล์
*   `POST /maintenance/snapshot` → สร้าง snapshot
*   `POST /maintenance/rollback/{snapshot_id}`

### 9.7 Bill Scan (V1)

*   `POST /scan/upload` (multipart)
*   `POST /scan/ocr/{attachment_id}`
*   `GET /scan/result/{attachment_id}`

* * *

10) Security & Privacy
----------------------

### 10.1 DB Encryption (แนะนำ)

*   ใช้ SQLite แบบเข้ารหัส (เช่น SQLCipher) หรือ file-level encryption
*   Key derivation:
    *   PIN → KDF (เช่น PBKDF2/Argon2) → master key
    *   Biometric: ใช้ OS keystore ปลดล็อก master key (ตัว wrapper ทำให้)

### 10.2 App Lock Flow

*   ตอนเปิดแอป: ต้อง unlock ก่อนถึงเปิด DB
*   ถ้าล็อก: API ตอบ `401 LOCKED` และ UI แสดงหน้าปลดล็อก

### 10.3 Data handling

*   ไม่มี telemetry
*   log ต้องไม่พิมพ์ข้อมูลการเงินลง plain text

* * *

11) Performance Requirements
----------------------------

*   รายการ 10,000 รายการ: เปิดหน้า Home ≤ 400ms ด้วย pagination + index
*   Report เดือนปัจจุบัน: ≤ 300ms ด้วย aggregate
*   Write transaction: ≤ 150ms

**DB Index แนะนำ**

*   `transaction(occurred_at)`
*   `transaction(category_id, occurred_at)`
*   `transaction(type, occurred_at)`
*   `budget(month_yyyymm, category_id)`
*   `recurring_rule(next_run_date, is_active)`

* * *

12) Background Jobs (Local Scheduler)
-------------------------------------

*   ทุกครั้งที่เปิดแอป หรือวันละครั้ง:
    *   run recurring due → generate transactions
    *   สร้าง snapshot อัตโนมัติ (เช่น วันละครั้งหรือก่อน restore)

* * *

13) Error Handling & Data Integrity
-----------------------------------

*   ทุก write สำคัญต้องอยู่ใน transaction (BEGIN/COMMIT)
*   ป้องกันข้อมูลซ้ำจาก recurring: unique key `(recurring_rule_id, run_date)`
*   Soft delete เพื่อกัน “ลบพลาด” + rollback ได้

* * *

14) QA / Test Plan (ย่อ)
------------------------

*   Unit test: budget calculation, recurring next\_run\_date, reports aggregation
*   Integration test: create/edit/delete transaction แล้ว report เปลี่ยนถูกต้อง
*   Security test: lock/unlock แล้ว DB เปิดไม่ได้เมื่อ locked
*   OCR test (V1): ภาพชัด/ไม่ชัด/ยอดเงินหลายตำแหน่ง

* * *

Deliverables ที่แนะนำให้ทำต่อทันที (เพื่อให้พัฒนาไว)
====================================================

1.  **Design System เล็กๆ**: สีรายรับ/รายจ่าย, icon set, spacing, typography
2.  **API Contract + Sample JSON** สำหรับทุก endpoint
3.  **DB Migration strategy** (Alembic/Flask-Migrate) แม้เป็น SQLite ก็ต้องมี
4.  **Budget Calculation Spec** (policy เกินงบ/rollover/งบ 0 หมายถึงอะไร)
5.  **Packaging Spec** แยก Android/Windows (WebView wrapper + Flask local)

* * *

ถ้าคุณต้องการ ผมทำให้ต่อได้เลยเป็น “แพ็กเอกสารส่ง Dev” แบบที่คุณชอบ เช่น

*   `PRD_FRONTEND.md`
*   `PRD_BACKEND.md`
*   `API_CONTRACT.json`
*   `DB_SCHEMA.sql`
*   `USER_FLOWS.md` (Flow ลูกศรแบบเข้าใจง่าย)

และผมจะยึดหน้าจอ/โฟลว์ตามภาพที่คุณทำไว้ให้ “เหมือนของจริง” มากที่สุดครับ

## Response:
ได้เลยปอนด์ — ด้านล่างผมทำเป็นไฟล์สไตล์ **PRD-Frontend.md** และ **PRD-Backend.md** (เน้นตามหน้าจอที่ส่งมา: หมวดบัญชี, เพิ่มหมวด, สมาชิก/โปรเจค, Line Login + Project Code) และเพิ่ม requirement “เป็นทั้ง Chatbot + หน้าเว็บ CRUD” บน **Python Flask + SQLite**

* * *

PRD-Frontend.md
---------------

PRD — Frontend (Web)
====================

Product: จดรายรับรายจ่าย (LINE Auth + Web CRUD + Chatbot Companion)
--------------------------------------------------------------------------

### 1) เป้าหมาย

*   ผู้ใช้ล็อกอินด้วย LINE แล้วใช้งานเว็บเพื่อ **บันทึกรายรับ/รายจ่าย + งบประมาณ + รายการประจำ**
*   มี “โปรเจค/ครอบครัว” (Project/Household) เพื่อแยกบัญชีหลายบ้าน/หลายกลุ่ม
*   มี “สมาชิก” ในโปรเจค พร้อม Role (เช่น เจ้าของ/สมาชิก)
*   UX ต้อง “จดได้ไวเหมือนแอป” (โมดอล เพิ่มรายการ, เลือกหมวดเร็ว, แก้ไข/ลบง่าย)
*   เชื่อมกับ LINE Chatbot: พิมพ์คุยได้ + CRUD ผ่านแชทได้ (แต่หน้าเว็บคือศูนย์กลางจัดการ)

### 2) ผู้ใช้ (Personas)

*   เจ้าของบ้าน (Owner): สร้างโปรเจค เชิญสมาชิก ตั้งงบ ดูรายงาน
*   สมาชิก (Member): จดรายจ่าย/รายรับของตัวเอง ดูสรุป
*   ผู้ดูแล (Admin — optional): จัดการหมวด/งบ/รายการประจำ

### 3) Information Architecture (ตาม bottom nav)

1.  **หน้าหลัก** (Ledger)
2.  **รายการประจำ** (Recurring)
3.  **รายงาน** (Reports)
4.  **หมวดบัญชี** (Categories) ← ตามภาพ
5.  **สมาชิก** (Members + Projects) ← ตามภาพ
6.  **โปรไฟล์/ตั้งค่า** (Profile/Settings)

Global:

*   FAB “+” เพิ่มรายการ (เหมือนในภาพ)
*   Top bar: สลับ “รายรับ/รายจ่าย” + ปุ่ม “งบประมาณ” (ตามภาพหมวดบัญชี)

* * *

4) Screen Specs
---------------

### 4.1 Login (LINE)

**Entry points**

*   `/login` → ปุ่ม “Login with LINE”
*   หลัง login กลับมาที่ `/app`

**States**

*   Not logged-in → เห็นหน้า Landing + Login CTA
*   Logged-in but no project → redirect ไป `/members` (หน้าโปรเจค/ครอบครัว) ให้สร้างหรือเข้าร่วม

**Acceptance**

*   login สำเร็จแล้วได้ session/token และกลับหน้าเดิมที่ผู้ใช้ต้องการ

* * *

### 4.2 Members (สมาชิก) + Projects (โปรเจค)

อิงจากภาพ:

*   การ์ด “ครอบครัวของฉัน” + ปุ่ม “เพิ่มสมาชิกได้ 2 คน”
*   ส่วน “โปรเจคของฉัน” พร้อมปุ่มสร้างโปรเจค และแสดงโค้ด project

#### 4.2.1 Project List / Current Project Card

**Components**

*   Current Project card (ชื่อโปรเจค + จำนวนสมาชิก (x/y))
*   ปุ่ม: Edit (ไอคอนดินสอ) / Switch project (dropdown)
*   CTA: “สร้างโปรเจค” / “เข้าร่วมโปรเจค”

#### 4.2.2 Modal: เชิญสมาชิก (Invite Member)

อิงจากภาพ modal “เชิญสมาชิก”  
**Fields**

*   Display Name (required)
*   Nickname (optional)
*   Role dropdown (default: สมาชิก, owner-only สร้าง owner ได้)
*   Button: ยืนยันเพิ่มคน

**Rules**

*   Owner เท่านั้นที่เชิญได้
*   จำกัดจำนวนสมาชิกตาม policy (MVP อาจ 2–5 คน)

#### 4.2.3 Modal: สร้างโปรเจค

อิงจากภาพ “สร้างโปรเจค”  
**Fields**

*   ชื่อโปรเจค (required)
*   Project Code (auto-generated, copy ได้)
*   Hint: ใช้สำหรับพิมพ์ใน LINE เช่น #project… เพื่อเข้าร่วม
*   Button: สร้าง

**Acceptance**

*   สร้างแล้ว set เป็น current project
*   มีปุ่ม copy code

* * *

### 4.3 Categories (หมวดบัญชี)

อิงจากภาพ: list หมวดรายจ่าย/รายรับ + ตัวเลข “ใช้ไป: …” และปุ่ม “งบประมาณ”

**Top Controls**

*   Toggle: รายรับ / รายจ่าย
*   Button: งบประมาณ (ไปหน้า/โมดอลตั้งงบ)

**List Row**

*   Icon + ชื่อหมวด
*   Subtext: “ใช้ไป: X.XX”
*   Right: งบ/ใช้จริง หรือ 0.00 (ตามภาพ)

**Actions**

*   FAB “+” → Modal เพิ่มหมวด
*   Tap row → Drilldown รายการหมวดนั้น (filter อัตโนมัติ)

#### 4.3.1 Modal: เพิ่มหมวดรายจ่าย/รายรับ

อิงจากภาพ “เพิ่มหมวดรายจ่าย”  
**Fields**

*   ชื่อหมวด (required)
*   Icon picker (grid + scroll)
*   Color (optional V1)
*   Button: บันทึก / ยกเลิก

**Validation**

*   ชื่อซ้ำในประเภทเดียวกันแจ้งเตือน (แต่อนุญาตได้ถ้าตั้งค่า)

* * *

### 4.4 Ledger (หน้าหลักรายการ)

**Top**

*   ปุ่มใหญ่ “รายรับ” / “รายจ่าย”
*   Month selector  
    **List**
*   Group by date
*   Tap row → edit modal (type, category, date/time, note, amount, delete)  
    **Footer Summary**
*   รายรับรวม / รายจ่ายรวม / คงเหลือ

* * *

### 4.5 Add/Edit Transaction Modal

*   ประเภท (รายรับ/รายจ่าย)
*   หมวด (dropdown/search)
*   วันที่/เวลา
*   รายละเอียด
*   จำนวนเงิน
*   แนบรูป/สแกนบิล (V1)

* * *

### 4.6 Budget (งบประมาณรายเดือน)

**View**

*   เลือกเดือน
*   รายการหมวด + งบ + ใช้จริง + คงเหลือ/เกินงบ
*   กราฟ Budget vs Actual (เหมือนภาพรายงาน)

**Actions**

*   ตั้งงบรายหมวด (inline edit หรือ modal)
*   Policy: เตือนเมื่อใช้ถึง 80% และเมื่อเกินงบ

* * *

### 4.7 Reports (รายงาน)

*   Daily / Monthly / Yearly
*   By Category
*   Budget vs Actual
*   Drilldown ตามหมวด/ช่วงเวลา

* * *

5) Chatbot Entry (UI ที่เว็บต้องรองรับ)
---------------------------------------

*   หน้า `/help/line` อธิบายคำสั่งหลัก + ปุ่ม “เชื่อม LINE” (ถ้ายังไม่เชื่อม)
*   หน้า `/projects/{id}/line-link` แสดง **Project Code** + QR (optional) + วิธี join

* * *

6) Requirements: UX/Quality
---------------------------

*   CRUD สำคัญต้องทำผ่าน modal (ลดการเปลี่ยนหน้า)
*   ทุกหน้าใช้ pagination/virtual list เมื่อข้อมูลเยอะ
*   รองรับมือถือเป็นหลัก (responsive)
*   i18n ไทย/อังกฤษ (labels แยกไฟล์)

* * *

7) Acceptance Criteria (MVP)
----------------------------

*   ล็อกอิน LINE ได้ และผูกกับผู้ใช้ในระบบ
*   สร้างโปรเจคได้, เชิญสมาชิกได้, สลับโปรเจคได้
*   เพิ่ม/แก้/ลบ รายรับรายจ่ายได้
*   เพิ่มหมวดได้
*   ตั้งงบรายเดือนต่อหมวดได้
*   Chatbot สามารถทำ CRUD ขั้นพื้นฐานได้ (เพิ่มรายการ + ดูสรุป)

* * *

PRD-Backend.md
--------------

PRD — Backend (Flask + SQLite + LINE Auth + LINE Bot)
=====================================================

### 1) เป้าหมายระบบ

*   เป็น Backend สำหรับเว็บ (SPA/SSR ก็ได้) + Webhook สำหรับ LINE Bot
*   รองรับ Multi-Project (หลายครอบครัว/หลายกลุ่ม)
*   มี RBAC ง่ายๆ (Owner/Member)
*   ข้อมูลเก็บใน SQLite (ต่อโปรเจคหรือรวมไฟล์เดียวได้)
*   ปลอดภัย: OAuth2 (LINE Login), session/JWT, webhook signature verify

* * *

2) High-level Architecture
--------------------------

**Components**

1.  Flask Web App
    *   Web routes (serve UI)
    *   REST API `/api/v1/*`
2.  SQLite
    *   schema + migrations
3.  LINE Login (OAuth2)
    *   authorize → callback → get profile → create user
4.  LINE Messaging API (Bot)
    *   Webhook endpoint `/line/webhook`
    *   verify signature
    *   parse message → intent → CRUD ผ่าน service layer

**Key idea**

*   “เว็บ” และ “บอท” ใช้ชุด service เดียวกัน (TransactionService / BudgetService / ProjectService) เพื่อความถูกต้อง一致

* * *

3) Data Model (SQLite Schema)
-----------------------------

### 3.1 Auth / Users

*   `user`
    *   id (pk)
    *   line\_user\_id (unique)
    *   display\_name
    *   picture\_url (nullable)
    *   created\_at, updated\_at
*   `session`
    *   id, user\_id, token\_hash, expires\_at, created\_at

### 3.2 Projects / Membership

*   `project`
    *   id (pk)
    *   name
    *   project\_code (unique, short)
    *   owner\_user\_id
    *   created\_at
*   `project_member`
    *   id
    *   project\_id
    *   user\_id
    *   role (owner|member)
    *   nick\_name (nullable)
    *   is\_active
    *   joined\_at

### 3.3 Accounting

*   `category`
    *   id
    *   project\_id
    *   type (income|expense)
    *   name\_th
    *   name\_en (nullable)
    *   icon\_key
    *   color (nullable)
    *   sort\_order
    *   is\_active
*   `transaction`
    *   id
    *   project\_id
    *   created\_by\_user\_id
    *   type (income|expense)
    *   category\_id
    *   amount (decimal as integer satang recommended)
    *   note (nullable)
    *   occurred\_at (datetime)
    *   created\_at, updated\_at
    *   deleted\_at (soft delete)
*   `budget`
    *   id
    *   project\_id
    *   category\_id
    *   month\_yyyymm (e.g., 202601)
    *   limit\_amount (satang)
    *   created\_at, updated\_at

### 3.4 Recurring

*   `recurring_rule`
    *   id, project\_id, created\_by\_user\_id
    *   type, category\_id, amount, note
    *   freq (daily|weekly|monthly)
    *   day\_of\_week (0-6 nullable)
    *   day\_of\_month (1-31 nullable)
    *   start\_date, next\_run\_date
    *   remind\_days
    *   is\_active
*   `recurring_run`
    *   id
    *   recurring\_rule\_id
    *   run\_date
    *   transaction\_id
    *   created\_at
    *   UNIQUE(recurring\_rule\_id, run\_date)

### 3.5 Audit

*   `audit_log`
    *   id, project\_id, user\_id
    *   action (CREATE\_TXN/UPDATE\_TXN/DELETE\_TXN/...)
    *   entity\_type, entity\_id
    *   before\_json, after\_json
    *   created\_at

* * *

4) API Endpoints (REST)
-----------------------

### 4.1 Auth

*   `GET /auth/line/login` → redirect to LINE authorize
*   `GET /auth/line/callback` → exchange code → get profile → create/update user → create session → redirect `/app`
*   `POST /auth/logout`

### 4.2 Projects

*   `GET /api/v1/projects`
*   `POST /api/v1/projects` (create; owner=me)
*   `POST /api/v1/projects/join` (join by project\_code)
*   `GET /api/v1/projects/{project_id}`
*   `POST /api/v1/projects/{project_id}/switch` (set current project in session)

### 4.3 Members

*   `GET /api/v1/projects/{project_id}/members`
*   `POST /api/v1/projects/{project_id}/members/invite` (owner only)
*   `PATCH /api/v1/projects/{project_id}/members/{member_id}` (role/nickname)
*   `DELETE /api/v1/projects/{project_id}/members/{member_id}` (deactivate)

### 4.4 Categories

*   `GET /api/v1/projects/{project_id}/categories?type=expense|income`
*   `POST /api/v1/projects/{project_id}/categories`
*   `PATCH /api/v1/projects/{project_id}/categories/{category_id}`
*   `DELETE /api/v1/projects/{project_id}/categories/{category_id}` (soft)

### 4.5 Transactions

*   `GET /api/v1/projects/{project_id}/transactions?from=&to=&type=&category_id=&q=&page=`
*   `POST /api/v1/projects/{project_id}/transactions`
*   `GET /api/v1/projects/{project_id}/transactions/{id}`
*   `PATCH /api/v1/projects/{project_id}/transactions/{id}`
*   `DELETE /api/v1/projects/{project_id}/transactions/{id}`

### 4.6 Budgets

*   `GET /api/v1/projects/{project_id}/budgets?month=YYYYMM`
*   `PUT /api/v1/projects/{project_id}/budgets/{category_id}?month=YYYYMM` (upsert)
*   `GET /api/v1/projects/{project_id}/reports/budget-vs-actual?month=YYYYMM`

### 4.7 Reports

*   `GET /api/v1/projects/{project_id}/reports/summary?from=&to=`
*   `GET /api/v1/projects/{project_id}/reports/by-category?month=YYYYMM&type=`
*   `GET /api/v1/projects/{project_id}/reports/trend?months=12`

* * *

5) LINE Bot (Webhook + Commands)
--------------------------------

### 5.1 Webhook

*   `POST /line/webhook`
    *   verify `X-Line-Signature`
    *   handle event types: message, postback
    *   map `line_user_id` → user
    *   resolve current project:
        *   ถ้าข้อความมี `#<project_code>` ให้ switch/join
        *   ไม่งั้นใช้ last\_used\_project ใน session store (ต้องมีตาราง `user_pref` หรือ field ใน user)

### 5.2 Command Spec (MVP)

**1) เพิ่มรายจ่าย**

*   ผู้ใช้พิมพ์: `จ่าย 350 เดินทาง ค่ารถ`
*   Bot ตอบ: “บันทึกแล้ว ✅ 350 บาท หมวดเดินทาง”

**2) เพิ่มรายรับ**

*   `รับ 15000 เงินเดือน`

**3) สรุปวันนี้/เดือนนี้**

*   `สรุปวันนี้`
*   `สรุปเดือนนี้`

**4) ดูงบหมวด**

*   `งบ เดินทาง`
*   ตอบ: งบ/ใช้จริง/คงเหลือ

**5) แก้ไขล่าสุด**

*   `แก้ล่าสุด 300` (เปลี่ยน amount)
*   หรือ “ยกเลิกล่าสุด”

> Intent parsing (ไทย) ใช้ rule-based ก่อน (regex) แล้วค่อยเพิ่ม NLP ภายหลัง

### 5.3 Postback UI (optional)

*   ปุ่ม quick replies: “เพิ่มรายจ่าย”, “เพิ่มรายรับ”, “สรุปเดือนนี้”
*   เลือกหมวดแบบ carousel (ดึงจาก DB ตาม project)

* * *

6) Business Rules
-----------------

*   Amount เก็บเป็น “สตางค์” (int) เพื่อไม่พังเรื่อง float
*   Soft delete ทุก entity สำคัญ
*   Owner เท่านั้น: สร้าง/ลบโปรเจค, เชิญสมาชิก, แก้ role
*   Category เป็น per-project (แต่มี default template ตอนสร้างโปรเจค)
*   Budget เป็น per-month per-category
*   Recurring:
    *   run-due สร้าง transaction จริง และกันซ้ำด้วย unique constraint

* * *

7) Security
-----------

*   LINE OAuth: ตรวจ state, ใช้ HTTPS
*   Session:
    *   cookie httpOnly + sameSite
    *   หรือ JWT (แต่ถ้า local web ง่ายสุด cookie session)
*   LINE Webhook:
    *   verify signature ทุกครั้ง
*   RBAC middleware:
    *   ตรวจ membership ก่อนเข้าถึง project resources

* * *

8) Performance
--------------

*   Index:
    *   transaction(project\_id, occurred\_at)
    *   transaction(project\_id, category\_id, occurred\_at)
    *   budget(project\_id, month\_yyyymm)
*   Reports ใช้ aggregate query + cache (optional)

* * *

9) Observability (local-friendly)
---------------------------------

*   audit\_log สำหรับการเปลี่ยนแปลงสำคัญ
*   error log ไม่เก็บข้อมูลส่วนตัวเกินจำเป็น

* * *

10) Acceptance Criteria (MVP)
-----------------------------

*   LINE Login สำเร็จ → เข้าหน้าเว็บได้
*   สร้างโปรเจค + ได้ project\_code
*   เชิญสมาชิก/เข้าร่วมโปรเจคด้วย code ได้
*   CRUD หมวด + CRUD รายการ + ตั้งงบรายเดือน
*   LINE Bot:
    *   เพิ่มรายรับ/รายจ่ายด้วยข้อความไทยแบบสั้นได้
    *   ขอ “สรุปวันนี้/เดือนนี้” ได้
    *   ตรวจ “งบหมวด” ได้

* * *

ถ้าปอนด์อยากให้ “พร้อมลงมือทำทันที” ผมทำต่อให้เป็นชุดเอกสาร dev-ready ได้เลยแบบไฟล์จริง เช่น

*   `API_CONTRACT.json` (request/response ตัวอย่างทุก endpoint)
*   `COMMAND_SPECS_TH.md` (แพทเทิร์นคำสั่งแชท + regex intent)
*   `DB_SCHEMA.sql` + `MIGRATION_PLAN.md` (SQLite migrations)
*   `UI_ROUTES.md` (mapping หน้า → endpoint ที่เรียก)

## Response:
```json
{
  "meta": {
    "product": "จดรายรับรายจ่าย",
    "version": "1.0.0",
    "base_url": "http://localhost:5000",
    "api_base": "/api/v1",
    "auth": {
      "type": "cookie_session_or_bearer",
      "note": "เว็บแนะนำใช้ Cookie Session (HttpOnly). ถ้าใช้ Bearer ให้ส่ง Authorization: Bearer <token>"
    },
    "money": {
      "storage": "integer_satang",
      "display": "THB",
      "example": "350.00 THB => 35000 satang"
    },
    "pagination": {
      "default_page_size": 50,
      "max_page_size": 200
    },
    "common_headers": {
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    "errors": {
      "standard_error_shape": {
        "error": {
          "code": "string",
          "message": "string",
          "details": {},
          "request_id": "string"
        }
      },
      "common_codes": [
        "UNAUTHORIZED",
        "FORBIDDEN",
        "NOT_FOUND",
        "VALIDATION_ERROR",
        "CONFLICT",
        "RATE_LIMITED",
        "INTERNAL_ERROR"
      ]
    }
  },
  "schemas": {
    "User": {
      "id": "usr_123",
      "line_user_id": "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "display_name": "Pond",
      "picture_url": "https://profile.line-scdn.net/xxx",
      "created_at": "2026-01-03T05:32:00Z",
      "updated_at": "2026-01-03T05:32:00Z"
    },
    "Project": {
      "id": "prj_123",
      "name": "ครอบครัวคุณ Pond",
      "project_code": "aoq0f2i0",
      "owner_user_id": "usr_123",
      "member_count": 2,
      "created_at": "2026-01-03T05:33:00Z"
    },
    "ProjectMember": {
      "id": "mem_123",
      "project_id": "prj_123",
      "user_id": "usr_123",
      "display_name": "Pond Titipong",
      "nick_name": "ปอนด์",
      "role": "owner",
      "is_active": true,
      "joined_at": "2026-01-03T05:33:10Z"
    },
    "Category": {
      "id": "cat_123",
      "project_id": "prj_123",
      "type": "expense",
      "name_th": "เดินทาง",
      "name_en": "Travel",
      "icon_key": "ic_bus",
      "color": "#E74C3C",
      "sort_order": 10,
      "is_active": true,
      "created_at": "2026-01-03T05:35:00Z",
      "updated_at": "2026-01-03T05:35:00Z"
    },
    "Transaction": {
      "id": "txn_123",
      "project_id": "prj_123",
      "created_by_user_id": "usr_123",
      "type": "expense",
      "category_id": "cat_123",
      "amount_satang": 35000,
      "currency": "THB",
      "note": "ค่าเดินทาง",
      "occurred_at": "2026-01-03T03:54:59Z",
      "created_at": "2026-01-03T05:36:10Z",
      "updated_at": "2026-01-03T05:36:10Z",
      "deleted_at": null
    },
    "Budget": {
      "id": "bud_123",
      "project_id": "prj_123",
      "category_id": "cat_123",
      "month_yyyymm": 202601,
      "limit_amount_satang": 300000,
      "created_at": "2026-01-03T05:40:00Z",
      "updated_at": "2026-01-03T05:40:00Z"
    },
    "ReportBudgetVsActualRow": {
      "category_id": "cat_123",
      "category_name_th": "เดินทาง",
      "type": "expense",
      "budget_limit_satang": 300000,
      "actual_spent_satang": 35000,
      "remaining_satang": 265000,
      "status": "UNDER_BUDGET"
    },
    "RecurringRule": {
      "id": "rr_123",
      "project_id": "prj_123",
      "created_by_user_id": "usr_123",
      "type": "expense",
      "category_id": "cat_food",
      "amount_satang": 150000,
      "currency": "THB",
      "note": "อาหารประจำ",
      "freq": "monthly",
      "day_of_week": null,
      "day_of_month": 1,
      "start_date": "2026-01-03",
      "next_run_date": "2026-02-01",
      "remind_days": 3,
      "is_active": true,
      "created_at": "2026-01-03T05:45:00Z",
      "updated_at": "2026-01-03T05:45:00Z"
    }
  },
  "endpoints": [
    {
      "name": "Auth - Start LINE Login",
      "method": "GET",
      "path": "/auth/line/login",
      "description": "Redirect ไป LINE OAuth authorize (ไม่ใช่ JSON)",
      "request": {
        "headers": {},
        "query": {
          "redirect": "/app"
        },
        "body": null
      },
      "responses": [
        {
          "status": 302,
          "headers": {
            "Location": "https://access.line.me/oauth2/v2.1/authorize?...",
            "Set-Cookie": "session=...; HttpOnly; SameSite=Lax"
          },
          "body": null
        }
      ]
    },
    {
      "name": "Auth - LINE Callback",
      "method": "GET",
      "path": "/auth/line/callback",
      "description": "LINE redirect กลับมา พร้อม code/state แล้วระบบแลก token + โปรไฟล์ สร้าง user/session",
      "request": {
        "query": {
          "code": "AUTH_CODE_FROM_LINE",
          "state": "CSRF_STATE"
        },
        "body": null
      },
      "responses": [
        {
          "status": 302,
          "headers": {
            "Location": "/app",
            "Set-Cookie": "session=...; HttpOnly; SameSite=Lax"
          },
          "body": null
        },
        {
          "status": 400,
          "body": {
            "error": {
              "code": "VALIDATION_ERROR",
              "message": "Invalid state or missing code",
              "details": {},
              "request_id": "req_001"
            }
          }
        }
      ]
    },
    {
      "name": "Auth - Logout",
      "method": "POST",
      "path": "/auth/logout",
      "description": "ล้าง session",
      "request": {
        "headers": {},
        "body": {}
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "ok": true
          }
        }
      ]
    },
    {
      "name": "Me - Get Current User",
      "method": "GET",
      "path": "/api/v1/me",
      "description": "ข้อมูลผู้ใช้ที่ล็อกอินอยู่ + current_project_id",
      "request": {
        "headers": {}
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "user": {
              "id": "usr_123",
              "display_name": "Pond",
              "picture_url": "https://profile.line-scdn.net/xxx"
            },
            "current_project_id": "prj_123"
          }
        },
        {
          "status": 401,
          "body": {
            "error": {
              "code": "UNAUTHORIZED",
              "message": "Login required",
              "details": {},
              "request_id": "req_002"
            }
          }
        }
      ]
    },
    {
      "name": "Projects - List",
      "method": "GET",
      "path": "/api/v1/projects",
      "description": "รายชื่อโปรเจคที่ user เป็นสมาชิก",
      "request": {
        "headers": {}
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "projects": [
              {
                "id": "prj_123",
                "name": "ครอบครัวคุณ Pond",
                "project_code": "aoq0f2i0",
                "member_count": 2,
                "role": "owner",
                "created_at": "2026-01-03T05:33:00Z"
              }
            ]
          }
        }
      ]
    },
    {
      "name": "Projects - Create",
      "method": "POST",
      "path": "/api/v1/projects",
      "description": "สร้างโปรเจคใหม่ และ set เป็น current project",
      "request": {
        "headers": {},
        "body": {
          "name": "ทริปเชียงใหม่",
          "project_code": "aoq0f2i0"
        }
      },
      "responses": [
        {
          "status": 201,
          "body": {
            "project": {
              "id": "prj_999",
              "name": "ทริปเชียงใหม่",
              "project_code": "aoq0f2i0",
              "owner_user_id": "usr_123",
              "member_count": 1,
              "created_at": "2026-01-03T05:50:00Z"
            },
            "current_project_id": "prj_999"
          }
        },
        {
          "status": 409,
          "body": {
            "error": {
              "code": "CONFLICT",
              "message": "project_code already exists",
              "details": {
                "field": "project_code"
              },
              "request_id": "req_003"
            }
          }
        }
      ]
    },
    {
      "name": "Projects - Join by Code",
      "method": "POST",
      "path": "/api/v1/projects/join",
      "description": "เข้าร่วมโปรเจคด้วย project_code (ใช้ได้ทั้งเว็บและ LINE)",
      "request": {
        "body": {
          "project_code": "aoq0f2i0"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "joined": true,
            "project": {
              "id": "prj_999",
              "name": "ทริปเชียงใหม่",
              "project_code": "aoq0f2i0",
              "member_count": 2
            },
            "current_project_id": "prj_999"
          }
        },
        {
          "status": 404,
          "body": {
            "error": {
              "code": "NOT_FOUND",
              "message": "Project not found",
              "details": {},
              "request_id": "req_004"
            }
          }
        }
      ]
    },
    {
      "name": "Projects - Switch Current",
      "method": "POST",
      "path": "/api/v1/projects/{project_id}/switch",
      "description": "ตั้ง current project ใน session",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "body": {}
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "current_project_id": "prj_123"
          }
        },
        {
          "status": 403,
          "body": {
            "error": {
              "code": "FORBIDDEN",
              "message": "Not a member of this project",
              "details": {},
              "request_id": "req_005"
            }
          }
        }
      ]
    },
    {
      "name": "Members - List",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/members",
      "description": "รายชื่อสมาชิกในโปรเจค",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "members": [
              {
                "id": "mem_123",
                "user_id": "usr_123",
                "display_name": "Pond Titipong",
                "nick_name": "ปอนด์",
                "role": "owner",
                "is_active": true
              },
              {
                "id": "mem_124",
                "user_id": "usr_456",
                "display_name": "Mom",
                "nick_name": "แม่",
                "role": "member",
                "is_active": true
              }
            ]
          }
        }
      ]
    },
    {
      "name": "Members - Invite (Owner Only)",
      "method": "POST",
      "path": "/api/v1/projects/{project_id}/members/invite",
      "description": "เชิญสมาชิก (สร้าง invite token หรือเพิ่มสมาชิกให้ทันทีถ้ามี user_id)",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "body": {
          "display_name": "น้อง",
          "nick_name": "น้อง",
          "role": "member"
        }
      },
      "responses": [
        {
          "status": 201,
          "body": {
            "invite": {
              "invite_code": "inv_abc123",
              "expires_at": "2026-01-10T00:00:00Z",
              "project_id": "prj_123",
              "role": "member"
            },
            "share_text": "เข้าร่วมครอบครัวด้วยโค้ด: inv_abc123 หรือพิมพ์ใน LINE: #project aoq0f2i0"
          }
        },
        {
          "status": 403,
          "body": {
            "error": {
              "code": "FORBIDDEN",
              "message": "Owner only",
              "details": {},
              "request_id": "req_006"
            }
          }
        }
      ]
    },
    {
      "name": "Categories - List",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/categories",
      "description": "ดึงหมวดตามประเภท",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "query": {
          "type": "expense"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "categories": [
              {
                "id": "cat_food",
                "type": "expense",
                "name_th": "อาหาร",
                "icon_key": "ic_food",
                "color": "#E74C3C",
                "sort_order": 1,
                "is_active": true
              },
              {
                "id": "cat_travel",
                "type": "expense",
                "name_th": "เดินทาง",
                "icon_key": "ic_bus",
                "color": "#E74C3C",
                "sort_order": 2,
                "is_active": true
              }
            ]
          }
        }
      ]
    },
    {
      "name": "Categories - Create",
      "method": "POST",
      "path": "/api/v1/projects/{project_id}/categories",
      "description": "เพิ่มหมวดรายรับ/รายจ่าย",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "body": {
          "type": "expense",
          "name_th": "ค่าน้ำดื่ม",
          "name_en": "Water",
          "icon_key": "ic_water",
          "color": "#E74C3C",
          "sort_order": 20
        }
      },
      "responses": [
        {
          "status": 201,
          "body": {
            "category": {
              "id": "cat_777",
              "project_id": "prj_123",
              "type": "expense",
              "name_th": "ค่าน้ำดื่ม",
              "name_en": "Water",
              "icon_key": "ic_water",
              "color": "#E74C3C",
              "sort_order": 20,
              "is_active": true,
              "created_at": "2026-01-03T06:00:00Z",
              "updated_at": "2026-01-03T06:00:00Z"
            }
          }
        },
        {
          "status": 400,
          "body": {
            "error": {
              "code": "VALIDATION_ERROR",
              "message": "name_th is required",
              "details": {
                "field": "name_th"
              },
              "request_id": "req_007"
            }
          }
        }
      ]
    },
    {
      "name": "Transactions - List",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/transactions",
      "description": "ดึงรายการรายรับ/รายจ่ายตามช่วงเวลา/หมวด/ค้นหา",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "query": {
          "from": "2026-01-01",
          "to": "2026-01-31",
          "type": "expense",
          "category_id": "cat_travel",
          "q": "ค่า",
          "page": 1,
          "page_size": 50
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "items": [
              {
                "id": "txn_123",
                "type": "expense",
                "category_id": "cat_travel",
                "amount_satang": 35000,
                "currency": "THB",
                "note": "ค่าเดินทาง",
                "occurred_at": "2026-01-03T03:54:59Z",
                "created_by_user_id": "usr_123"
              }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1
          }
        }
      ]
    },
    {
      "name": "Transactions - Create",
      "method": "POST",
      "path": "/api/v1/projects/{project_id}/transactions",
      "description": "สร้างรายการ",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "body": {
          "type": "expense",
          "category_id": "cat_travel",
          "amount_satang": 35000,
          "occurred_at": "2026-01-03T10:54:59+07:00",
          "note": "ค่าเดินทาง"
        }
      },
      "responses": [
        {
          "status": 201,
          "body": {
            "transaction": {
              "id": "txn_124",
              "project_id": "prj_123",
              "type": "expense",
              "category_id": "cat_travel",
              "amount_satang": 35000,
              "currency": "THB",
              "occurred_at": "2026-01-03T03:54:59Z",
              "note": "ค่าเดินทาง",
              "created_by_user_id": "usr_123",
              "created_at": "2026-01-03T06:05:00Z",
              "updated_at": "2026-01-03T06:05:00Z",
              "deleted_at": null
            }
          }
        },
        {
          "status": 400,
          "body": {
            "error": {
              "code": "VALIDATION_ERROR",
              "message": "amount_satang must be > 0",
              "details": {
                "field": "amount_satang"
              },
              "request_id": "req_008"
            }
          }
        }
      ]
    },
    {
      "name": "Transactions - Get by ID",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/transactions/{id}",
      "request": {
        "path_params": {
          "project_id": "prj_123",
          "id": "txn_124"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "transaction": {
              "id": "txn_124",
              "project_id": "prj_123",
              "type": "expense",
              "category_id": "cat_travel",
              "amount_satang": 35000,
              "currency": "THB",
              "occurred_at": "2026-01-03T03:54:59Z",
              "note": "ค่าเดินทาง",
              "created_by_user_id": "usr_123",
              "created_at": "2026-01-03T06:05:00Z",
              "updated_at": "2026-01-03T06:05:00Z",
              "deleted_at": null
            }
          }
        }
      ]
    },
    {
      "name": "Transactions - Update (PATCH)",
      "method": "PATCH",
      "path": "/api/v1/projects/{project_id}/transactions/{id}",
      "description": "แก้ไขบางฟิลด์",
      "request": {
        "path_params": {
          "project_id": "prj_123",
          "id": "txn_124"
        },
        "body": {
          "category_id": "cat_food",
          "amount_satang": 40000,
          "note": "เปลี่ยนเป็นค่าอาหาร"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "transaction": {
              "id": "txn_124",
              "project_id": "prj_123",
              "type": "expense",
              "category_id": "cat_food",
              "amount_satang": 40000,
              "currency": "THB",
              "occurred_at": "2026-01-03T03:54:59Z",
              "note": "เปลี่ยนเป็นค่าอาหาร",
              "updated_at": "2026-01-03T06:08:00Z"
            }
          }
        }
      ]
    },
    {
      "name": "Transactions - Delete (Soft)",
      "method": "DELETE",
      "path": "/api/v1/projects/{project_id}/transactions/{id}",
      "request": {
        "path_params": {
          "project_id": "prj_123",
          "id": "txn_124"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "deleted": true,
            "id": "txn_124"
          }
        }
      ]
    },
    {
      "name": "Budgets - List by Month",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/budgets",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "query": {
          "month": 202601
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "month_yyyymm": 202601,
            "budgets": [
              {
                "category_id": "cat_food",
                "limit_amount_satang": 500000
              },
              {
                "category_id": "cat_travel",
                "limit_amount_satang": 300000
              }
            ]
          }
        }
      ]
    },
    {
      "name": "Budgets - Upsert",
      "method": "PUT",
      "path": "/api/v1/projects/{project_id}/budgets/{category_id}",
      "description": "ตั้งงบหมวดต่อเดือน (สร้างหรืออัปเดต)",
      "request": {
        "path_params": {
          "project_id": "prj_123",
          "category_id": "cat_travel"
        },
        "query": {
          "month": 202601
        },
        "body": {
          "limit_amount_satang": 350000
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "budget": {
              "project_id": "prj_123",
              "category_id": "cat_travel",
              "month_yyyymm": 202601,
              "limit_amount_satang": 350000,
              "updated_at": "2026-01-03T06:10:00Z"
            }
          }
        }
      ]
    },
    {
      "name": "Reports - Summary",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/reports/summary",
      "description": "สรุปรายรับ/รายจ่าย/คงเหลือในช่วงเวลา",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "query": {
          "from": "2026-01-01",
          "to": "2026-01-31"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "from": "2026-01-01",
            "to": "2026-01-31",
            "income_total_satang": 1500000,
            "expense_total_satang": 35000,
            "net_satang": 1465000,
            "currency": "THB"
          }
        }
      ]
    },
    {
      "name": "Reports - By Category (Month)",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/reports/by-category",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "query": {
          "month": 202601,
          "type": "expense"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "month_yyyymm": 202601,
            "type": "expense",
            "rows": [
              {
                "category_id": "cat_travel",
                "category_name_th": "เดินทาง",
                "total_satang": 35000,
                "tx_count": 1
              }
            ]
          }
        }
      ]
    },
    {
      "name": "Reports - Budget vs Actual (Month)",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/reports/budget-vs-actual",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "query": {
          "month": 202601,
          "type": "expense"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "month_yyyymm": 202601,
            "type": "expense",
            "rows": [
              {
                "category_id": "cat_travel",
                "category_name_th": "เดินทาง",
                "budget_limit_satang": 300000,
                "actual_spent_satang": 35000,
                "remaining_satang": 265000,
                "status": "UNDER_BUDGET"
              }
            ]
          }
        }
      ]
    },
    {
      "name": "Recurring - List",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/recurring",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "rules": [
              {
                "id": "rr_123",
                "type": "expense",
                "category_id": "cat_food",
                "amount_satang": 150000,
                "note": "อาหารประจำ",
                "freq": "monthly",
                "day_of_month": 1,
                "start_date": "2026-01-03",
                "next_run_date": "2026-02-01",
                "remind_days": 3,
                "is_active": true
              }
            ]
          }
        }
      ]
    },
    {
      "name": "Recurring - Create",
      "method": "POST",
      "path": "/api/v1/projects/{project_id}/recurring",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "body": {
          "type": "expense",
          "category_id": "cat_food",
          "amount_satang": 150000,
          "note": "อาหารประจำ",
          "freq": "monthly",
          "day_of_month": 1,
          "start_date": "2026-01-03",
          "remind_days": 3
        }
      },
      "responses": [
        {
          "status": 201,
          "body": {
            "rule": {
              "id": "rr_124",
              "project_id": "prj_123",
              "type": "expense",
              "category_id": "cat_food",
              "amount_satang": 150000,
              "freq": "monthly",
              "day_of_month": 1,
              "start_date": "2026-01-03",
              "next_run_date": "2026-02-01",
              "remind_days": 3,
              "is_active": true
            }
          }
        }
      ]
    },
    {
      "name": "Recurring - Run Due (Internal/Manual)",
      "method": "POST",
      "path": "/api/v1/projects/{project_id}/recurring/run-due",
      "description": "สร้าง transaction จาก recurring ที่ถึงกำหนด (owner/admin หรือ internal cron)",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "body": {
          "run_date": "2026-02-01"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "run_date": "2026-02-01",
            "created_count": 1,
            "created_transaction_ids": [
              "txn_9001"
            ]
          }
        }
      ]
    },
    {
      "name": "LINE Bot - Webhook",
      "method": "POST",
      "path": "/line/webhook",
      "description": "รับ event จาก LINE Messaging API (ไม่ใช่ API สำหรับ frontend)",
      "request": {
        "headers": {
          "X-Line-Signature": "base64..."
        },
        "body": {
          "destination": "Uxxxxxxxx",
          "events": [
            {
              "type": "message",
              "message": {
                "type": "text",
                "id": "123",
                "text": "จ่าย 350 เดินทาง ค่ารถ"
              },
              "source": {
                "type": "user",
                "userId": "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              },
              "replyToken": "replyToken...",
              "timestamp": 1767412345678
            }
          ]
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "ok": true
          }
        },
        {
          "status": 401,
          "body": {
            "error": {
              "code": "UNAUTHORIZED",
              "message": "Invalid LINE signature",
              "details": {},
              "request_id": "req_009"
            }
          }
        }
      ]
    }
  ]
}
```

## Response:
````markdown
# COMMAND_SPECS_TH.md
## LINE Chatbot Commands (TH) — Pattern + Regex Intent (MVP)

> เป้าหมาย: ให้คนในบ้าน “พิมพ์สั้นๆ แล้วบันทึกได้จริง”  
> แนวทาง: MVP ใช้ **Rule-based (Regex + Slot extraction)** ก่อน แล้วค่อยเพิ่ม NLP ภายหลัง  
> ข้อควรทำ: พยายาม “ถามกลับให้น้อยที่สุด” แต่ถ้าข้อมูลไม่พอให้ถามแบบเลือกตัวเลือก

---

## 0) หลักการออกแบบคำสั่ง
1) **คำสั่งต้องสั้น**: 1 บรรทัดจบ  
2) **รองรับพิมพ์ผิดเล็กน้อย**: เว้นวรรค, เครื่องหมาย, ตัวพิมพ์  
3) **จำนวนเงินเป็นหัวใจ**: จับได้ทั้ง `350`, `350.50`, `350บาท`  
4) **หมวดเป็น keyword**: match จากชื่อหมวดใน DB (ไทย/อังกฤษ) + alias  
5) **โปรเจคสำคัญ**: ถ้ามีหลายโปรเจค ต้องมีวิธีสลับ/กำหนดโปรเจคได้ง่าย  
6) **ความปลอดภัย**: ไม่โชว์ข้อมูลเกินจำเป็นในกลุ่ม/ห้องแชท

---

## 1) Tokens / Slot Extraction (มาตรฐาน)
### 1.1 Amount (เงิน)
- รองรับ:
  - `350`, `350.50`
  - `350บาท`, `350 บ.`, `350฿`
  - `1,250` (มี comma)
- แปลงเป็น satang (int)

**Regex (amount)**
```regex
(?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)
````

**Regex (amount with currency suffix)**

```regex
(?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)\s*(?:บาท|บ\.|฿)?
```

### 1.2 Date (วันที่)

*   รองรับ:
    *   `วันนี้`, `เมื่อวาน`
    *   `3/1`, `03/01/2026`, `2026-01-03`
*   ถ้าไม่ระบุ → default = วันนี้

**Regex (date)**

```regex
(?P<date>\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}|วันนี้|เมื่อวาน)
```

### 1.3 Time (เวลา)

*   รองรับ `10:54`, `10.54`, `10:54:59`
*   ถ้าไม่ระบุ → default = now

**Regex (time)**

```regex
(?P<time>\d{1,2}[:\.]\d{2}(?:[:\.]\d{2})?)
```

### 1.4 Category (หมวด)

*   ไม่ regex ล้วน ๆ (เพราะต้องเทียบ DB)
*   กลยุทธ์:
    1.  tokenize ข้อความ
    2.  ลอง match ชื่อหมวด/alias ที่ยาวที่สุดก่อน (longest match)
    3.  ถ้าไม่เจอ → ให้เสนอ top 5 หมวดที่ใกล้เคียง

**Alias ตัวอย่าง**

*   เดินทาง: `เดินทาง|รถ|ค่าแท็กซี่|แท็กซี่|บีทีเอส|รถไฟฟ้า|น้ำมัน`
*   อาหาร: `อาหาร|ข้าว|กาแฟ|ร้านอาหาร|มื้อ`
*   ค่าไฟ: `ค่าไฟ|ไฟฟ้า|PEA|MEA`

* * *

2) Project / Context Commands
-----------------------------

### 2.1 สลับโปรเจคด้วย project code

**ตัวอย่าง**

*   `#project aoq0f2i0`
*   `เข้าร่วม aoq0f2i0`

**Intent:** `PROJECT_SWITCH_OR_JOIN`

**Regex**

```regex
^(?:#\s*project\s+|เข้าร่วม\s+|join\s+)(?P<code>[a-z0-9]{6,12})\s*$
```

**Behavior**

*   ถ้า code เป็นโปรเจคที่ user เป็นสมาชิก → switch current\_project
*   ถ้าไม่เป็นสมาชิกแต่มีโปรเจคนี้อยู่ → join (ถ้านโยบายอนุญาต) หรือส่ง invite flow
*   ตอบกลับ: “ตั้งโปรเจคเป็น {ชื่อโปรเจค} แล้ว ✅”

* * *

3) Core CRUD Commands (Transactions)
------------------------------------

### 3.1 เพิ่มรายจ่าย (Expense Create)

**ตัวอย่าง**

*   `จ่าย 350 เดินทาง ค่ารถ`
*   `จ่าย350 ค่าไฟ`
*   `ซื้อ 129 กาแฟ`
*   `จ่าย 60 เมื่อวาน อาหาร ข้าวมันไก่`
*   `จ่าย 450 3/1 10:30 เดินทาง แท็กซี่`

**Intent:** `TXN_CREATE_EXPENSE`

**Regex (หัวคำสั่ง)**

```regex
^(?P<verb>จ่าย|ซื้อ|เสีย|ใช้)\s*(?P<rest>.+)$
```

**Parsing Strategy**

*   จาก `rest`:
    1.  หา amount ก่อน
    2.  หา date/time (optional)
    3.  ที่เหลือ → หา category จาก DB
    4.  ที่เหลืออีก → note/description

**Success Reply (MVP)**

*   `บันทึกแล้ว ✅ จ่าย 350.00 บาท • เดินทาง • "ค่ารถ" (03/01 10:54)`

**If missing category**

*   ถามกลับ: `หมวดนี้คืออะไรดีครับ? เลือกเลข: 1) เดินทาง 2) อาหาร 3) อื่นๆ`

* * *

### 3.2 เพิ่มรายรับ (Income Create)

**ตัวอย่าง**

*   `รับ 15000 เงินเดือน`
*   `รายรับ 5000 โบนัส`
*   `ได้ 200 ขายของ`

**Intent:** `TXN_CREATE_INCOME`

**Regex**

```regex
^(?P<verb>รับ|ได้|รายรับ)\s*(?P<rest>.+)$
```

**Behavior**

*   เหมือนรายจ่าย แต่ type=income

**Reply**

*   `บันทึกแล้ว ✅ รับ 15,000.00 บาท • เงินเดือน`

* * *

### 3.3 แก้ไข “รายการล่าสุด” (Update Last)

**ตัวอย่าง**

*   `แก้ล่าสุด 300`
*   `แก้ล่าสุด หมวด อาหาร`
*   `แก้ล่าสุด โน้ต ค่ารถไปกลับ`
*   `แก้ล่าสุด วันที่ เมื่อวาน`
*   `แก้ล่าสุด เวลา 09:10`

**Intent:** `TXN_UPDATE_LAST`

**Regex**

```regex
^แก้ล่าสุด\s+(?P<field>จำนวน|เงิน|หมวด|โน้ต|หมายเหตุ|วันที่|เวลา)\s*(?P<value>.+)$
```

**Field mapping**

*   จำนวน/เงิน → amount
*   หมวด → category
*   โน้ต/หมายเหตุ → note
*   วันที่ → date
*   เวลา → time

**Behavior**

*   หา last transaction ของ user ใน current\_project (ภายใน X ชั่วโมง หรือ last 20 รายการ)
*   ถ้า ambiguous: ส่งรายการล่าสุด 3 รายการให้เลือก (1/2/3)

**Reply**

*   `แก้ไขแล้ว ✅ รายการล่าสุดเป็น 300.00 บาท`

* * *

### 3.4 ลบ “รายการล่าสุด” (Delete Last)

**ตัวอย่าง**

*   `ลบล่าสุด`
*   `ยกเลิกล่าสุด`
*   `undo`

**Intent:** `TXN_DELETE_LAST`

**Regex**

```regex
^(ลบล่าสุด|ยกเลิกล่าสุด|undo)\s*$
```

**Behavior**

*   soft delete + แจ้งผล
*   (แนะนำ) เก็บ undo window 5 นาที: “พิมพ์ กู้คืนล่าสุด ได้”

**Reply**

*   `ลบแล้ว ✅ (รายการ: เดินทาง 350.00 บาท)`

* * *

### 3.5 แสดงรายการ (Read/List)

**ตัวอย่าง**

*   `รายการวันนี้`
*   `รายการเมื่อวาน`
*   `รายการเดือนนี้`
*   `รายการ เดินทาง เดือนนี้`
*   `ดูรายการ อาหาร 3/1-3/7`

**Intent:** `TXN_LIST`

**Regex**

```regex
^(?:รายการ|ดูรายการ)\s*(?P<rest>.*)$
```

**Parsing**

*   rest อาจมี:
    *   ช่วงเวลา: วันนี้/เมื่อวาน/เดือนนี้/ปีนี้ หรือ `3/1-3/7`
    *   หมวด: match DB
*   ถ้าไม่ระบุ → default วันนี้

**Reply**

*   ส่งสรุป + รายการ top 5 และปุ่ม “ดูทั้งหมดในเว็บ”

* * *

4) Summary / Reports Commands
-----------------------------

### 4.1 สรุปวันนี้/เดือนนี้/ปีนี้

**ตัวอย่าง**

*   `สรุปวันนี้`
*   `สรุปเดือนนี้`
*   `สรุปปีนี้`

**Intent:** `REPORT_SUMMARY`

**Regex**

```regex
^สรุป(?P<range>วันนี้|เมื่อวาน|เดือนนี้|ปีนี้)\s*$
```

**Reply template**

*   `สรุปเดือนนี้ (ม.ค. 2026)\nรายรับ: 15,000\nรายจ่าย: 350\nคงเหลือ: 14,650`

* * *

### 4.2 งบหมวด (Budget Status)

**ตัวอย่าง**

*   `งบ เดินทาง`
*   `งบอาหาร`
*   `งบ เดือนนี้`
*   `งบทั้งหมด`

**Intent:** `BUDGET_STATUS`

**Regex**

```regex
^งบ\s*(?P<rest>.*)$
```

**Parsing**

*   ถ้า rest ว่าง → งบทั้งหมดเดือนนี้
*   ถ้ามีคำว่า `ทั้งหมด` → งบทั้งหมด
*   ถ้ามีหมวด → งบหมวดนั้น

**Reply**

*   `งบเดินทาง (ม.ค. 2026): งบ 3,000 | ใช้ไป 350 | เหลือ 2,650 ✅`

* * *

### 4.3 ตั้งงบ (Budget Upsert)

**ตัวอย่าง**

*   `ตั้งงบ เดินทาง 3000`
*   `งบ เดินทาง = 3000`
*   `กำหนดงบ อาหาร 5000`

**Intent:** `BUDGET_SET`

**Regex**

```regex
^(?:ตั้งงบ|กำหนดงบ|งบ)\s+(?P<category>.+?)\s*(?:=)?\s*(?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)\s*(?:บาท|บ\.|฿)?\s*$
```

**Behavior**

*   upsert budget สำหรับเดือนปัจจุบัน (หรือรองรับ “ก.พ.” ใน V1)

**Reply**

*   `ตั้งงบแล้ว ✅ เดินทาง = 3,000 บาท (ม.ค. 2026)`

* * *

5) Categories Commands (Optional in MVP)
----------------------------------------

### 5.1 เพิ่มหมวด

**ตัวอย่าง**

*   `เพิ่มหมวด ค่าเกม`
*   `เพิ่มหมวดรายจ่าย ค่าเกม`
*   `เพิ่มหมวดรายรับ เงินปันผล`

**Intent:** `CATEGORY_CREATE`

**Regex**

```regex
^เพิ่มหมวด(?:(?P<type>รายจ่าย|รายรับ))?\s+(?P<name>.+)$
```

**Behavior**

*   ถ้าไม่ระบุ type → ถาม “เป็นรายรับหรือรายจ่าย?”
*   icon ให้ default และให้แก้ในเว็บภายหลัง

* * *

6) Help / Onboarding Commands
-----------------------------

### 6.1 ขอความช่วยเหลือ

**ตัวอย่าง**

*   `ช่วยเหลือ`
*   `help`
*   `คำสั่ง`

**Intent:** `HELP`

**Regex**

```regex
^(ช่วยเหลือ|help|คำสั่ง)\s*$
```

**Reply**

*   ส่ง quick guide + ตัวอย่าง 5 บรรทัด + วิธีใส่ `#project CODE`

* * *

7) Ambiguity Handling (สำคัญมาก)
--------------------------------

### 7.1 ไม่เจอหมวด

*   ตอบกลับพร้อมตัวเลือก:
    *   `ไม่เจอหมวด “xxx” เลือกหมวดใกล้เคียง: 1) เดินทาง 2) อาหาร 3) อื่นๆ`
*   ถ้าผู้ใช้ตอบ `1` → ใช้หมวดนั้นและบันทึกรายการเดิม (ต้องมี pending state)

### 7.2 พบหมวดหลายอันใกล้เคียง

*   ตอบให้เลือก:
    *   `“รถ” อาจเป็น: 1) เดินทาง 2) ผ่อนชำระ 3) อื่นๆ`

### 7.3 ผู้ใช้มีหลายโปรเจคและยังไม่เลือก

*   ตอบ:
    *   `คุณมี 2 โปรเจค: 1) ครอบครัว 2) ทริปเชียงใหม่ — พิมพ์ “เลือก 1” หรือ “#project CODE”`

* * *

8) Pending State (State Machine สำหรับแชท)
------------------------------------------

> เพื่อให้ถามกลับได้แบบไม่พัง flow

### 8.1 State Keys

*   `pending_intent`
*   `pending_payload` (amount/date/time/note/category candidates)
*   `expires_at` (เช่น 10 นาที)
*   `reply_to_message_id` (optional)

### 8.2 Example

*   User: `จ่าย 350 รถ`
*   Bot: `รถ หมายถึงหมวดไหน? 1) เดินทาง 2) ผ่อนชำระ 3) อื่นๆ`
*   User: `1`
*   Bot: `บันทึกแล้ว ✅ จ่าย 350 • เดินทาง`

* * *

9) Test Cases (ขั้นต่ำ)
-----------------------

1.  `จ่าย 350 เดินทาง ค่ารถ` → CREATE expense OK
2.  `รับ 15000 เงินเดือน` → CREATE income OK
3.  `สรุปเดือนนี้` → SUMMARY OK
4.  `ตั้งงบ เดินทาง 3000` → BUDGET\_SET OK
5.  `ลบล่าสุด` → DELETE last OK
6.  `#project aoq0f2i0` → SWITCH/JOIN OK
7.  `จ่าย 50` (ไม่มีหมวด) → ถามกลับ OK

* * *

10) Intent List (Canonical)
---------------------------

*   `PROJECT_SWITCH_OR_JOIN`
*   `TXN_CREATE_EXPENSE`
*   `TXN_CREATE_INCOME`
*   `TXN_UPDATE_LAST`
*   `TXN_DELETE_LAST`
*   `TXN_LIST`
*   `REPORT_SUMMARY`
*   `BUDGET_STATUS`
*   `BUDGET_SET`
*   `CATEGORY_CREATE`
*   `HELP`

* * *

```

ถ้าปอนด์อยากให้ “เอาไปใช้เขียนโค้ดได้ทันที” ผมทำเพิ่มให้ได้อีก 2 ไฟล์:
- `INTENT_PARSER_RULES.json` (นิยาม regex + priority + field mapping)
- `CHAT_REPLY_TEMPLATES_TH.json` (ข้อความตอบกลับมาตรฐาน + i18n)
```

## Response:
```markdown
# UI_ROUTES.md
## Mapping: หน้าเว็บ (UI) → API Endpoints ที่เรียก (Flask + LINE Auth + SQLite)

> โฟกัส: ให้ Dev เห็นภาพ “แต่ละหน้าเรียก API อะไรบ้าง” + โหลดลำดับไหน (critical path)  
> Base: `/api/v1` (REST) และ auth ผ่าน Cookie Session (แนะนำ)

---

## 0) Global Rules (ทุกหน้า)
### 0.1 Auth Guard
- ถ้า API ตอบ `401 UNAUTHORIZED`:
  - redirect → `/login`
- ถ้า API ตอบ `403 FORBIDDEN`:
  - show toast “ไม่มีสิทธิ์เข้าถึงโปรเจคนี้”

### 0.2 Current Project Context
- UI ต้องรู้ `current_project_id` ก่อนเรียก resource อื่น
- Source:
  1) `GET /api/v1/me` (preferred)
  2) หรือ session cookie server-rendered

### 0.3 Common APIs (ใช้ซ้ำหลายหน้า)
- `GET /api/v1/me` → user + current_project_id
- `GET /api/v1/projects` → รายชื่อโปรเจคทั้งหมดของ user
- `POST /api/v1/projects/{project_id}/switch` → เปลี่ยน current project

---

## 1) /login (LINE Login)
### UI
- ปุ่ม “Login with LINE”

### Calls
- **Navigate**: `GET /auth/line/login?redirect=/app`
  - (redirect ไป LINE OAuth)

### After callback
- LINE redirect → `/auth/line/callback` → (server sets session) → redirect `/app`

---

## 2) /app (Shell / App Layout)
> หน้า container ที่มี Bottom Nav + initial bootstrap

### On load (critical path)
1) `GET /api/v1/me`
2) ถ้า `current_project_id` ว่าง → redirect `/members`
3) ถ้ามี → preload minimal data:
   - `GET /api/v1/projects` (ใช้ทำ switcher)
   - `GET /api/v1/projects/{project_id}/categories?type=expense` (cache)
   - `GET /api/v1/projects/{project_id}/categories?type=income` (cache)

---

## 3) /ledger (หน้าหลักรายการ)
อิงภาพ: ปุ่มรายรับ/รายจ่าย, เลือกเดือน, list รายการ, summary

### UI State
- selectedMonth (YYYY-MM)
- tabType: expense|income|all
- search (optional V1)

### On enter
1) `GET /api/v1/me`
2) `GET /api/v1/projects/{project_id}/transactions?from=YYYY-MM-01&to=YYYY-MM-last&type=<tabType>&page=1&page_size=50`
3) `GET /api/v1/projects/{project_id}/reports/summary?from=...&to=...` (ทำ summary bar)

### Actions
#### 3.1 Tap “รายรับ” button
- open Category Picker (income)
- (ไม่ต้องเรียก API ถ้า preloaded categories แล้ว)
- ถ้าไม่ preload:
  - `GET /api/v1/projects/{project_id}/categories?type=income`

#### 3.2 Tap “รายจ่าย” button
- open Category Picker (expense)
- ถ้าไม่ preload:
  - `GET /api/v1/projects/{project_id}/categories?type=expense`

#### 3.3 Create Transaction (จาก modal)
- `POST /api/v1/projects/{project_id}/transactions`
- แล้ว refresh:
  - insert to list locally (optimistic) หรือ re-fetch page 1
  - `GET /api/v1/projects/{project_id}/reports/summary?from=...&to=...`

#### 3.4 Edit Transaction
- `PATCH /api/v1/projects/{project_id}/transactions/{id}`
- update row locally + refresh summary

#### 3.5 Delete Transaction
- `DELETE /api/v1/projects/{project_id}/transactions/{id}`
- remove row locally + refresh summary

#### 3.6 Pagination / Infinite scroll
- `GET /api/v1/projects/{project_id}/transactions?...&page=2`

---

## 4) /recurring (รายการประจำ)
อิงภาพ: ตั้งความถี่, วันเริ่ม, รอบถัดไป, เตือนก่อนกี่วัน

### On enter
1) `GET /api/v1/me`
2) `GET /api/v1/projects/{project_id}/recurring`
3) (optional) preload categories:
   - `GET /api/v1/projects/{project_id}/categories?type=expense`
   - `GET /api/v1/projects/{project_id}/categories?type=income`

### Actions
#### 4.1 Create recurring
- `POST /api/v1/projects/{project_id}/recurring`
- refresh list: `GET /api/v1/projects/{project_id}/recurring`

#### 4.2 Update recurring (toggle active / edit)
- `PATCH /api/v1/projects/{project_id}/recurring/{id}`
- update locally or re-fetch

#### 4.3 Run due (manual button for admin/owner)
- `POST /api/v1/projects/{project_id}/recurring/run-due` body `{ "run_date": "YYYY-MM-DD" }`
- แล้ว refresh ledger summary (optional):
  - `GET /api/v1/projects/{project_id}/reports/summary?from=...&to=...`

---

## 5) /reports (รายงาน)
อิงภาพ: Budget vs Actual chart + drilldown

### UI State
- selectedMonth (YYYYMM)
- type expense|income

### On enter
1) `GET /api/v1/me`
2) `GET /api/v1/projects/{project_id}/reports/budget-vs-actual?month=YYYYMM&type=expense`
3) `GET /api/v1/projects/{project_id}/reports/by-category?month=YYYYMM&type=expense`
4) (optional) `GET /api/v1/projects/{project_id}/reports/trend?months=12`

### Drilldown (tap category)
- navigate → `/category/{category_id}` (filtered list)
- Calls:
  - `GET /api/v1/projects/{project_id}/transactions?from=...&to=...&category_id={category_id}&page=1`

---

## 6) /categories (หมวดบัญชี)
อิงภาพ: toggle รายรับ/รายจ่าย + ปุ่มงบประมาณ + list หมวด + FAB เพิ่มหมวด

### On enter
1) `GET /api/v1/me`
2) `GET /api/v1/projects/{project_id}/categories?type=<expense|income>`
3) (เพื่อโชว์ “ใช้ไป” ใต้หมวด)
   - Option A (แนะนำ): ใช้ API รายงานรวมต่อหมวด
     - `GET /api/v1/projects/{project_id}/reports/by-category?month=YYYYMM&type=<expense|income>`
   - Option B: คำนวณจาก transactions (ไม่แนะนำถ้าข้อมูลเยอะ)

### Actions
#### 6.1 Create category (FAB)
- `POST /api/v1/projects/{project_id}/categories`
- refresh categories list:
  - `GET /api/v1/projects/{project_id}/categories?type=...`

#### 6.2 Edit category (optional V1)
- `PATCH /api/v1/projects/{project_id}/categories/{category_id}`

#### 6.3 Delete category (soft)
- `DELETE /api/v1/projects/{project_id}/categories/{category_id}`

#### 6.4 Tap “งบประมาณ”
- navigate → `/budget`
- (ดู section 7)

---

## 7) /budget (งบประมาณ)
อิงภาพแนวคิด: ซองเงินดิจิทัลรายหมวด

### On enter
1) `GET /api/v1/me`
2) `GET /api/v1/projects/{project_id}/budgets?month=YYYYMM`
3) `GET /api/v1/projects/{project_id}/reports/budget-vs-actual?month=YYYYMM&type=expense`
4) (optional) categories เพื่อแสดงชื่อ/ไอคอน:
   - `GET /api/v1/projects/{project_id}/categories?type=expense`

### Actions
#### 7.1 Upsert budget (inline edit)
- `PUT /api/v1/projects/{project_id}/budgets/{category_id}?month=YYYYMM`
  - body: `{ "limit_amount_satang": 300000 }`
- refresh:
  - `GET /api/v1/projects/{project_id}/budgets?month=YYYYMM`
  - `GET /api/v1/projects/{project_id}/reports/budget-vs-actual?month=YYYYMM&type=expense`

---

## 8) /members (สมาชิก + โปรเจค)
อิงภาพ: ส่วนครอบครัว, เพิ่มสมาชิก, สร้างโปรเจค, project code

### On enter
1) `GET /api/v1/me`
2) `GET /api/v1/projects`
3) (ถ้ามี current project) `GET /api/v1/projects/{project_id}/members`

### Actions
#### 8.1 Create project (modal)
- `POST /api/v1/projects`
- แล้ว UI:
  - set current project จาก response
  - refresh:
    - `GET /api/v1/projects`
    - `GET /api/v1/projects/{new_project_id}/members`

#### 8.2 Join project (by code)
- `POST /api/v1/projects/join` body `{ "project_code": "aoq0f2i0" }`
- refresh projects + members

#### 8.3 Switch project (dropdown)
- `POST /api/v1/projects/{project_id}/switch`
- refresh:
  - `GET /api/v1/projects/{project_id}/members`
  - (optional) preload categories for new project:
    - `GET /api/v1/projects/{project_id}/categories?type=expense`
    - `GET /api/v1/projects/{project_id}/categories?type=income`

#### 8.4 Invite member (owner only)
- `POST /api/v1/projects/{project_id}/members/invite`
- refresh members:
  - `GET /api/v1/projects/{project_id}/members`
- UI shows share text for LINE

---

## 9) /profile (โปรไฟล์/ตั้งค่า)
> ส่วนเว็บ MVP อาจมีแค่ logout + info

### On enter
- `GET /api/v1/me`

### Actions
- Logout:
  - `POST /auth/logout` → redirect `/login`

---

## 10) Optional V1: /help/line (คู่มือคำสั่งแชท)
### On enter
- (ไม่มี API ก็ได้) หรือ:
  - `GET /api/v1/projects` เพื่อโชว์ project codes
  - `GET /api/v1/me`

---

## 11) Performance Notes (เพื่อ Dev)
### 11.1 ลดจำนวน call หน้า /categories
- แนะนำใช้ `reports/by-category` เพื่อเอา “ใช้ไป” รายหมวด (แทนการ sum เองจาก transactions)

### 11.2 Cache categories
- categories เปลี่ยนไม่บ่อย ให้ cache ใน client (per project) 5–30 นาที หรือจนกว่าจะมี create/update/delete

### 11.3 Summary ควรเรียกเฉพาะเมื่อจำเป็น
- ledger summary เรียกตอนเปลี่ยนเดือน หรือหลัง CRUD

---

## 12) Endpoint Checklist (หน้าไหนใช้ endpoint อะไรบ้าง)
- /login → `/auth/line/login`, `/auth/line/callback`
- /app → `/api/v1/me`, `/api/v1/projects`, `/categories`
- /ledger → `/transactions`, `/reports/summary`
- /recurring → `/recurring`, (optional) `/recurring/run-due`
- /reports → `/reports/budget-vs-actual`, `/reports/by-category`, `/reports/trend`
- /categories → `/categories`, `/reports/by-category`
- /budget → `/budgets`, `/reports/budget-vs-actual`
- /members → `/projects`, `/members`, `/members/invite`, `/projects/join`, `/projects/{id}/switch`
- /profile → `/api/v1/me`, `/auth/logout`

---
```

## Response:
DB\_SCHEMA.sql
--------------

```sql
-- DB_SCHEMA.sql
-- Product: จดรายรับรายจ่าย (Flask + SQLite)
-- Money: store as integer satang (THB * 100)
-- Time: store as ISO-8601 TEXT in UTC where possible

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- -----------------------------
-- 0) Migration bookkeeping
-- -----------------------------
CREATE TABLE IF NOT EXISTS schema_migrations (
  version        TEXT PRIMARY KEY,                 -- e.g. "0001_initial"
  applied_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- -----------------------------
-- 1) Users / Auth (LINE)
-- -----------------------------
CREATE TABLE IF NOT EXISTS user (
  id            TEXT PRIMARY KEY,                  -- "usr_xxx"
  line_user_id  TEXT NOT NULL UNIQUE,              -- LINE userId
  display_name  TEXT NOT NULL,
  picture_url   TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- current project preference (optional but recommended)
CREATE TABLE IF NOT EXISTS user_pref (
  user_id             TEXT PRIMARY KEY,
  current_project_id  TEXT,
  locale              TEXT DEFAULT 'th',
  tz                  TEXT DEFAULT 'Asia/Bangkok',
  created_at          TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Session table (optional; if you use Flask server-side sessions you may not need this)
CREATE TABLE IF NOT EXISTS session (
  id           TEXT PRIMARY KEY,                   -- "ses_xxx"
  user_id      TEXT NOT NULL,
  token_hash   TEXT NOT NULL,                      -- hash of session token
  expires_at   TEXT NOT NULL,
  created_at   TEXT NOT NULL DEFAULT (datetime('now')),
  revoked_at   TEXT,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_session_user_id ON session(user_id);
CREATE INDEX IF NOT EXISTS idx_session_expires  ON session(expires_at);

-- -----------------------------
-- 2) Projects / Membership
-- -----------------------------
CREATE TABLE IF NOT EXISTS project (
  id             TEXT PRIMARY KEY,                 -- "prj_xxx"
  name           TEXT NOT NULL,
  project_code   TEXT NOT NULL UNIQUE,             -- short code, used in LINE (#project CODE)
  owner_user_id  TEXT NOT NULL,
  created_at     TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at     TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at     TEXT,
  FOREIGN KEY (owner_user_id) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_project_owner ON project(owner_user_id);

CREATE TABLE IF NOT EXISTS project_member (
  id          TEXT PRIMARY KEY,                    -- "mem_xxx"
  project_id  TEXT NOT NULL,
  user_id     TEXT NOT NULL,
  role        TEXT NOT NULL CHECK(role IN ('owner','member','admin')),
  nick_name   TEXT,
  is_active   INTEGER NOT NULL DEFAULT 1,
  joined_at   TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  UNIQUE(project_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_member_project ON project_member(project_id);
CREATE INDEX IF NOT EXISTS idx_member_user    ON project_member(user_id);

-- Optional: invite flow (owner sends invite_code)
CREATE TABLE IF NOT EXISTS project_invite (
  id          TEXT PRIMARY KEY,                    -- "inv_xxx"
  project_id  TEXT NOT NULL,
  invite_code TEXT NOT NULL UNIQUE,                -- short code share in LINE
  role        TEXT NOT NULL CHECK(role IN ('member','admin')),
  expires_at  TEXT NOT NULL,
  created_by  TEXT NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  used_at     TEXT,
  used_by     TEXT,
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by) REFERENCES user(id),
  FOREIGN KEY (used_by) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_invite_project ON project_invite(project_id);
CREATE INDEX IF NOT EXISTS idx_invite_expires ON project_invite(expires_at);

-- -----------------------------
-- 3) Categories
-- -----------------------------
CREATE TABLE IF NOT EXISTS category (
  id          TEXT PRIMARY KEY,                    -- "cat_xxx"
  project_id  TEXT NOT NULL,
  type        TEXT NOT NULL CHECK(type IN ('income','expense')),
  name_th     TEXT NOT NULL,
  name_en     TEXT,
  icon_key    TEXT NOT NULL DEFAULT 'ic_default',
  color       TEXT,
  sort_order  INTEGER NOT NULL DEFAULT 0,
  is_active   INTEGER NOT NULL DEFAULT 1,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at  TEXT,
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  UNIQUE(project_id, type, name_th)
);

CREATE INDEX IF NOT EXISTS idx_category_project_type ON category(project_id, type);
CREATE INDEX IF NOT EXISTS idx_category_project_sort ON category(project_id, sort_order);

-- -----------------------------
-- 4) Transactions (Ledger)
-- -----------------------------
CREATE TABLE IF NOT EXISTS transaction (
  id                 TEXT PRIMARY KEY,             -- "txn_xxx"
  project_id         TEXT NOT NULL,
  created_by_user_id TEXT NOT NULL,
  type               TEXT NOT NULL CHECK(type IN ('income','expense')),
  category_id        TEXT NOT NULL,
  amount_satang      INTEGER NOT NULL CHECK(amount_satang > 0),
  currency           TEXT NOT NULL DEFAULT 'THB',
  note               TEXT,
  occurred_at        TEXT NOT NULL,                -- ISO-8601 (prefer UTC)
  created_at         TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at         TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at         TEXT,
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by_user_id) REFERENCES user(id),
  FOREIGN KEY (category_id) REFERENCES category(id)
);

CREATE INDEX IF NOT EXISTS idx_txn_project_time     ON transaction(project_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_txn_project_type_time ON transaction(project_id, type, occurred_at);
CREATE INDEX IF NOT EXISTS idx_txn_project_cat_time ON transaction(project_id, category_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_txn_created_by       ON transaction(created_by_user_id);

-- -----------------------------
-- 5) Budget (Monthly Envelope)
-- -----------------------------
CREATE TABLE IF NOT EXISTS budget (
  id                  TEXT PRIMARY KEY,            -- "bud_xxx"
  project_id          TEXT NOT NULL,
  category_id         TEXT NOT NULL,
  month_yyyymm        INTEGER NOT NULL,            -- e.g. 202601
  limit_amount_satang INTEGER NOT NULL CHECK(limit_amount_satang >= 0),
  created_at          TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at          TEXT,
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  FOREIGN KEY (category_id) REFERENCES category(id),
  UNIQUE(project_id, category_id, month_yyyymm)
);

CREATE INDEX IF NOT EXISTS idx_budget_project_month ON budget(project_id, month_yyyymm);

-- -----------------------------
-- 6) Recurring
-- -----------------------------
CREATE TABLE IF NOT EXISTS recurring_rule (
  id                 TEXT PRIMARY KEY,             -- "rr_xxx"
  project_id         TEXT NOT NULL,
  created_by_user_id TEXT NOT NULL,
  type               TEXT NOT NULL CHECK(type IN ('income','expense')),
  category_id        TEXT NOT NULL,
  amount_satang      INTEGER NOT NULL CHECK(amount_satang > 0),
  currency           TEXT NOT NULL DEFAULT 'THB',
  note               TEXT,
  freq               TEXT NOT NULL CHECK(freq IN ('daily','weekly','monthly')),
  day_of_week        INTEGER,                      -- 0-6 (Mon=0 recommended) if weekly
  day_of_month       INTEGER,                      -- 1-31 if monthly
  start_date         TEXT NOT NULL,                -- 'YYYY-MM-DD'
  next_run_date      TEXT NOT NULL,                -- 'YYYY-MM-DD'
  remind_days        INTEGER NOT NULL DEFAULT 0,
  is_active          INTEGER NOT NULL DEFAULT 1,
  created_at         TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at         TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at         TEXT,
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by_user_id) REFERENCES user(id),
  FOREIGN KEY (category_id) REFERENCES category(id)
);

CREATE INDEX IF NOT EXISTS idx_rr_project_next ON recurring_rule(project_id, next_run_date, is_active);

CREATE TABLE IF NOT EXISTS recurring_run (
  id               TEXT PRIMARY KEY,               -- "rrun_xxx"
  recurring_rule_id TEXT NOT NULL,
  run_date         TEXT NOT NULL,                  -- 'YYYY-MM-DD'
  transaction_id   TEXT NOT NULL,
  created_at       TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (recurring_rule_id) REFERENCES recurring_rule(id) ON DELETE CASCADE,
  FOREIGN KEY (transaction_id) REFERENCES transaction(id),
  UNIQUE(recurring_rule_id, run_date)
);

CREATE INDEX IF NOT EXISTS idx_rrun_rule ON recurring_run(recurring_rule_id);

-- -----------------------------
-- 7) Attachments + OCR (V1 optional, keep in schema now)
-- -----------------------------
CREATE TABLE IF NOT EXISTS attachment (
  id             TEXT PRIMARY KEY,                 -- "att_xxx"
  transaction_id TEXT NOT NULL,
  file_path      TEXT NOT NULL,                    -- local path in app storage
  mime_type      TEXT NOT NULL,
  sha256         TEXT,
  created_at     TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (transaction_id) REFERENCES transaction(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_attachment_txn ON attachment(transaction_id);

CREATE TABLE IF NOT EXISTS ocr_result (
  id            TEXT PRIMARY KEY,                  -- "ocr_xxx"
  attachment_id TEXT NOT NULL,
  engine        TEXT NOT NULL DEFAULT 'offline',
  confidence    REAL,
  extracted_json TEXT NOT NULL,                    -- JSON string
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (attachment_id) REFERENCES attachment(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ocr_attachment ON ocr_result(attachment_id);

-- -----------------------------
-- 8) Audit Log
-- -----------------------------
CREATE TABLE IF NOT EXISTS audit_log (
  id          TEXT PRIMARY KEY,                    -- "aud_xxx"
  project_id  TEXT NOT NULL,
  user_id     TEXT,
  action      TEXT NOT NULL,                       -- e.g. CREATE_TXN / UPDATE_TXN
  entity_type TEXT NOT NULL,                       -- transaction/category/budget/...
  entity_id   TEXT NOT NULL,
  before_json TEXT,
  after_json  TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_audit_project_time ON audit_log(project_id, created_at);

-- -----------------------------
-- 9) Helpful Views (optional)
-- -----------------------------
-- Monthly totals per category (exclude deleted)
CREATE VIEW IF NOT EXISTS v_monthly_category_totals AS
SELECT
  t.project_id,
  t.type,
  t.category_id,
  CAST(strftime('%Y%m', t.occurred_at) AS INTEGER) AS month_yyyymm,
  SUM(t.amount_satang) AS total_satang,
  COUNT(*) AS tx_count
FROM transaction t
WHERE t.deleted_at IS NULL
GROUP BY t.project_id, t.type, t.category_id, month_yyyymm;
```

* * *

MIGRATION\_PLAN.md
------------------

```markdown
# MIGRATION_PLAN.md
## SQLite Migrations (Flask) — แผนและรูปแบบที่แนะนำ

> เป้าหมาย: ทำให้ “อัปเดต schema ได้ปลอดภัย” แม้ใช้ SQLite และ deploy แบบ local/offline  
> แนวทาง: ใช้ **SQL migration files แบบ versioned** + ตาราง `schema_migrations`  
> เหตุผล: SQLite มีข้อจำกัด ALTER TABLE (โดยเฉพาะ drop column/modify type) → ต้องวางแผน “expand/contract” และ “table copy” เมื่อจำเป็น

---

## 1) โครงสร้างโฟลเดอร์
```

app/  
migrations\_sql/  
0001\_initial.sql  
0002\_add\_invites.sql  
0003\_add\_attachments\_ocr.sql  
0004\_add\_user\_pref.sql  
0005\_indexes\_optimize.sql  
db.py (migration runner)  
schema/DB\_SCHEMA.sql (reference)

````

---

## 2) Migration Runner (แนวคิด)
### 2.1 หลักการ
- ทุกไฟล์ migration ต้อง:
  - อยู่ใน transaction (`BEGIN; ... COMMIT;`) ถ้าไม่ขัดกับ SQLite DDL บางคำสั่ง
  - ปิดท้ายด้วย `INSERT INTO schema_migrations(version) VALUES ('000X_name');`
- Runner จะ:
  1) สร้าง `schema_migrations` ถ้ายังไม่มี
  2) list ไฟล์ migration ตามชื่อเรียง
  3) เช็คว่ารันแล้วหรือยังจาก `schema_migrations`
  4) รันเฉพาะไฟล์ที่ยังไม่เคยรัน

### 2.2 Idempotency
- ใช้ `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`
- หลีกเลี่ยงการรันซ้ำโดยอาศัย `schema_migrations`

---

## 3) Versioning Policy
- ใช้เลข 4 หลัก + snake_case
  - `0001_initial`
  - `0002_add_invites`
- ห้ามแก้ migration ที่ถูก deploy แล้ว (immutable)
- ถ้าต้องแก้ ให้สร้าง migration ใหม่เสมอ

---

## 4) Migration Scripts (ตัวอย่างไฟล์)
> หมายเหตุ: ด้านล่างเป็นตัวอย่าง “โครง” ให้ copy ไปเป็นไฟล์จริงใน `migrations_sql/`

### 4.1 0001_initial.sql
- สร้างตารางหลักทั้งหมด: user/project/member/category/transaction/budget/recurring/audit + indexes
- (แนะนำ) ใส่ default categories template ตอนสร้างโปรเจคใน code ไม่ใส่ใน migration

**Key checks**
- foreign_keys=ON
- money เป็น satang int
- soft delete fields

### 4.2 0002_add_invites.sql
- เพิ่มตาราง `project_invite`
- เพิ่ม index ที่เกี่ยวข้อง
- ใช้เมื่อต้องการ flow “เชิญสมาชิก” ในเว็บ/LINE

### 4.3 0003_add_attachments_ocr.sql
- เพิ่ม `attachment`, `ocr_result`
- รองรับ scan bill และแนบรูป

### 4.4 0004_add_user_pref.sql
- เพิ่ม `user_pref` เพื่อเก็บ current_project_id, locale, timezone (ช่วยให้ bot สลับโปรเจคถูก)

### 4.5 0005_indexes_optimize.sql
- เพิ่ม/ปรับ index เพื่อ performance เมื่อข้อมูลเยอะ
- ใช้ในช่วงปลายเมื่อเห็น query จริงแล้ว

---

## 5) SQLite ALTER TABLE Strategy (สำคัญ)
SQLite ทำได้จำกัด:
- ✅ ADD COLUMN
- ✅ RENAME TABLE / RENAME COLUMN (SQLite เวอร์ชันใหม่)
- ❌ DROP COLUMN (ต้องใช้ workaround)
- ❌ MODIFY COLUMN TYPE (ต้อง copy table)

### 5.1 Workaround: Rebuild Table (Drop/Modify)
1) `ALTER TABLE old RENAME TO old__tmp;`
2) `CREATE TABLE old (... new schema ...);`
3) `INSERT INTO old (cols...) SELECT cols... FROM old__tmp;`
4) สร้าง indexes ใหม่
5) `DROP TABLE old__tmp;`

**กฎ:** ต้องทำใน transaction และ backup DB ก่อนเสมอ

---

## 6) Backups ก่อน migration
- ทุกครั้งก่อนรัน migrations:
  - copy db file -> `backup/db_YYYYMMDD_HHMMSS.sqlite`
  - เก็บไว้ N ชุด (เช่น 10 ชุด)

---

## 7) Seed Data
- ไม่ควร seed ข้อมูล “ธุรกิจ” ใน migration
- แนะนำ seed ผ่าน code:
  - default categories per project
  - default budgets = 0

---

## 8) Testing Plan (Migration)
- Test 1: new install → run all migrations → schema ok
- Test 2: upgrade path:
  - db ที่มี `0001` → apply `0002..0005` → data intact
- Test 3: downgrade (optional)
  - ไม่บังคับทำ downgrade ใน MVP
  - แต่ต้องมี backup/restore

---

## 9) Example Migration File Template
```sql
-- 000X_some_change.sql
PRAGMA foreign_keys = ON;

BEGIN;

-- DDL changes here
-- CREATE TABLE IF NOT EXISTS ...
-- ALTER TABLE ... ADD COLUMN ...

INSERT INTO schema_migrations(version) VALUES ('000X_some_change');

COMMIT;
````

* * *

10) Recommended Minimal Set for MVP
-----------------------------------

*   ✅ 0001\_initial.sql
*   ✅ 0002\_add\_invites.sql (ถ้าทำเชิญสมาชิกจริง)
*   (optional V1) 0003\_add\_attachments\_ocr.sql
*   ✅ 0004\_add\_user\_pref.sql
*   ✅ 0005\_indexes\_optimize.sql (ทำหลังมีข้อมูลจริง)

* * *

```

ถ้าปอนด์อยากได้ “ไฟล์ migration จริงครบชุด” (0001–0005) แบบพร้อมวางโฟลเดอร์ ผมจัดให้เป็นบล็อก SQL แยกไฟล์ให้เลยครับ (จะได้ copy วางทีละไฟล์ได้ทันที)
```

## Response:
ได้ครับ — ทำได้ **แน่นอน** และทำได้แบบ “ปลอดภัย/ควบคุมได้” ด้วย โดยให้ **Botpress เป็นหัวคิด (AI Orchestrator)** แล้วให้ **Flask เป็นแหล่งความจริง (Source of Truth) สำหรับ CRUD + กฎธุรกิจ + SQLite**

ภาพรวมคือ: **LINE → Botpress (เข้าใจภาษา/ตัดสินใจ) → Flask API (ทำงานจริงกับข้อมูล) → Botpress สรุปคำตอบ → LINE**

* * *

สถาปัตยกรรมที่แนะนำ
-------------------

### Option A (แนะนำสุด): Botpress คุยกับ Flask ผ่าน “Tool/API Calls”

1.  ผู้ใช้พิมพ์ใน LINE
2.  LINE ส่งเข้า **Botpress** (ผ่าน LINE channel หรือ webhook bridge)
3.  Botpress วิเคราะห์ intent/slot (เช่น จ่าย 350 เดินทาง)
4.  Botpress **เรียก Flask API** (เช่น `POST /transactions`)
5.  Flask บันทึก SQLite + คืนผลลัพธ์
6.  Botpress สร้างข้อความตอบกลับ แล้วส่งกลับไป LINE

**ข้อดี**

*   Flask คุมกฎธุรกิจ/ความถูกต้องของข้อมูล
*   Botpress ทำหน้าที่ภาษา/AI/บริบทสนทนา
*   แยกความรับผิดชอบชัด

* * *

### Option B: LINE → Flask → ส่งต่อไป Botpress → Flask ทำ CRUD

Flask เป็นตัวรับ webhook LINE ก่อน แล้วส่งข้อความไป Botpress เพื่อให้คิด แล้ว Flask ทำ CRUD ตามผลที่ Botpress ส่งกลับมา

**ข้อดี**: คุมความปลอดภัยที่ฝั่ง Flask มากขึ้น  
**ข้อเสีย**: ต้องเขียน orchestration เองเยอะกว่า

* * *

เชื่อมกับ URL Webhook ของ Botpress ได้ไหม?
------------------------------------------

URL ที่ให้มา `https://webhook.botpress.cloud/...` ใช้เป็น “ปลายทางรับ event” ของ Botpress ได้ (โดยทั่วไป Botpress มี endpoint สำหรับรับข้อความเข้า) แต่ “รูปแบบ payload” ต้องตรงกับที่ Botpress คาดหวัง

แนวทางปฏิบัติที่เวิร์กสุด:

*   ให้ Botpress เป็นตัวรับ message (จาก LINE channel ใน Botpress หรือจาก Flask forwarding)
*   แล้ว Botpress ไปเรียก Flask API ต่อเพื่อ CRUD

* * *

Flask ต้องเตรียมอะไรบ้าง (เพื่อให้ Botpress ทำ CRUD ได้)
--------------------------------------------------------

### 1) ทำ “Service API” สำหรับบอท (แยกจากเว็บ)

แนะนำเพิ่ม namespace เช่น:

*   `/api/v1/bot/...` หรือใช้ `/api/v1/projects/...` เดิมได้ แต่ต้องมี auth สำหรับบอท

### 2) Auth ระหว่าง Botpress ↔ Flask (สำคัญมาก)

อย่าให้ Botpress เรียก API โดยไม่ป้องกัน

**แนะนำ**: ใช้ `X-BOT-TOKEN` (shared secret) หรือ HMAC signature

*   Botpress ใส่ header:
    *   `X-BOT-TOKEN: <secret>`
*   Flask ตรวจ header ก่อนทุกครั้ง

(ถ้าขึ้น production จริง แนะนำ OAuth2 service-to-service หรือ mTLS แต่ MVP ใช้ shared secret ได้)

### 3) Endpoint ที่บอทต้องใช้จริง (ขั้นต่ำ)

*   `POST /api/v1/projects/{project_id}/transactions`
*   `GET /api/v1/projects/{project_id}/reports/summary?...`
*   `GET /api/v1/projects/{project_id}/categories?type=expense|income`
*   `PUT /api/v1/projects/{project_id}/budgets/{category_id}?month=YYYYMM`
*   `GET /api/v1/projects/{project_id}/transactions?...` (สำหรับ “ดูรายการ”)

### 4) Mapping LINE user → user/project ใน Flask

Botpress ต้องส่ง `line_user_id` มาด้วย เพื่อให้ Flask:

*   หา user
*   รู้ current\_project\_id (จาก `user_pref`)
*   ตรวจว่า user เป็น member ของ project

* * *

ตัวอย่าง Flow “จ่าย 350 เดินทาง ค่ารถ”
--------------------------------------

1.  LINE message → Botpress
2.  Botpress วิเคราะห์ได้:

```json
{
  "intent": "TXN_CREATE_EXPENSE",
  "amount_satang": 35000,
  "category_name": "เดินทาง",
  "note": "ค่ารถ"
}
```

3.  Botpress เรียก Flask:  
    `POST /api/v1/bot/transactions/create`

```json
{
  "line_user_id": "Uxxxxxxxx",
  "project_hint": null,
  "type": "expense",
  "amount_satang": 35000,
  "category_text": "เดินทาง",
  "note": "ค่ารถ",
  "occurred_at": "2026-01-03T12:34:00+07:00"
}
```

4.  Flask ทำงาน:
    *   resolve project จาก user\_pref
*   resolve category จากชื่อ/alias
*   insert transaction
*   return:

```json
{
  "ok": true,
  "transaction": {
    "id": "txn_124",
    "amount_satang": 35000,
    "category_name_th": "เดินทาง",
    "occurred_at": "2026-01-03T05:34:00Z"
  },
  "budget_hint": {
    "month_yyyymm": 202601,
    "remaining_satang": 265000,
    "status": "UNDER_BUDGET"
  }
}
```

5.  Botpress ตอบกลับ LINE:

> บันทึกแล้ว ✅ จ่าย 350 บาท • เดินทาง (“ค่ารถ”)  
> งบเดินทางเดือนนี้เหลือ 2,650 บาท

* * *

ให้ Botpress “ช่วยคิดวิเคราะห์” ได้แค่ไหน?
------------------------------------------

ได้ 2 แบบ:

### แบบที่ 1: Botpress วิเคราะห์จากข้อมูลที่ Flask ส่งกลับ (แนะนำ)

*   Flask ส่ง summary/report กลับไป
*   Botpress สรุปเป็นภาษาคนให้เข้าใจง่าย

### แบบที่ 2: Botpress ดึงข้อมูลดิบจาก Flask แล้ววิเคราะห์เอง

*   Botpress เรียกหลาย endpoint (list txns, budgets)
*   แล้วให้ AI สรุป/หา insight
*   ต้องระวัง: ข้อมูลเยอะ/ค่าใช้จ่าย/latency

**แนะนำ**: ให้ Flask ทำ aggregation (reports) แล้ว Botpress ทำ “ภาษา + ข้อเสนอแนะ”

* * *

จุดที่ต้องระวัง (สำคัญ)
-----------------------

1.  **Security**: webhook ของ Flask ที่เปิดให้ Botpress ต้องมี token/signature
2.  **Privacy**: อย่าส่งข้อมูลมากเกินจำเป็นไป Botpress (เพราะ Botpress เป็น cloud)
    *   ถ้าคอนเซ็ปต์คุณ “ข้อมูลอยู่ในเครื่อง 100%” แบบเดิม → การใช้ Botpress cloud จะ “ไม่ 100% local” แล้ว
    *   ถ้ารับได้ว่า “ส่งเฉพาะข้อความ/summary ขึ้น cloud” ก็โอเค
3.  **Idempotency**: LINE อาจส่งซ้ำ ต้องมี `message_id`/`event_id` กันบันทึกซ้ำ
4.  **Project context**: ผู้ใช้มีหลายโปรเจค ต้องมีกติกา `#project CODE` หรือให้เลือก

* * *

สรุปคำตอบ
---------

*   ✅ ทำได้: ให้ **Botpress เป็นหัวคิด AI** และให้ **Flask ทำ CRUD + วิเคราะห์รายงาน**
*   ✅ เชื่อมได้: Botpress เรียก Flask API เพื่อเพิ่ม/แก้/ลบ/สรุปข้อมูล
*   ⚠️ แต่: ถ้าต้องการ “ข้อมูลอยู่ในเครื่อง 100%” จริง ๆ การใช้ Botpress cloud จะขัดแนวคิด (เพราะข้อความ/บางข้อมูลต้องออกนอกเครื่อง)

* * *

ถ้าคุณบอกผมว่า “ยอมให้ข้อมูลออกไป Botpress ได้ระดับไหน”

*   A) ส่งแค่ “ข้อความผู้ใช้” + “ผลลัพธ์แบบสรุป”
*   B) ส่งรายการธุรกรรมบางส่วนเพื่อทำ insight  
    ผมจะจัด **PRD เสริม + API ของ `/api/v1/bot/*` + security spec (token/HMAC) + idempotency** ให้ครบชุดเลยครับ

## Response:
ต่อไปนี้คือ “ชุดเอกสารเสริม” ตามที่เลือก **B) ส่งรายการธุรกรรมบางส่วนให้ Botpress ทำ insight** ครบตามที่ขอ: **PRD เสริม + API `/api/v1/bot/*` + Security spec (Token/HMAC) + Idempotency**

* * *

PRD เสริม — Botpress Insight Integration (Mode B)
=================================================

1) เป้าหมาย
-----------

*   ให้ Botpress (AI) ทำ “สรุป/วิเคราะห์/แนะนำ” จาก **ชุดข้อมูลธุรกรรมบางส่วน** ที่จำกัดและปลอดภัย
*   Flask เป็น **Source of Truth** สำหรับ CRUD + รายงาน + นโยบายข้อมูล
*   Botpress เรียก Flask ผ่าน `/api/v1/bot/*` เพื่อ:
    *   CRUD แบบมี guard
    *   ดึง “dataset แบบจำกัด” (window/time-range, fields minimal)
    *   บันทึก insight/log ที่ได้กลับมา (optional)

2) ขอบเขตข้อมูลที่อนุญาตส่งออก (Data Minimization Policy)
---------------------------------------------------------

**อนุญาตส่งออก**

*   รายการธุรกรรม: เฉพาะ fields ที่จำเป็นต่อ insight
*   ระยะเวลา: จำกัดตามคำขอผู้ใช้ (เช่น 7/30/90 วัน) หรือเพดานสูงสุด 12 เดือน
*   หมวด: ส่งเป็น `category_name`/`category_id` (ไม่จำเป็นต้องส่ง note ทั้งหมด)

**ควรจำกัด/ปิดโดยดีฟอลต์**

*   `note` (รายละเอียด) → ส่งเฉพาะเมื่อผู้ใช้พิมพ์ “อนุญาต” หรือ “ต้องการวิเคราะห์ละเอียด”
*   merchant/ชื่อร้าน (ถ้าคุณจะทำในอนาคต)
*   attachment/OCR raw text (ห้ามส่ง)

3) Insight Use-cases (ตัวอย่าง)
-------------------------------

1.  “เดือนนี้ใช้เงินกับอะไรเยอะสุด 3 อันดับ”
2.  “หมวดไหนมีแนวโน้มเกินงบ”
3.  “เทียบเดือนนี้กับเดือนที่แล้ว”
4.  “แนะนำลดค่าใช้จ่ายแบบเป็นรูปธรรม” (เช่น หมวดเดินทางเพิ่มขึ้น 40%)
5.  “ตรวจจับความผิดปกติ” (spike detection) แบบง่าย

4) Consent UX (สำหรับ Mode B)
-----------------------------

*   ครั้งแรกที่ผู้ใช้ถาม insight: Bot ต้องแจ้งว่า “จะดึงรายการบางส่วนไปวิเคราะห์”
*   บันทึก consent ต่อโปรเจค/ต่อผู้ใช้:
    *   `insight_share_level = minimal | with_notes`
*   ผู้ใช้สั่ง:
    *   `เปิดวิเคราะห์ละเอียด` (อนุญาตส่ง note)
    *   `ปิดวิเคราะห์ละเอียด` (ส่งแบบ minimal)

* * *

API: /api/v1/bot/\* (Bot-to-Flask Contract)
===========================================

> ทุก endpoint ใต้ `/api/v1/bot/*` ต้องมี Security + Idempotency  
> Flask จะทำ “resolve user/project” จาก `line_user_id` + `user_pref.current_project_id` (หรือ project\_code)

A) Auth/Context
---------------

### 1) Resolve Context (ตรวจ user + project)

`POST /api/v1/bot/context/resolve`

**Request**

```json
{
  "line_user_id": "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "project_code": "aoq0f2i0",
  "request_locale": "th"
}
```

**Response 200**

```json
{
  "ok": true,
  "user": { "id": "usr_123", "display_name": "Pond" },
  "project": { "id": "prj_123", "name": "ครอบครัว", "project_code": "aoq0f2i0" },
  "permissions": { "role": "member" },
  "insight_share_level": "minimal"
}
```

**Errors**

*   404 user not found (ยังไม่เคย login)
*   403 not member
*   404 project\_code not found

* * *

B) CRUD ผ่านบอท (thin wrapper)
------------------------------

### 2) Create Transaction

`POST /api/v1/bot/transactions/create`

**Request**

```json
{
  "event_id": "line_msg_1234567890",
  "line_user_id": "Uxxxx",
  "project_code": "aoq0f2i0",
  "type": "expense",
  "amount_satang": 35000,
  "category_text": "เดินทาง",
  "note": "ค่ารถ",
  "occurred_at": "2026-01-03T12:34:00+07:00"
}
```

**Response 201**

```json
{
  "ok": true,
  "transaction": {
    "id": "txn_124",
    "type": "expense",
    "amount_satang": 35000,
    "category_id": "cat_travel",
    "category_name_th": "เดินทาง",
    "occurred_at": "2026-01-03T05:34:00Z"
  },
  "budget_hint": {
    "month_yyyymm": 202601,
    "category_id": "cat_travel",
    "remaining_satang": 265000,
    "status": "UNDER_BUDGET"
  }
}
```

### 3) Update Last Transaction (optional convenience)

`POST /api/v1/bot/transactions/update-last`

**Request**

```json
{
  "event_id": "line_msg_1234567891",
  "line_user_id": "Uxxxx",
  "field": "amount_satang",
  "value": 40000
}
```

**Response 200**

```json
{
  "ok": true,
  "updated_transaction_id": "txn_124"
}
```

### 4) Delete Last Transaction

`POST /api/v1/bot/transactions/delete-last`

**Request**

```json
{
  "event_id": "line_msg_1234567892",
  "line_user_id": "Uxxxx"
}
```

**Response 200**

```json
{ "ok": true, "deleted_transaction_id": "txn_124" }
```

* * *

C) Data Export (Mode B) — ส่ง “บางส่วน” ไปทำ insight
----------------------------------------------------

### 5) Export Transactions Dataset (Minimal/With Notes)

`POST /api/v1/bot/insights/export`

**Request**

```json
{
  "event_id": "line_msg_1234567893",
  "line_user_id": "Uxxxx",
  "project_code": "aoq0f2i0",
  "range": {
    "from": "2026-01-01",
    "to": "2026-01-31"
  },
  "limit": 500,
  "share_level": "minimal",
  "include": {
    "categories": true,
    "budgets": true
  }
}
```

**Response 200**

```json
{
  "ok": true,
  "policy_applied": {
    "max_range_days": 365,
    "max_rows": 500,
    "note_included": false
  },
  "project": { "id": "prj_123", "name": "ครอบครัว" },
  "month_yyyymm": 202601,
  "dataset": {
    "transactions": [
      {
        "id": "txn_1",
        "type": "expense",
        "amount_satang": 35000,
        "occurred_date": "2026-01-03",
        "category_id": "cat_travel"
      }
    ],
    "categories": [
      { "id": "cat_travel", "type": "expense", "name_th": "เดินทาง" }
    ],
    "budgets": [
      { "category_id": "cat_travel", "month_yyyymm": 202601, "limit_amount_satang": 300000 }
    ]
  }
}
```

> หมายเหตุ: ใน `minimal` จะส่ง `occurred_date` (ไม่ต้อง timestamp) และไม่ส่ง `note`

### 6) Save Insight Result (optional)

`POST /api/v1/bot/insights/save`

**Request**

```json
{
  "event_id": "line_msg_1234567893",
  "line_user_id": "Uxxxx",
  "project_id": "prj_123",
  "insight_type": "MONTHLY_SPEND_TOP3",
  "summary_text": "เดือนนี้ใช้มากสุด: อาหาร 5,200 / เดินทาง 1,800 / ช้อปปิ้ง 900",
  "payload_json": {
    "top3": [
      { "category_id": "cat_food", "total_satang": 520000 },
      { "category_id": "cat_travel", "total_satang": 180000 }
    ]
  }
}
```

**Response 201**

```json
{ "ok": true, "insight_id": "ins_001" }
```

* * *

Security Spec (Token + HMAC)
============================

1) Threat Model (ย่อ)
---------------------

*   ป้องกันคนอื่นยิง `/api/v1/bot/*` แทน Botpress
*   ป้องกัน replay (ยิงซ้ำเพื่อบันทึกซ้ำ)
*   ป้องกัน payload ถูกแก้ไขกลางทาง

2) Headers ที่บังคับใช้
-----------------------

Botpress ต้องส่ง headers:

*   `X-BOT-ID: botpress-prod`
*   `X-BOT-TS: 1700000000` (unix seconds)
*   `X-BOT-NONCE: <uuid>`
*   `X-BOT-SIGN: <base64(hmac_sha256(secret, signing_string))>`

และ (ถ้าต้องการ) `X-BOT-TOKEN: <static token>` เป็นชั้นแรก

3) Signing String (มาตรฐาน)
---------------------------

ให้ใช้ string นี้:

```
METHOD\n
PATH\n
X-BOT-TS\n
X-BOT-NONCE\n
SHA256_HEX(BODY_JSON_CANONICAL)
```

**Example**

```
POST
/api/v1/bot/transactions/create
1700000000
550e8400-e29b-41d4-a716-446655440000
3a6eb0790f... (sha256 of body)
```

4) Verification Rules (Flask)
-----------------------------

*   ตรวจ `X-BOT-TS` ต้องอยู่ในช่วง ±300 วินาที
*   `X-BOT-NONCE` ต้องไม่เคยใช้ในช่วง 10 นาที (เก็บใน DB/Redis/file cache)
*   ตรวจ HMAC ถูกต้อง
*   ถ้าไม่ผ่าน → 401

* * *

Idempotency Spec (กันบันทึกซ้ำ)
===============================

1) Key ที่ใช้
-------------

*   ใช้ `event_id` จาก LINE message id หรือ Botpress event id
*   ทุก bot endpoint ที่ “เขียนข้อมูล” ต้องรับ `event_id`

2) Table สำหรับ idempotency
---------------------------

เพิ่มตาราง:

*   `idempotency_key`
    *   key (pk) = `event_id`
    *   scope = endpoint name
    *   request\_hash
    *   response\_json
    *   created\_at
    *   expires\_at

**พฤติกรรม**

*   ถ้าเคยมี key เดิม (และ request\_hash ตรงกัน)
    *   คืน response\_json เดิมทันที (200/201)
*   ถ้า key เดิมแต่ request\_hash ไม่ตรง
    *   คืน 409 CONFLICT (ป้องกัน event\_id reuse ผิดวัตถุประสงค์)

3) TTL
------

*   เก็บ 7–30 วัน ตามความเหมาะสม
*   แต่ nonce cache (สำหรับ HMAC) แค่ 10 นาที

* * *

เพิ่มเติมที่ “ควรมี” สำหรับ Mode B
==================================

1.  **Policy Engine ใน Flask**
    *   จำกัดวันย้อนหลัง, จำนวนแถว, fields ที่ส่ง
*   ถ้าผู้ใช้ขอ “ทั้งปีและละเอียด” ให้ Bot ตอบว่าเกิน policy และเสนอแบ่งช่วง
    2.  **Consent Flag**
    *   `project_setting.insight_share_level` ต่อโปรเจค
*   หรือ `user_pref.insight_share_level` ต่อผู้ใช้
    3.  **PII Scrubber**
    *   ถ้าจะส่ง note ให้ตัด pattern เสี่ยง (เบอร์โทร/เลขบัญชี) (optional แต่ดีมาก)

* * *

ถ้าคุณต้องการ ผมสามารถ “อัปเดต DB\_SCHEMA.sql/MIGRATION\_PLAN.md” ให้รวมตารางที่เพิ่มสำหรับ **nonce + idempotency + insight storage + project settings** เป็น migration file ชุดใหม่ (เช่น `0006_bot_security.sql`) ให้พร้อมใช้งานทันทีด้วยครับ

## Response:
```json
{
  "meta": {
    "product": "จดรายรับรายจ่าย",
    "version": "1.1.0-botpress-mode-b",
    "base_url": "http://localhost:5000",
    "api_base": "/api/v1",
    "time_zone_default": "Asia/Bangkok",
    "money": {
      "storage": "integer_satang",
      "currency_default": "THB",
      "example": "350.00 THB => 35000 satang"
    },
    "auth": {
      "web": {
        "type": "cookie_session_or_bearer",
        "note": "เว็บแนะนำใช้ Cookie Session (HttpOnly). ถ้าใช้ Bearer ให้ส่ง Authorization: Bearer <token>"
      },
      "bot": {
        "type": "token_and_hmac",
        "required_headers": [
          "X-BOT-ID",
          "X-BOT-TS",
          "X-BOT-NONCE",
          "X-BOT-SIGN"
        ],
        "optional_headers": [
          "X-BOT-TOKEN"
        ],
        "hmac": {
          "algo": "HMAC-SHA256",
          "signing_string": "METHOD\\nPATH\\nX-BOT-TS\\nX-BOT-NONCE\\nSHA256_HEX(BODY_JSON_CANONICAL)",
          "ts_skew_seconds": 300,
          "nonce_ttl_minutes": 10
        }
      }
    },
    "idempotency": {
      "required_for_write_endpoints": true,
      "key_field": "event_id",
      "behavior": {
        "same_event_same_hash": "return_saved_response",
        "same_event_diff_hash": "409_CONFLICT"
      }
    },
    "common_headers": {
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    "errors": {
      "standard_error_shape": {
        "error": {
          "code": "string",
          "message": "string",
          "details": {},
          "request_id": "string"
        }
      },
      "common_codes": [
        "UNAUTHORIZED",
        "FORBIDDEN",
        "NOT_FOUND",
        "VALIDATION_ERROR",
        "CONFLICT",
        "RATE_LIMITED",
        "INTERNAL_ERROR"
      ]
    }
  },
  "schemas": {
    "User": {
      "id": "usr_123",
      "line_user_id": "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "display_name": "Pond",
      "picture_url": "https://profile.line-scdn.net/xxx",
      "created_at": "2026-01-03T05:32:00Z",
      "updated_at": "2026-01-03T05:32:00Z"
    },
    "Project": {
      "id": "prj_123",
      "name": "ครอบครัวคุณ Pond",
      "project_code": "aoq0f2i0",
      "owner_user_id": "usr_123",
      "member_count": 2,
      "created_at": "2026-01-03T05:33:00Z"
    },
    "ProjectSettings": {
      "project_id": "prj_123",
      "insight_share_level": "minimal",
      "insight_max_range_days": 365,
      "insight_max_rows": 500,
      "allow_note_share": false,
      "created_at": "2026-01-03T05:33:00Z",
      "updated_at": "2026-01-03T05:33:00Z"
    },
    "ProjectMember": {
      "id": "mem_123",
      "project_id": "prj_123",
      "user_id": "usr_123",
      "display_name": "Pond Titipong",
      "nick_name": "ปอนด์",
      "role": "owner",
      "is_active": true,
      "joined_at": "2026-01-03T05:33:10Z"
    },
    "Category": {
      "id": "cat_123",
      "project_id": "prj_123",
      "type": "expense",
      "name_th": "เดินทาง",
      "name_en": "Travel",
      "icon_key": "ic_bus",
      "color": "#E74C3C",
      "sort_order": 10,
      "is_active": true,
      "created_at": "2026-01-03T05:35:00Z",
      "updated_at": "2026-01-03T05:35:00Z"
    },
    "Transaction": {
      "id": "txn_123",
      "project_id": "prj_123",
      "created_by_user_id": "usr_123",
      "type": "expense",
      "category_id": "cat_123",
      "amount_satang": 35000,
      "currency": "THB",
      "note": "ค่าเดินทาง",
      "occurred_at": "2026-01-03T03:54:59Z",
      "created_at": "2026-01-03T05:36:10Z",
      "updated_at": "2026-01-03T05:36:10Z",
      "deleted_at": null
    },
    "Budget": {
      "id": "bud_123",
      "project_id": "prj_123",
      "category_id": "cat_123",
      "month_yyyymm": 202601,
      "limit_amount_satang": 300000,
      "created_at": "2026-01-03T05:40:00Z",
      "updated_at": "2026-01-03T05:40:00Z"
    },
    "ReportBudgetVsActualRow": {
      "category_id": "cat_123",
      "category_name_th": "เดินทาง",
      "type": "expense",
      "budget_limit_satang": 300000,
      "actual_spent_satang": 35000,
      "remaining_satang": 265000,
      "status": "UNDER_BUDGET"
    },
    "RecurringRule": {
      "id": "rr_123",
      "project_id": "prj_123",
      "created_by_user_id": "usr_123",
      "type": "expense",
      "category_id": "cat_food",
      "amount_satang": 150000,
      "currency": "THB",
      "note": "อาหารประจำ",
      "freq": "monthly",
      "day_of_week": null,
      "day_of_month": 1,
      "start_date": "2026-01-03",
      "next_run_date": "2026-02-01",
      "remind_days": 3,
      "is_active": true,
      "created_at": "2026-01-03T05:45:00Z",
      "updated_at": "2026-01-03T05:45:00Z"
    },
    "BotSecurityHeadersExample": {
      "X-BOT-ID": "botpress-prod",
      "X-BOT-TS": "1700000000",
      "X-BOT-NONCE": "550e8400-e29b-41d4-a716-446655440000",
      "X-BOT-SIGN": "base64(hmac_sha256(secret, signing_string))",
      "X-BOT-TOKEN": "optional-static-token"
    },
    "BotIdempotencyRecord": {
      "event_id": "line_msg_1234567890",
      "scope": "bot.transactions.create",
      "request_hash": "sha256hex(body)",
      "response_json": "{...}",
      "created_at": "2026-01-03T06:00:00Z",
      "expires_at": "2026-02-03T06:00:00Z"
    },
    "BotNonceRecord": {
      "bot_id": "botpress-prod",
      "nonce": "550e8400-e29b-41d4-a716-446655440000",
      "ts": 1700000000,
      "created_at": "2026-01-03T06:00:00Z",
      "expires_at": "2026-01-03T06:10:00Z"
    },
    "InsightRecord": {
      "id": "ins_001",
      "project_id": "prj_123",
      "created_by_user_id": "usr_123",
      "source": "botpress",
      "insight_type": "MONTHLY_SPEND_TOP3",
      "summary_text": "เดือนนี้ใช้มากสุด: อาหาร 5,200 / เดินทาง 1,800 / ช้อปปิ้ง 900",
      "payload_json": {
        "top3": [
          {
            "category_id": "cat_food",
            "total_satang": 520000
          }
        ]
      },
      "created_at": "2026-01-03T06:15:00Z"
    }
  },
  "endpoints": [
    {
      "name": "Auth - Start LINE Login",
      "method": "GET",
      "path": "/auth/line/login",
      "description": "Redirect ไป LINE OAuth authorize (ไม่ใช่ JSON)",
      "request": {
        "query": {
          "redirect": "/app"
        },
        "body": null
      },
      "responses": [
        {
          "status": 302,
          "headers": {
            "Location": "https://access.line.me/oauth2/v2.1/authorize?...",
            "Set-Cookie": "session=...; HttpOnly; SameSite=Lax"
          },
          "body": null
        }
      ]
    },
    {
      "name": "Auth - LINE Callback",
      "method": "GET",
      "path": "/auth/line/callback",
      "description": "LINE redirect กลับมา พร้อม code/state แล้วระบบแลก token + โปรไฟล์ สร้าง user/session",
      "request": {
        "query": {
          "code": "AUTH_CODE_FROM_LINE",
          "state": "CSRF_STATE"
        },
        "body": null
      },
      "responses": [
        {
          "status": 302,
          "headers": {
            "Location": "/app",
            "Set-Cookie": "session=...; HttpOnly; SameSite=Lax"
          },
          "body": null
        },
        {
          "status": 400,
          "body": {
            "error": {
              "code": "VALIDATION_ERROR",
              "message": "Invalid state or missing code",
              "details": {},
              "request_id": "req_001"
            }
          }
        }
      ]
    },
    {
      "name": "Auth - Logout",
      "method": "POST",
      "path": "/auth/logout",
      "description": "ล้าง session",
      "request": {
        "body": {}
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "ok": true
          }
        }
      ]
    },
    {
      "name": "Me - Get Current User",
      "method": "GET",
      "path": "/api/v1/me",
      "description": "ข้อมูลผู้ใช้ที่ล็อกอินอยู่ + current_project_id",
      "request": {
        "headers": {
          "Authorization": "Bearer <token> (optional if cookie session)"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "user": {
              "id": "usr_123",
              "display_name": "Pond",
              "picture_url": "https://profile.line-scdn.net/xxx"
            },
            "current_project_id": "prj_123"
          }
        },
        {
          "status": 401,
          "body": {
            "error": {
              "code": "UNAUTHORIZED",
              "message": "Login required",
              "details": {},
              "request_id": "req_002"
            }
          }
        }
      ]
    },
    {
      "name": "Projects - List",
      "method": "GET",
      "path": "/api/v1/projects",
      "description": "รายชื่อโปรเจคที่ user เป็นสมาชิก",
      "request": {},
      "responses": [
        {
          "status": 200,
          "body": {
            "projects": [
              {
                "id": "prj_123",
                "name": "ครอบครัวคุณ Pond",
                "project_code": "aoq0f2i0",
                "member_count": 2,
                "role": "owner",
                "created_at": "2026-01-03T05:33:00Z"
              }
            ]
          }
        }
      ]
    },
    {
      "name": "Projects - Create",
      "method": "POST",
      "path": "/api/v1/projects",
      "description": "สร้างโปรเจคใหม่ และ set เป็น current project",
      "request": {
        "body": {
          "name": "ทริปเชียงใหม่",
          "project_code": "aoq0f2i0"
        }
      },
      "responses": [
        {
          "status": 201,
          "body": {
            "project": {
              "id": "prj_999",
              "name": "ทริปเชียงใหม่",
              "project_code": "aoq0f2i0",
              "owner_user_id": "usr_123",
              "member_count": 1,
              "created_at": "2026-01-03T05:50:00Z"
            },
            "current_project_id": "prj_999"
          }
        },
        {
          "status": 409,
          "body": {
            "error": {
              "code": "CONFLICT",
              "message": "project_code already exists",
              "details": {
                "field": "project_code"
              },
              "request_id": "req_003"
            }
          }
        }
      ]
    },
    {
      "name": "Projects - Join by Code",
      "method": "POST",
      "path": "/api/v1/projects/join",
      "description": "เข้าร่วมโปรเจคด้วย project_code (ใช้ได้ทั้งเว็บและ LINE)",
      "request": {
        "body": {
          "project_code": "aoq0f2i0"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "joined": true,
            "project": {
              "id": "prj_999",
              "name": "ทริปเชียงใหม่",
              "project_code": "aoq0f2i0",
              "member_count": 2
            },
            "current_project_id": "prj_999"
          }
        },
        {
          "status": 404,
          "body": {
            "error": {
              "code": "NOT_FOUND",
              "message": "Project not found",
              "details": {},
              "request_id": "req_004"
            }
          }
        }
      ]
    },
    {
      "name": "Projects - Switch Current",
      "method": "POST",
      "path": "/api/v1/projects/{project_id}/switch",
      "description": "ตั้ง current project ใน session",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "body": {}
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "current_project_id": "prj_123"
          }
        },
        {
          "status": 403,
          "body": {
            "error": {
              "code": "FORBIDDEN",
              "message": "Not a member of this project",
              "details": {},
              "request_id": "req_005"
            }
          }
        }
      ]
    },
    {
      "name": "Project Settings - Get",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/settings",
      "description": "ตั้งค่านโยบายแชร์ข้อมูลสำหรับ insight (Mode B)",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "settings": {
              "project_id": "prj_123",
              "insight_share_level": "minimal",
              "insight_max_range_days": 365,
              "insight_max_rows": 500,
              "allow_note_share": false
            }
          }
        }
      ]
    },
    {
      "name": "Project Settings - Update (Owner/Admin)",
      "method": "PATCH",
      "path": "/api/v1/projects/{project_id}/settings",
      "description": "แก้นโยบายแชร์ข้อมูล (เช่น เปิดส่ง note)",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "body": {
          "insight_share_level": "with_notes",
          "allow_note_share": true,
          "insight_max_rows": 300
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "settings": {
              "project_id": "prj_123",
              "insight_share_level": "with_notes",
              "insight_max_range_days": 365,
              "insight_max_rows": 300,
              "allow_note_share": true
            }
          }
        }
      ]
    },
    {
      "name": "Members - List",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/members",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "members": [
              {
                "id": "mem_123",
                "user_id": "usr_123",
                "display_name": "Pond Titipong",
                "nick_name": "ปอนด์",
                "role": "owner",
                "is_active": true
              },
              {
                "id": "mem_124",
                "user_id": "usr_456",
                "display_name": "Mom",
                "nick_name": "แม่",
                "role": "member",
                "is_active": true
              }
            ]
          }
        }
      ]
    },
    {
      "name": "Members - Invite (Owner Only)",
      "method": "POST",
      "path": "/api/v1/projects/{project_id}/members/invite",
      "description": "เชิญสมาชิก (สร้าง invite token)",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "body": {
          "display_name": "น้อง",
          "nick_name": "น้อง",
          "role": "member"
        }
      },
      "responses": [
        {
          "status": 201,
          "body": {
            "invite": {
              "invite_code": "inv_abc123",
              "expires_at": "2026-01-10T00:00:00Z",
              "project_id": "prj_123",
              "role": "member"
            },
            "share_text": "เข้าร่วมครอบครัวด้วยโค้ด: inv_abc123 หรือพิมพ์ใน LINE: #project aoq0f2i0"
          }
        }
      ]
    },
    {
      "name": "Categories - List",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/categories",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "query": {
          "type": "expense"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "categories": [
              {
                "id": "cat_food",
                "type": "expense",
                "name_th": "อาหาร",
                "icon_key": "ic_food",
                "color": "#E74C3C",
                "sort_order": 1,
                "is_active": true
              },
              {
                "id": "cat_travel",
                "type": "expense",
                "name_th": "เดินทาง",
                "icon_key": "ic_bus",
                "color": "#E74C3C",
                "sort_order": 2,
                "is_active": true
              }
            ]
          }
        }
      ]
    },
    {
      "name": "Categories - Create",
      "method": "POST",
      "path": "/api/v1/projects/{project_id}/categories",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "body": {
          "type": "expense",
          "name_th": "ค่าน้ำดื่ม",
          "name_en": "Water",
          "icon_key": "ic_water",
          "color": "#E74C3C",
          "sort_order": 20
        }
      },
      "responses": [
        {
          "status": 201,
          "body": {
            "category": {
              "id": "cat_777",
              "project_id": "prj_123",
              "type": "expense",
              "name_th": "ค่าน้ำดื่ม",
              "name_en": "Water",
              "icon_key": "ic_water",
              "color": "#E74C3C",
              "sort_order": 20,
              "is_active": true,
              "created_at": "2026-01-03T06:00:00Z",
              "updated_at": "2026-01-03T06:00:00Z"
            }
          }
        }
      ]
    },
    {
      "name": "Transactions - List",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/transactions",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "query": {
          "from": "2026-01-01",
          "to": "2026-01-31",
          "type": "expense",
          "category_id": "cat_travel",
          "q": "ค่า",
          "page": 1,
          "page_size": 50
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "items": [
              {
                "id": "txn_123",
                "type": "expense",
                "category_id": "cat_travel",
                "amount_satang": 35000,
                "currency": "THB",
                "note": "ค่าเดินทาง",
                "occurred_at": "2026-01-03T03:54:59Z",
                "created_by_user_id": "usr_123"
              }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1
          }
        }
      ]
    },
    {
      "name": "Transactions - Create",
      "method": "POST",
      "path": "/api/v1/projects/{project_id}/transactions",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "body": {
          "type": "expense",
          "category_id": "cat_travel",
          "amount_satang": 35000,
          "occurred_at": "2026-01-03T12:54:59+07:00",
          "note": "ค่าเดินทาง"
        }
      },
      "responses": [
        {
          "status": 201,
          "body": {
            "transaction": {
              "id": "txn_124",
              "project_id": "prj_123",
              "type": "expense",
              "category_id": "cat_travel",
              "amount_satang": 35000,
              "currency": "THB",
              "occurred_at": "2026-01-03T03:54:59Z",
              "note": "ค่าเดินทาง",
              "created_by_user_id": "usr_123",
              "created_at": "2026-01-03T06:05:00Z",
              "updated_at": "2026-01-03T06:05:00Z",
              "deleted_at": null
            }
          }
        }
      ]
    },
    {
      "name": "Budgets - List by Month",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/budgets",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "query": {
          "month": 202601
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "month_yyyymm": 202601,
            "budgets": [
              {
                "category_id": "cat_food",
                "limit_amount_satang": 500000
              },
              {
                "category_id": "cat_travel",
                "limit_amount_satang": 300000
              }
            ]
          }
        }
      ]
    },
    {
      "name": "Budgets - Upsert",
      "method": "PUT",
      "path": "/api/v1/projects/{project_id}/budgets/{category_id}",
      "request": {
        "path_params": {
          "project_id": "prj_123",
          "category_id": "cat_travel"
        },
        "query": {
          "month": 202601
        },
        "body": {
          "limit_amount_satang": 350000
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "budget": {
              "project_id": "prj_123",
              "category_id": "cat_travel",
              "month_yyyymm": 202601,
              "limit_amount_satang": 350000,
              "updated_at": "2026-01-03T06:10:00Z"
            }
          }
        }
      ]
    },
    {
      "name": "Reports - Summary",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/reports/summary",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "query": {
          "from": "2026-01-01",
          "to": "2026-01-31"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "from": "2026-01-01",
            "to": "2026-01-31",
            "income_total_satang": 1500000,
            "expense_total_satang": 35000,
            "net_satang": 1465000,
            "currency": "THB"
          }
        }
      ]
    },
    {
      "name": "Reports - By Category (Month)",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/reports/by-category",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "query": {
          "month": 202601,
          "type": "expense"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "month_yyyymm": 202601,
            "type": "expense",
            "rows": [
              {
                "category_id": "cat_travel",
                "category_name_th": "เดินทาง",
                "total_satang": 35000,
                "tx_count": 1
              }
            ]
          }
        }
      ]
    },
    {
      "name": "Reports - Budget vs Actual (Month)",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/reports/budget-vs-actual",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        },
        "query": {
          "month": 202601,
          "type": "expense"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "month_yyyymm": 202601,
            "type": "expense",
            "rows": [
              {
                "category_id": "cat_travel",
                "category_name_th": "เดินทาง",
                "budget_limit_satang": 300000,
                "actual_spent_satang": 35000,
                "remaining_satang": 265000,
                "status": "UNDER_BUDGET"
              }
            ]
          }
        }
      ]
    },
    {
      "name": "Recurring - List",
      "method": "GET",
      "path": "/api/v1/projects/{project_id}/recurring",
      "request": {
        "path_params": {
          "project_id": "prj_123"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "rules": [
              {
                "id": "rr_123",
                "type": "expense",
                "category_id": "cat_food",
                "amount_satang": 150000,
                "note": "อาหารประจำ",
                "freq": "monthly",
                "day_of_month": 1,
                "start_date": "2026-01-03",
                "next_run_date": "2026-02-01",
                "remind_days": 3,
                "is_active": true
              }
            ]
          }
        }
      ]
    },

    {
      "name": "BOT - Context Resolve",
      "method": "POST",
      "path": "/api/v1/bot/context/resolve",
      "description": "Botpress เรียกเพื่อ resolve user + project + policy (requires Token+HMAC)",
      "security": {
        "bot_hmac_required": true,
        "idempotency_required": false
      },
      "request": {
        "headers": {
          "X-BOT-ID": "botpress-prod",
          "X-BOT-TS": "1700000000",
          "X-BOT-NONCE": "550e8400-e29b-41d4-a716-446655440000",
          "X-BOT-SIGN": "base64(...)"
        },
        "body": {
          "line_user_id": "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
          "project_code": "aoq0f2i0",
          "request_locale": "th"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "ok": true,
            "user": {
              "id": "usr_123",
              "display_name": "Pond"
            },
            "project": {
              "id": "prj_123",
              "name": "ครอบครัว",
              "project_code": "aoq0f2i0"
            },
            "permissions": {
              "role": "member"
            },
            "policy": {
              "insight_share_level": "minimal",
              "insight_max_range_days": 365,
              "insight_max_rows": 500,
              "allow_note_share": false
            }
          }
        },
        {
          "status": 401,
          "body": {
            "error": {
              "code": "UNAUTHORIZED",
              "message": "Invalid bot signature",
              "details": {},
              "request_id": "req_bot_001"
            }
          }
        }
      ]
    },
    {
      "name": "BOT - Create Transaction",
      "method": "POST",
      "path": "/api/v1/bot/transactions/create",
      "description": "Botpress สร้างรายการรายรับ/รายจ่าย (requires Token+HMAC + idempotency event_id)",
      "security": {
        "bot_hmac_required": true,
        "idempotency_required": true
      },
      "request": {
        "headers": {
          "X-BOT-ID": "botpress-prod",
          "X-BOT-TS": "1700000000",
          "X-BOT-NONCE": "550e8400-e29b-41d4-a716-446655440000",
          "X-BOT-SIGN": "base64(...)"
        },
        "body": {
          "event_id": "line_msg_1234567890",
          "line_user_id": "Uxxxx",
          "project_code": "aoq0f2i0",
          "type": "expense",
          "amount_satang": 35000,
          "category_text": "เดินทาง",
          "note": "ค่ารถ",
          "occurred_at": "2026-01-03T12:34:00+07:00"
        }
      },
      "responses": [
        {
          "status": 201,
          "body": {
            "ok": true,
            "transaction": {
              "id": "txn_124",
              "type": "expense",
              "amount_satang": 35000,
              "category_id": "cat_travel",
              "category_name_th": "เดินทาง",
              "occurred_at": "2026-01-03T05:34:00Z"
            },
            "budget_hint": {
              "month_yyyymm": 202601,
              "category_id": "cat_travel",
              "remaining_satang": 265000,
              "status": "UNDER_BUDGET"
            }
          }
        },
        {
          "status": 409,
          "body": {
            "error": {
              "code": "CONFLICT",
              "message": "Idempotency key reused with different payload",
              "details": {
                "event_id": "line_msg_1234567890"
              },
              "request_id": "req_bot_002"
            }
          }
        }
      ]
    },
    {
      "name": "BOT - Update Last Transaction",
      "method": "POST",
      "path": "/api/v1/bot/transactions/update-last",
      "description": "แก้ไขรายการล่าสุดของ user ในโปรเจคปัจจุบัน (idempotency required)",
      "security": {
        "bot_hmac_required": true,
        "idempotency_required": true
      },
      "request": {
        "headers": {
          "X-BOT-ID": "botpress-prod",
          "X-BOT-TS": "1700000000",
          "X-BOT-NONCE": "550e8400-e29b-41d4-a716-446655440000",
          "X-BOT-SIGN": "base64(...)"
        },
        "body": {
          "event_id": "line_msg_1234567891",
          "line_user_id": "Uxxxx",
          "field": "amount_satang",
          "value": 40000
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "ok": true,
            "updated_transaction_id": "txn_124"
          }
        }
      ]
    },
    {
      "name": "BOT - Delete Last Transaction",
      "method": "POST",
      "path": "/api/v1/bot/transactions/delete-last",
      "description": "ลบ (soft delete) รายการล่าสุด (idempotency required)",
      "security": {
        "bot_hmac_required": true,
        "idempotency_required": true
      },
      "request": {
        "headers": {
          "X-BOT-ID": "botpress-prod",
          "X-BOT-TS": "1700000000",
          "X-BOT-NONCE": "550e8400-e29b-41d4-a716-446655440000",
          "X-BOT-SIGN": "base64(...)"
        },
        "body": {
          "event_id": "line_msg_1234567892",
          "line_user_id": "Uxxxx"
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "ok": true,
            "deleted_transaction_id": "txn_124"
          }
        }
      ]
    },
    {
      "name": "BOT - Export Dataset for Insights (Mode B)",
      "method": "POST",
      "path": "/api/v1/bot/insights/export",
      "description": "ส่งชุดข้อมูลธุรกรรมบางส่วนให้ Botpress วิเคราะห์ (policy enforced)",
      "security": {
        "bot_hmac_required": true,
        "idempotency_required": true
      },
      "request": {
        "headers": {
          "X-BOT-ID": "botpress-prod",
          "X-BOT-TS": "1700000000",
          "X-BOT-NONCE": "550e8400-e29b-41d4-a716-446655440000",
          "X-BOT-SIGN": "base64(...)"
        },
        "body": {
          "event_id": "line_msg_1234567893",
          "line_user_id": "Uxxxx",
          "project_code": "aoq0f2i0",
          "range": {
            "from": "2026-01-01",
            "to": "2026-01-31"
          },
          "limit": 500,
          "share_level": "minimal",
          "include": {
            "categories": true,
            "budgets": true
          }
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "ok": true,
            "policy_applied": {
              "max_range_days": 365,
              "max_rows": 500,
              "note_included": false
            },
            "project": {
              "id": "prj_123",
              "name": "ครอบครัว"
            },
            "dataset": {
              "transactions": [
                {
                  "id": "txn_1",
                  "type": "expense",
                  "amount_satang": 35000,
                  "occurred_date": "2026-01-03",
                  "category_id": "cat_travel"
                }
              ],
              "categories": [
                {
                  "id": "cat_travel",
                  "type": "expense",
                  "name_th": "เดินทาง"
                }
              ],
              "budgets": [
                {
                  "category_id": "cat_travel",
                  "month_yyyymm": 202601,
                  "limit_amount_satang": 300000
                }
              ]
            }
          }
        }
      ]
    },
    {
      "name": "BOT - Save Insight Result (Optional)",
      "method": "POST",
      "path": "/api/v1/bot/insights/save",
      "description": "บันทึก insight ที่ Botpress สรุปกลับมา (idempotency required)",
      "security": {
        "bot_hmac_required": true,
        "idempotency_required": true
      },
      "request": {
        "headers": {
          "X-BOT-ID": "botpress-prod",
          "X-BOT-TS": "1700000000",
          "X-BOT-NONCE": "550e8400-e29b-41d4-a716-446655440000",
          "X-BOT-SIGN": "base64(...)"
        },
        "body": {
          "event_id": "line_msg_1234567894",
          "line_user_id": "Uxxxx",
          "project_id": "prj_123",
          "insight_type": "MONTHLY_SPEND_TOP3",
          "summary_text": "เดือนนี้ใช้มากสุด: อาหาร 5,200 / เดินทาง 1,800 / ช้อปปิ้ง 900",
          "payload_json": {
            "top3": [
              {
                "category_id": "cat_food",
                "total_satang": 520000
              },
              {
                "category_id": "cat_travel",
                "total_satang": 180000
              }
            ]
          }
        }
      },
      "responses": [
        {
          "status": 201,
          "body": {
            "ok": true,
            "insight_id": "ins_001"
          }
        }
      ]
    },
    {
      "name": "LINE Bot - Webhook (if using Flask as LINE receiver)",
      "method": "POST",
      "path": "/line/webhook",
      "description": "รับ event จาก LINE Messaging API (ไม่ใช่ API สำหรับ frontend). ถ้าใช้ Botpress LINE Channel อาจไม่ต้องมี endpoint นี้",
      "request": {
        "headers": {
          "X-Line-Signature": "base64..."
        },
        "body": {
          "events": [
            {
              "type": "message",
              "message": {
                "type": "text",
                "id": "123",
                "text": "จ่าย 350 เดินทาง ค่ารถ"
              },
              "source": {
                "type": "user",
                "userId": "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              },
              "replyToken": "replyToken...",
              "timestamp": 1767412345678
            }
          ]
        }
      },
      "responses": [
        {
          "status": 200,
          "body": {
            "ok": true
          }
        }
      ]
    }
  ]
}
```

## Response:
````markdown
# COMMAND_SPECS_TH.md
## LINE Chatbot Commands (TH) — Pattern + Regex Intent (v1.1 Botpress Mode B)

> เป้าหมาย: ให้คนในบ้าน “พิมพ์สั้นๆ แล้วบันทึกได้จริง” + มีคำสั่ง “ขอ insight” ที่อนุญาตส่งข้อมูลบางส่วนไป Botpress  
> โหมด B: อนุญาตส่ง “ธุรกรรมบางส่วน” (จำกัดช่วงเวลา/จำนวนแถว/fields) เพื่อทำ insight

---

## 0) หลักการออกแบบคำสั่ง (อัปเดต)
1) **บันทึกไว**: 1 บรรทัดจบ  
2) **แก้/ลบไว**: `แก้ล่าสุด`, `ลบล่าสุด`  
3) **ขอ insight ได้**: `วิเคราะห์...`, `อินไซต์...`  
4) **Consent ชัด**: คำสั่งเปิด/ปิดการส่งข้อมูลเพื่อวิเคราะห์  
5) **Privacy by default**: ค่าเริ่มต้นส่งแบบ **minimal (ไม่ส่ง note)**

---

## 1) Tokens / Slot Extraction (มาตรฐาน)

### 1.1 Amount (เงิน)
รองรับ: `350`, `350.50`, `350บาท`, `1,250`, `350฿`

```regex
(?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)\s*(?:บาท|บ\.|฿)?
````

### 1.2 Date (วันที่)

รองรับ: `วันนี้`, `เมื่อวาน`, `3/1`, `03/01/2026`, `2026-01-03`

```regex
(?P<date>\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}|วันนี้|เมื่อวาน)
```

### 1.3 Date Range (ช่วงเวลา)

รองรับ: `3/1-3/7`, `2026-01-01 ถึง 2026-01-31`, `7วัน`, `30วัน`, `เดือนนี้`, `ปีนี้`

```regex
(?P<range>
  (?P<from>\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})
  \s*(?:\-|ถึง)\s*
  (?P<to>\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})
| (?P<days>\d{1,3})\s*วัน
| เดือนนี้
| ปีนี้
| วันนี้
| เมื่อวาน
)
```

> Implementation note: regex ข้างบนมี whitespace/newlines เพื่ออ่านง่าย ในโค้ดให้ compile ด้วย flags `re.VERBOSE`

### 1.4 Time (เวลา)

รองรับ: `10:54`, `10.54`, `10:54:59`

```regex
(?P<time>\d{1,2}[:\.]\d{2}(?:[:\.]\d{2})?)
```

### 1.5 Category (หมวด)

*   ไม่ใช้ regex ล้วน ๆ (ต้องเทียบ DB + alias)
*   ใช้กลยุทธ์:
    *   longest match จากรายการ category/alias ของโปรเจค
    *   ถ้าไม่เจอ → เสนอ 3–5 ตัวเลือกให้เลือกเลข

* * *

2) Project / Context Commands
-----------------------------

### 2.1 สลับ/เข้าร่วมโปรเจคด้วย project code

ตัวอย่าง:

*   `#project aoq0f2i0`
*   `เข้าร่วม aoq0f2i0`
*   `join aoq0f2i0`

**Intent:** `PROJECT_SWITCH_OR_JOIN`

```regex
^(?:#\s*project\s+|เข้าร่วม\s+|join\s+)(?P<code>[a-z0-9]{6,12})\s*$
```

**Behavior**

*   ถ้า user เป็นสมาชิก → switch current\_project
*   ถ้าไม่เป็นสมาชิกแต่โปรเจคมีอยู่ → join หรือ invite flow

* * *

3) Core CRUD Commands (Transactions)
------------------------------------

### 3.1 เพิ่มรายจ่าย

ตัวอย่าง:

*   `จ่าย 350 เดินทาง ค่ารถ`
*   `ซื้อ 129 กาแฟ`
*   `จ่าย 60 เมื่อวาน อาหาร ข้าวมันไก่`

**Intent:** `TXN_CREATE_EXPENSE`

```regex
^(?P<verb>จ่าย|ซื้อ|เสีย|ใช้)\s*(?P<rest>.+)$
```

**Parsing Strategy (rest)**

1.  หา amount
2.  หา date/time (optional)
3.  หา category จาก DB (ไทย/อังกฤษ/alias)
4.  ที่เหลือ = note

* * *

### 3.2 เพิ่มรายรับ

ตัวอย่าง:

*   `รับ 15000 เงินเดือน`
*   `ได้ 200 ขายของ`

**Intent:** `TXN_CREATE_INCOME`

```regex
^(?P<verb>รับ|ได้|รายรับ)\s*(?P<rest>.+)$
```

* * *

### 3.3 แก้ไข “รายการล่าสุด”

ตัวอย่าง:

*   `แก้ล่าสุด 300`
*   `แก้ล่าสุด หมวด อาหาร`
*   `แก้ล่าสุด โน้ต ค่ารถไปกลับ`
*   `แก้ล่าสุด วันที่ เมื่อวาน`

**Intent:** `TXN_UPDATE_LAST`

```regex
^แก้ล่าสุด\s+(?:(?P<field>จำนวน|เงิน|หมวด|โน้ต|หมายเหตุ|วันที่|เวลา)\s*)?(?P<value>.+)$
```

**Rules**

*   ถ้าไม่ระบุ field และ value เป็นตัวเลข → ถือว่าแก้ amount
*   ถ้า value เป็น “วันนี้/เมื่อวาน/3/1” → ถือว่าแก้ date
*   ถ้า value เป็น “10:30” → ถือว่าแก้ time

* * *

### 3.4 ลบ “รายการล่าสุด”

ตัวอย่าง:

*   `ลบล่าสุด`
*   `ยกเลิกล่าสุด`
*   `undo`

**Intent:** `TXN_DELETE_LAST`

```regex
^(ลบล่าสุด|ยกเลิกล่าสุด|undo)\s*$
```

* * *

### 3.5 ดูรายการ

ตัวอย่าง:

*   `รายการวันนี้`
*   `รายการเดือนนี้`
*   `ดูรายการ อาหาร 7วัน`
*   `รายการ เดินทาง 3/1-3/7`

**Intent:** `TXN_LIST`

```regex
^(?:รายการ|ดูรายการ)\s*(?P<rest>.*)$
```

* * *

4) Summary / Budget Commands
----------------------------

### 4.1 สรุป

ตัวอย่าง:

*   `สรุปวันนี้`
*   `สรุปเดือนนี้`
*   `สรุป 7วัน`

**Intent:** `REPORT_SUMMARY`

```regex
^สรุป\s*(?P<range>วันนี้|เมื่อวาน|เดือนนี้|ปีนี้|\d{1,3}\s*วัน|\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?\s*(?:\-|ถึง)\s*\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?)\s*$
```

* * *

### 4.2 งบ (ดูสถานะ)

ตัวอย่าง:

*   `งบ`
*   `งบทั้งหมด`
*   `งบ เดินทาง`
*   `งบเดือนนี้`

**Intent:** `BUDGET_STATUS`

```regex
^งบ\s*(?P<rest>.*)$
```

* * *

### 4.3 ตั้งงบ

ตัวอย่าง:

*   `ตั้งงบ เดินทาง 3000`
*   `งบ อาหาร = 5000`
*   `กำหนดงบ ค่าไฟ 1200`

**Intent:** `BUDGET_SET`

```regex
^(?:ตั้งงบ|กำหนดงบ|งบ)\s+(?P<category>.+?)\s*(?:=)?\s*(?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)\s*(?:บาท|บ\.|฿)?\s*$
```

* * *

5) Insight Commands (Mode B) ⭐️
-------------------------------

> Insight = Botpress จะ “ขอ export dataset” จาก Flask แล้วนำไปสรุป  
> ค่าเริ่มต้น: `minimal` (ไม่ส่ง note)

### 5.1 ขอให้วิเคราะห์/อินไซต์

ตัวอย่าง:

*   `วิเคราะห์เดือนนี้`
*   `อินไซต์ 30วัน`
*   `ช่วยดูว่าเดือนนี้ใช้กับอะไรเยอะสุด`
*   `วิเคราะห์ เดินทาง 90วัน`
*   `เทียบเดือนนี้กับเดือนที่แล้ว`

**Intent:** `INSIGHT_REQUEST`

```regex
^(?P<verb>วิเคราะห์|อินไซต์|insight|สรุปเชิงลึก|ช่วยวิเคราะห์)\s*(?P<rest>.*)$
```

**Slot extraction (rest)**

*   range: วันนี้/เดือนนี้/30วัน/3/1-3/7
*   category (optional): match DB
*   compare: ถ้ามีคำว่า `เทียบ|เปรียบเทียบ|vs` → set compare\_mode = true
*   detail: ถ้ามีคำว่า `ละเอียด` → request share\_level = with\_notes (แต่ต้องมี consent)

* * *

### 5.2 เปิด/ปิด “วิเคราะห์ละเอียด” (ส่ง note ได้)

#### เปิด

ตัวอย่าง:

*   `เปิดวิเคราะห์ละเอียด`
*   `อนุญาตส่งรายละเอียด`
*   `เปิดส่งโน้ต`

**Intent:** `INSIGHT_CONSENT_ENABLE_NOTES`

```regex
^(เปิดวิเคราะห์ละเอียด|อนุญาตส่งรายละเอียด|เปิดส่งโน้ต|อนุญาตส่งโน้ต)\s*$
```

#### ปิด

ตัวอย่าง:

*   `ปิดวิเคราะห์ละเอียด`
*   `ไม่อนุญาตส่งรายละเอียด`
*   `ปิดส่งโน้ต`

**Intent:** `INSIGHT_CONSENT_DISABLE_NOTES`

```regex
^(ปิดวิเคราะห์ละเอียด|ไม่อนุญาตส่งรายละเอียด|ปิดส่งโน้ต|ไม่อนุญาตส่งโน้ต)\s*$
```

**Behavior**

*   Bot เรียก Flask:
    *   `PATCH /api/v1/projects/{project_id}/settings` (owner/admin เท่านั้น) หรือ
    *   ถ้าต้องการระดับ user-only: `PATCH /api/v1/me/prefs` (ถ้าคุณเพิ่ม endpoint นี้ภายหลัง)
*   ถ้า user ไม่ใช่ owner/admin ให้บอกว่า “ต้องให้เจ้าของโปรเจคเปิดให้”

* * *

### 5.3 ขอ “ส่งข้อมูลแบบ minimal” (ยืนยันโหมดปลอดภัย)

ตัวอย่าง:

*   `วิเคราะห์แบบปลอดภัย`
*   `วิเคราะห์แบบไม่ส่งรายละเอียด`

**Intent:** `INSIGHT_FORCE_MINIMAL`

```regex
^(วิเคราะห์แบบปลอดภัย|วิเคราะห์แบบไม่ส่งรายละเอียด|insight\s*minimal)\s*$
```

* * *

6) Help / Onboarding
--------------------

### 6.1 ขอความช่วยเหลือ

ตัวอย่าง:

*   `ช่วยเหลือ`
*   `คำสั่ง`
*   `help`

**Intent:** `HELP`

```regex
^(ช่วยเหลือ|help|คำสั่ง)\s*$
```

* * *

7) Ambiguity Handling (รองรับการถามกลับ)
----------------------------------------

### 7.1 ไม่เจอหมวด

*   Bot ส่งตัวเลือก 3–5 หมวด ให้ผู้ใช้ตอบ `1/2/3`
*   ใช้ pending state

### 7.2 หลายโปรเจค / ยังไม่เลือกโปรเจค

*   Bot ให้เลือก หรือให้พิมพ์ `#project CODE`

### 7.3 Insight ขอช่วงยาวเกิน policy

*   ตอบ:
    *   “ช่วงเวลายาวเกิน 365 วัน ขอแบ่งเป็น 3 เดือน/6 เดือน/12 เดือน”
*   และถามให้เลือก

* * *

8) Pending State (State Machine สำหรับแชท)
------------------------------------------

> รองรับทั้ง CRUD และ Insight

### 8.1 States

*   `pending_intent`
*   `pending_payload`
*   `expires_at` (10 นาที)
*   `choices` (เช่น category candidates, range candidates)

### 8.2 ตัวอย่าง: Insight ต้องการเลือกช่วงเวลา

*   User: `วิเคราะห์`
*   Bot: `อยากวิเคราะห์ช่วงไหนครับ? 1) วันนี้ 2) 7 วัน 3) เดือนนี้ 4) 30 วัน`
*   User: `3`
*   Bot: เรียก export dataset แล้วสรุป

* * *

9) Canonical Intent List (v1.1)
-------------------------------

*   `PROJECT_SWITCH_OR_JOIN`
*   `TXN_CREATE_EXPENSE`
*   `TXN_CREATE_INCOME`
*   `TXN_UPDATE_LAST`
*   `TXN_DELETE_LAST`
*   `TXN_LIST`
*   `REPORT_SUMMARY`
*   `BUDGET_STATUS`
*   `BUDGET_SET`
*   `INSIGHT_REQUEST`
*   `INSIGHT_CONSENT_ENABLE_NOTES`
*   `INSIGHT_CONSENT_DISABLE_NOTES`
*   `INSIGHT_FORCE_MINIMAL`
*   `HELP`

* * *

```

ถ้าปอนด์อยากให้ผม “อัปเดต DB_SCHEMA.sql + MIGRATION_PLAN.md” เพิ่มตาราง `bot_nonce`, `idempotency_key`, `project_settings`, `insight` ให้ครบ พร้อม migration `0006_bot_security.sql` ผมจัดให้ต่อได้ทันทีครับ
```

2/2

## Response:
DB\_SCHEMA.sql (Updated v1.1 — Botpress Mode B + Security/Idempotency/Insights)
-------------------------------------------------------------------------------

```sql
-- DB_SCHEMA.sql (v1.1)
-- Product: จดรายรับรายจ่าย (Flask + SQLite)
-- Add: Botpress Mode B (export partial transactions for insights)
-- Add: bot_nonce, idempotency_key, project_settings, insight
-- Money: integer satang
-- Time: ISO-8601 TEXT

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- -----------------------------
-- 0) Migration bookkeeping
-- -----------------------------
CREATE TABLE IF NOT EXISTS schema_migrations (
  version        TEXT PRIMARY KEY,
  applied_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- -----------------------------
-- 1) Users / Auth (LINE)
-- -----------------------------
CREATE TABLE IF NOT EXISTS user (
  id            TEXT PRIMARY KEY,                  -- "usr_xxx"
  line_user_id  TEXT NOT NULL UNIQUE,              -- LINE userId
  display_name  TEXT NOT NULL,
  picture_url   TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_pref (
  user_id             TEXT PRIMARY KEY,
  current_project_id  TEXT,
  locale              TEXT DEFAULT 'th',
  tz                  TEXT DEFAULT 'Asia/Bangkok',
  -- per-user override (optional): minimal | with_notes
  insight_share_level TEXT DEFAULT NULL,
  created_at          TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Optional session table (if server-side sessions)
CREATE TABLE IF NOT EXISTS session (
  id           TEXT PRIMARY KEY,                   -- "ses_xxx"
  user_id      TEXT NOT NULL,
  token_hash   TEXT NOT NULL,
  expires_at   TEXT NOT NULL,
  created_at   TEXT NOT NULL DEFAULT (datetime('now')),
  revoked_at   TEXT,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_session_user_id ON session(user_id);
CREATE INDEX IF NOT EXISTS idx_session_expires  ON session(expires_at);

-- -----------------------------
-- 2) Projects / Membership
-- -----------------------------
CREATE TABLE IF NOT EXISTS project (
  id             TEXT PRIMARY KEY,                 -- "prj_xxx"
  name           TEXT NOT NULL,
  project_code   TEXT NOT NULL UNIQUE,
  owner_user_id  TEXT NOT NULL,
  created_at     TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at     TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at     TEXT,
  FOREIGN KEY (owner_user_id) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_project_owner ON project(owner_user_id);

CREATE TABLE IF NOT EXISTS project_member (
  id          TEXT PRIMARY KEY,                    -- "mem_xxx"
  project_id  TEXT NOT NULL,
  user_id     TEXT NOT NULL,
  role        TEXT NOT NULL CHECK(role IN ('owner','member','admin')),
  nick_name   TEXT,
  is_active   INTEGER NOT NULL DEFAULT 1,
  joined_at   TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  UNIQUE(project_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_member_project ON project_member(project_id);
CREATE INDEX IF NOT EXISTS idx_member_user    ON project_member(user_id);

CREATE TABLE IF NOT EXISTS project_invite (
  id          TEXT PRIMARY KEY,                    -- "inv_xxx"
  project_id  TEXT NOT NULL,
  invite_code TEXT NOT NULL UNIQUE,
  role        TEXT NOT NULL CHECK(role IN ('member','admin')),
  expires_at  TEXT NOT NULL,
  created_by  TEXT NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  used_at     TEXT,
  used_by     TEXT,
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by) REFERENCES user(id),
  FOREIGN KEY (used_by) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_invite_project ON project_invite(project_id);
CREATE INDEX IF NOT EXISTS idx_invite_expires ON project_invite(expires_at);

-- -----------------------------
-- 2.1) Project Settings (NEW)
-- -----------------------------
CREATE TABLE IF NOT EXISTS project_settings (
  project_id              TEXT PRIMARY KEY,
  insight_share_level     TEXT NOT NULL DEFAULT 'minimal' CHECK(insight_share_level IN ('minimal','with_notes')),
  insight_max_range_days  INTEGER NOT NULL DEFAULT 365 CHECK(insight_max_range_days BETWEEN 1 AND 3650),
  insight_max_rows        INTEGER NOT NULL DEFAULT 500 CHECK(insight_max_rows BETWEEN 1 AND 5000),
  allow_note_share        INTEGER NOT NULL DEFAULT 0 CHECK(allow_note_share IN (0,1)),
  created_at              TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at              TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE
);

-- -----------------------------
-- 3) Categories
-- -----------------------------
CREATE TABLE IF NOT EXISTS category (
  id          TEXT PRIMARY KEY,                    -- "cat_xxx"
  project_id  TEXT NOT NULL,
  type        TEXT NOT NULL CHECK(type IN ('income','expense')),
  name_th     TEXT NOT NULL,
  name_en     TEXT,
  icon_key    TEXT NOT NULL DEFAULT 'ic_default',
  color       TEXT,
  sort_order  INTEGER NOT NULL DEFAULT 0,
  is_active   INTEGER NOT NULL DEFAULT 1,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at  TEXT,
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  UNIQUE(project_id, type, name_th)
);

CREATE INDEX IF NOT EXISTS idx_category_project_type ON category(project_id, type);
CREATE INDEX IF NOT EXISTS idx_category_project_sort ON category(project_id, sort_order);

-- -----------------------------
-- 4) Transactions (Ledger)
-- -----------------------------
CREATE TABLE IF NOT EXISTS transaction (
  id                 TEXT PRIMARY KEY,             -- "txn_xxx"
  project_id         TEXT NOT NULL,
  created_by_user_id TEXT NOT NULL,
  type               TEXT NOT NULL CHECK(type IN ('income','expense')),
  category_id        TEXT NOT NULL,
  amount_satang      INTEGER NOT NULL CHECK(amount_satang > 0),
  currency           TEXT NOT NULL DEFAULT 'THB',
  note               TEXT,
  occurred_at        TEXT NOT NULL,                -- ISO-8601
  created_at         TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at         TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at         TEXT,
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by_user_id) REFERENCES user(id),
  FOREIGN KEY (category_id) REFERENCES category(id)
);

CREATE INDEX IF NOT EXISTS idx_txn_project_time      ON transaction(project_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_txn_project_type_time ON transaction(project_id, type, occurred_at);
CREATE INDEX IF NOT EXISTS idx_txn_project_cat_time  ON transaction(project_id, category_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_txn_created_by        ON transaction(created_by_user_id);

-- -----------------------------
-- 5) Budget
-- -----------------------------
CREATE TABLE IF NOT EXISTS budget (
  id                  TEXT PRIMARY KEY,            -- "bud_xxx"
  project_id          TEXT NOT NULL,
  category_id         TEXT NOT NULL,
  month_yyyymm        INTEGER NOT NULL,
  limit_amount_satang INTEGER NOT NULL CHECK(limit_amount_satang >= 0),
  created_at          TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at          TEXT,
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  FOREIGN KEY (category_id) REFERENCES category(id),
  UNIQUE(project_id, category_id, month_yyyymm)
);

CREATE INDEX IF NOT EXISTS idx_budget_project_month ON budget(project_id, month_yyyymm);

-- -----------------------------
-- 6) Recurring
-- -----------------------------
CREATE TABLE IF NOT EXISTS recurring_rule (
  id                 TEXT PRIMARY KEY,             -- "rr_xxx"
  project_id         TEXT NOT NULL,
  created_by_user_id TEXT NOT NULL,
  type               TEXT NOT NULL CHECK(type IN ('income','expense')),
  category_id        TEXT NOT NULL,
  amount_satang      INTEGER NOT NULL CHECK(amount_satang > 0),
  currency           TEXT NOT NULL DEFAULT 'THB',
  note               TEXT,
  freq               TEXT NOT NULL CHECK(freq IN ('daily','weekly','monthly')),
  day_of_week        INTEGER,
  day_of_month       INTEGER,
  start_date         TEXT NOT NULL,
  next_run_date      TEXT NOT NULL,
  remind_days        INTEGER NOT NULL DEFAULT 0,
  is_active          INTEGER NOT NULL DEFAULT 1,
  created_at         TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at         TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at         TEXT,
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by_user_id) REFERENCES user(id),
  FOREIGN KEY (category_id) REFERENCES category(id)
);

CREATE INDEX IF NOT EXISTS idx_rr_project_next ON recurring_rule(project_id, next_run_date, is_active);

CREATE TABLE IF NOT EXISTS recurring_run (
  id                TEXT PRIMARY KEY,              -- "rrun_xxx"
  recurring_rule_id TEXT NOT NULL,
  run_date          TEXT NOT NULL,
  transaction_id    TEXT NOT NULL,
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (recurring_rule_id) REFERENCES recurring_rule(id) ON DELETE CASCADE,
  FOREIGN KEY (transaction_id) REFERENCES transaction(id),
  UNIQUE(recurring_rule_id, run_date)
);

CREATE INDEX IF NOT EXISTS idx_rrun_rule ON recurring_run(recurring_rule_id);

-- -----------------------------
-- 7) Attachments + OCR (optional)
-- -----------------------------
CREATE TABLE IF NOT EXISTS attachment (
  id             TEXT PRIMARY KEY,                 -- "att_xxx"
  transaction_id TEXT NOT NULL,
  file_path      TEXT NOT NULL,
  mime_type      TEXT NOT NULL,
  sha256         TEXT,
  created_at     TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (transaction_id) REFERENCES transaction(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_attachment_txn ON attachment(transaction_id);

CREATE TABLE IF NOT EXISTS ocr_result (
  id             TEXT PRIMARY KEY,                 -- "ocr_xxx"
  attachment_id  TEXT NOT NULL,
  engine         TEXT NOT NULL DEFAULT 'offline',
  confidence     REAL,
  extracted_json TEXT NOT NULL,                    -- JSON string
  created_at     TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (attachment_id) REFERENCES attachment(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ocr_attachment ON ocr_result(attachment_id);

-- -----------------------------
-- 8) Audit Log
-- -----------------------------
CREATE TABLE IF NOT EXISTS audit_log (
  id          TEXT PRIMARY KEY,                    -- "aud_xxx"
  project_id  TEXT NOT NULL,
  user_id     TEXT,
  action      TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id   TEXT NOT NULL,
  before_json TEXT,
  after_json  TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_audit_project_time ON audit_log(project_id, created_at);

-- -----------------------------
-- 9) BOT Security: Nonce + Idempotency (NEW)
-- -----------------------------
CREATE TABLE IF NOT EXISTS bot_nonce (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  bot_id     TEXT NOT NULL,
  nonce      TEXT NOT NULL,
  ts         INTEGER NOT NULL,                     -- unix seconds from X-BOT-TS
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT NOT NULL,
  UNIQUE(bot_id, nonce)
);

CREATE INDEX IF NOT EXISTS idx_bot_nonce_expires ON bot_nonce(expires_at);

CREATE TABLE IF NOT EXISTS idempotency_key (
  event_id      TEXT PRIMARY KEY,                  -- e.g. line message id / bot event id
  scope         TEXT NOT NULL,                      -- e.g. "bot.transactions.create"
  request_hash  TEXT NOT NULL,                      -- sha256 hex
  response_json TEXT NOT NULL,                      -- JSON string
  status_code   INTEGER NOT NULL,                   -- 200/201
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_idem_scope_expires ON idempotency_key(scope, expires_at);

-- -----------------------------
-- 10) Insights storage (NEW, optional but recommended)
-- -----------------------------
CREATE TABLE IF NOT EXISTS insight (
  id                 TEXT PRIMARY KEY,             -- "ins_xxx"
  project_id          TEXT NOT NULL,
  created_by_user_id  TEXT,
  source              TEXT NOT NULL DEFAULT 'botpress',
  insight_type         TEXT NOT NULL,              -- e.g. MONTHLY_SPEND_TOP3
  summary_text         TEXT NOT NULL,
  payload_json         TEXT NOT NULL,              -- JSON string
  created_at           TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by_user_id) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_insight_project_time ON insight(project_id, created_at);

-- -----------------------------
-- 11) Helpful Views
-- -----------------------------
CREATE VIEW IF NOT EXISTS v_monthly_category_totals AS
SELECT
  t.project_id,
  t.type,
  t.category_id,
  CAST(strftime('%Y%m', t.occurred_at) AS INTEGER) AS month_yyyymm,
  SUM(t.amount_satang) AS total_satang,
  COUNT(*) AS tx_count
FROM transaction t
WHERE t.deleted_at IS NULL
GROUP BY t.project_id, t.type, t.category_id, month_yyyymm;
```

* * *

MIGRATION\_PLAN.md (Updated — add 0006\_bot\_security.sql)
----------------------------------------------------------

```markdown
# MIGRATION_PLAN.md
## SQLite Migrations (Flask) — v1.1 (Botpress Mode B)

> อัปเดตสำคัญ: เพิ่มตาราง/นโยบายสำหรับ Botpress Mode B
- project_settings (policy)
- bot_nonce (anti-replay)
- idempotency_key (write idempotency)
- insight (เก็บผลสรุป insight)

---

## 1) โครงสร้างโฟลเดอร์ (แนะนำ)
```

app/  
migrations\_sql/  
0001\_initial.sql  
0002\_add\_invites.sql  
0003\_add\_attachments\_ocr.sql  
0004\_add\_user\_pref.sql  
0005\_indexes\_optimize.sql  
0006\_bot\_security.sql ✅ NEW  
db.py (migration runner)  
schema/DB\_SCHEMA.sql

````

---

## 2) Migration Runner (คงเดิม)
- ใช้ตาราง `schema_migrations` เป็น source of truth
- เรียงไฟล์ตามชื่อ แล้วรันเฉพาะที่ยังไม่เคยรัน
- ก่อนรันทุกครั้ง: สำรองไฟล์ db (backup/rollback)

---

## 3) NEW: 0006_bot_security.sql (รายละเอียด)
### 3.1 เป้าหมาย
- เพิ่ม policy per project สำหรับการ export dataset ไป Botpress
- ป้องกัน replay ด้วย nonce
- กันบันทึกซ้ำด้วย idempotency
- เก็บ insight ที่ Botpress ส่งกลับมา

### 3.2 สิ่งที่สร้าง
- `project_settings`
- `bot_nonce`
- `idempotency_key`
- `insight`
- indexes ที่เกี่ยวข้อง

### 3.3 Data Backfill
- สำหรับโปรเจคเดิม: สร้าง row ใน `project_settings` อัตโนมัติ (default minimal)
  - insight_share_level = 'minimal'
  - allow_note_share = 0
  - max_range_days = 365
  - max_rows = 500

---

## 4) Template: 0006_bot_security.sql (พร้อมใช้งาน)
```sql
-- 0006_bot_security.sql
PRAGMA foreign_keys = ON;

BEGIN;

-- 1) project_settings
CREATE TABLE IF NOT EXISTS project_settings (
  project_id              TEXT PRIMARY KEY,
  insight_share_level     TEXT NOT NULL DEFAULT 'minimal' CHECK(insight_share_level IN ('minimal','with_notes')),
  insight_max_range_days  INTEGER NOT NULL DEFAULT 365 CHECK(insight_max_range_days BETWEEN 1 AND 3650),
  insight_max_rows        INTEGER NOT NULL DEFAULT 500 CHECK(insight_max_rows BETWEEN 1 AND 5000),
  allow_note_share        INTEGER NOT NULL DEFAULT 0 CHECK(allow_note_share IN (0,1)),
  created_at              TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at              TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE
);

-- Backfill defaults for existing projects
INSERT INTO project_settings(project_id)
SELECT p.id
FROM project p
LEFT JOIN project_settings ps ON ps.project_id = p.id
WHERE ps.project_id IS NULL AND p.deleted_at IS NULL;

-- 2) bot_nonce
CREATE TABLE IF NOT EXISTS bot_nonce (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  bot_id     TEXT NOT NULL,
  nonce      TEXT NOT NULL,
  ts         INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT NOT NULL,
  UNIQUE(bot_id, nonce)
);

CREATE INDEX IF NOT EXISTS idx_bot_nonce_expires ON bot_nonce(expires_at);

-- 3) idempotency_key
CREATE TABLE IF NOT EXISTS idempotency_key (
  event_id      TEXT PRIMARY KEY,
  scope         TEXT NOT NULL,
  request_hash  TEXT NOT NULL,
  response_json TEXT NOT NULL,
  status_code   INTEGER NOT NULL,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_idem_scope_expires ON idempotency_key(scope, expires_at);

-- 4) insight
CREATE TABLE IF NOT EXISTS insight (
  id                 TEXT PRIMARY KEY,
  project_id          TEXT NOT NULL,
  created_by_user_id  TEXT,
  source              TEXT NOT NULL DEFAULT 'botpress',
  insight_type         TEXT NOT NULL,
  summary_text         TEXT NOT NULL,
  payload_json         TEXT NOT NULL,
  created_at           TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by_user_id) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_insight_project_time ON insight(project_id, created_at);

INSERT INTO schema_migrations(version) VALUES ('0006_bot_security');

COMMIT;
````

* * *

5) Operational Notes
--------------------

### 5.1 Cleanup jobs (แนะนำ)

*   ลบ nonce หมดอายุ:
    *   `DELETE FROM bot_nonce WHERE expires_at < datetime('now');`
*   ลบ idempotency หมดอายุ:
    *   `DELETE FROM idempotency_key WHERE expires_at < datetime('now');`

ทำเป็น cron ภายในแอป หรือรันเมื่อเริ่มแอปวันละครั้งก็ได้

### 5.2 Policy enforcement

*   ตอน `/api/v1/bot/insights/export`
    *   clamp ช่วงวันที่ไม่เกิน `project_settings.insight_max_range_days`
    *   clamp rows ไม่เกิน `project_settings.insight_max_rows`
    *   ถ้า `allow_note_share=0` → ห้ามส่ง note แม้ขอ with\_notes

* * *

6) Upgrade Paths
----------------

*   New install → รัน 0001..0006 ตามลำดับ
*   Existing install:
    *   ตรวจ version ล่าสุดใน `schema_migrations`
    *   รัน 0006 เพิ่มตารางใหม่โดยไม่กระทบของเก่า

* * *

```

ถ้าปอนด์อยากให้ผม “แยก DB_SCHEMA.sql ออกเป็นชุด migration 0001–0006 แบบไฟล์จริง” ผมก็จัดให้เป็นบล็อกแยกไฟล์ครบเลยได้ครับ (copy วางได้ทันที)
```

## Response:
```markdown
# UI_ROUTES.md
## Mapping: หน้าเว็บ (UI) → API Endpoints ที่เรียก (Flask + LINE Auth + SQLite + Botpress Mode B)

> อัปเดต v1.1: เพิ่มหน้า/เส้นทางที่เกี่ยวกับ “Insight + Consent” (Mode B)  
> Base REST: `/api/v1`  
> Auth Web: Cookie Session (แนะนำ) หรือ Bearer  
> Botpress API: `/api/v1/bot/*` (ไม่เรียกจาก UI ปกติ)

---

## 0) Global Rules (ทุกหน้า)
### 0.1 Auth Guard
- ถ้า API ตอบ `401` → redirect `/login`
- ถ้า API ตอบ `403` → toast “ไม่มีสิทธิ์เข้าถึงโปรเจคนี้”

### 0.2 Current Project Context
- UI ต้องรู้ `current_project_id` ก่อน
- Source: `GET /api/v1/me`
- ถ้าไม่มี → redirect `/members`

### 0.3 Common APIs (ใช้ซ้ำหลายหน้า)
- `GET /api/v1/me`
- `GET /api/v1/projects`
- `POST /api/v1/projects/{project_id}/switch`

---

## 1) /login (LINE Login)
### UI
- ปุ่ม “Login with LINE”

### Calls
- Navigate: `GET /auth/line/login?redirect=/app` (302 ไป LINE)

### Callback
- LINE → `/auth/line/callback` (server set session) → redirect `/app`

---

## 2) /app (Shell / App Layout)
> container + nav + bootstrap

### On load (critical path)
1) `GET /api/v1/me`
2) ถ้า `current_project_id` ว่าง → `/members`
3) Preload:
   - `GET /api/v1/projects`
   - `GET /api/v1/projects/{project_id}/categories?type=expense`
   - `GET /api/v1/projects/{project_id}/categories?type=income`

---

## 3) /ledger (หน้าหลักรายการ)
### On enter
1) `GET /api/v1/me`
2) `GET /api/v1/projects/{project_id}/transactions?from=YYYY-MM-01&to=YYYY-MM-last&type=<tabType>&page=1&page_size=50`
3) `GET /api/v1/projects/{project_id}/reports/summary?from=...&to=...`

### Actions
- Create: `POST /api/v1/projects/{project_id}/transactions`
- Edit: `PATCH /api/v1/projects/{project_id}/transactions/{id}` *(ถ้าคุณเพิ่ม endpoint นี้)*
- Delete: `DELETE /api/v1/projects/{project_id}/transactions/{id}` *(ถ้าคุณเพิ่ม endpoint นี้)*
- Pagination: `GET /transactions?...&page=2`
- (Optional) แสดง “งบคงเหลือหมวดที่เลือก”:
  - `GET /api/v1/projects/{project_id}/reports/budget-vs-actual?month=YYYYMM&type=expense`

---

## 4) /recurring (รายการประจำ)
### On enter
1) `GET /api/v1/me`
2) `GET /api/v1/projects/{project_id}/recurring`

### Actions
- Create: `POST /api/v1/projects/{project_id}/recurring`
- Update: `PATCH /api/v1/projects/{project_id}/recurring/{id}`
- Run due (admin): `POST /api/v1/projects/{project_id}/recurring/run-due`

---

## 5) /reports (รายงาน)
### On enter
1) `GET /api/v1/me`
2) `GET /api/v1/projects/{project_id}/reports/budget-vs-actual?month=YYYYMM&type=expense`
3) `GET /api/v1/projects/{project_id}/reports/by-category?month=YYYYMM&type=expense`
4) (optional) `GET /api/v1/projects/{project_id}/reports/trend?months=12`

### Drilldown (tap category)
- Navigate: `/category/{category_id}`
- Call:
  - `GET /api/v1/projects/{project_id}/transactions?from=...&to=...&category_id={category_id}&page=1`

---

## 6) /categories (หมวดบัญชี)
### On enter
1) `GET /api/v1/me`
2) `GET /api/v1/projects/{project_id}/categories?type=<expense|income>`
3) (ใช้ไป/สรุปต่อหมวด):
   - `GET /api/v1/projects/{project_id}/reports/by-category?month=YYYYMM&type=<expense|income>`

### Actions
- Create: `POST /api/v1/projects/{project_id}/categories`
- Update: `PATCH /api/v1/projects/{project_id}/categories/{category_id}`
- Delete: `DELETE /api/v1/projects/{project_id}/categories/{category_id}`

---

## 7) /budget (งบประมาณ)
### On enter
1) `GET /api/v1/me`
2) `GET /api/v1/projects/{project_id}/budgets?month=YYYYMM`
3) `GET /api/v1/projects/{project_id}/reports/budget-vs-actual?month=YYYYMM&type=expense`

### Actions
- Upsert: `PUT /api/v1/projects/{project_id}/budgets/{category_id}?month=YYYYMM`

---

## 8) /members (สมาชิก + โปรเจค)
### On enter
1) `GET /api/v1/me`
2) `GET /api/v1/projects`
3) ถ้ามี project → `GET /api/v1/projects/{project_id}/members`

### Actions
- Create project: `POST /api/v1/projects`
- Join project: `POST /api/v1/projects/join`
- Switch project: `POST /api/v1/projects/{project_id}/switch`
- Invite: `POST /api/v1/projects/{project_id}/members/invite`

---

## 9) /settings (ตั้งค่า) ⭐️ (NEW/Updated)
> รวม: ภาษา/ธีม/ความเป็นส่วนตัว + **Insight Consent (Mode B)**

### On enter
1) `GET /api/v1/me`
2) `GET /api/v1/projects/{project_id}/settings`  ✅ NEW

### UI sections
- Insight Sharing
  - Toggle: “อนุญาต AI วิเคราะห์แบบปลอดภัย (minimal)” (เปิดตลอดได้)
  - Toggle: “อนุญาตส่ง ‘รายละเอียด/โน้ต’ เพื่อวิเคราะห์” (owner/admin เท่านั้น)
  - Slider/Select: “จำกัดช่วงเวลา” (max_range_days)
  - Slider/Select: “จำกัดจำนวนรายการ” (max_rows)

### Actions
- Update settings: `PATCH /api/v1/projects/{project_id}/settings` ✅ NEW
  - body: `{ insight_share_level, allow_note_share, insight_max_rows, insight_max_range_days }`

> Guard:
- ถ้า role ไม่ใช่ owner/admin → disable controls และแสดงข้อความ “ให้เจ้าของโปรเจคตั้งค่า”

---

## 10) /insights (AI Insights) ⭐️ (NEW)
> หน้าเว็บสำหรับดู insight ที่เคยสรุปไว้ (ถ้าเปิดใช้ `/api/v1/bot/insights/save`)

### On enter
1) `GET /api/v1/me`
2) `GET /api/v1/projects/{project_id}/insights?from=...&to=...&page=1&page_size=20` *(แนะนำเพิ่ม endpoint นี้)*

### Actions
- เปิดอ่าน insight:
  - `GET /api/v1/projects/{project_id}/insights/{insight_id}` *(optional)*
- ลบ insight (optional):
  - `DELETE /api/v1/projects/{project_id}/insights/{insight_id}`

> หมายเหตุ:
- ถ้ายังไม่ทำ endpoint insights ฝั่งเว็บ สามารถยุบเป็น “แสดงใน LINE เท่านั้น” ได้

---

## 11) /profile (โปรไฟล์)
### On enter
- `GET /api/v1/me`

### Actions
- Logout: `POST /auth/logout`

---

## 12) Botpress Routes (ไม่ใช่ UI) — เพื่อความชัดเจน
> UI ไม่เรียก แต่ระบบรวมมีอยู่

- `POST /api/v1/bot/context/resolve`
- `POST /api/v1/bot/transactions/create`
- `POST /api/v1/bot/transactions/update-last`
- `POST /api/v1/bot/transactions/delete-last`
- `POST /api/v1/bot/insights/export`
- `POST /api/v1/bot/insights/save`

---

## 13) Endpoint Checklist (หน้า → endpoints)
- /login → `/auth/line/login`, `/auth/line/callback`
- /app → `/api/v1/me`, `/api/v1/projects`, `/categories`
- /ledger → `/transactions`, `/reports/summary`, (optional) `/reports/budget-vs-actual`
- /recurring → `/recurring`, (optional) `/recurring/run-due`
- /reports → `/reports/budget-vs-actual`, `/reports/by-category`, (optional) `/reports/trend`
- /categories → `/categories`, `/reports/by-category`
- /budget → `/budgets`, `/reports/budget-vs-actual`
- /members → `/projects`, `/members`, `/members/invite`, `/projects/join`, `/projects/{id}/switch`
- /settings ✅ → `/projects/{id}/settings` (GET/PATCH)
- /insights ✅ → `/projects/{id}/insights` (ถ้าทำ)
- /profile → `/api/v1/me`, `/auth/logout`

---

## 14) Performance Notes
- Cache categories per project
- reports/by-category ใช้แทนการ sum จาก transactions
- settings เรียกเฉพาะเข้า /settings (ไม่ต้องทุกหน้า)

---
```
