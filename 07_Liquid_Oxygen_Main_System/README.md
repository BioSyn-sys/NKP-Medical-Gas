# 🏥 NKP Medical Oxygen Telemetry & Analytics Dashboard

[![GitHub Pages Deployment](https://img.shields.io/badge/GitHub%20Pages-Live%20Demo-06b6d4?style=for-the-badge&logo=github)](https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/)
[![Build Status](https://img.shields.io/badge/Build-Passing-10b981?style=for-the-badge)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](https://opensource.org/licenses/MIT)

ยินดีต้อนรับสู่ระบบบริหารจัดการและแดชบอร์ดติดตามการใช้ออกซิเจนทางการแพทย์ (Medical Oxygen System Analytics) ของ **โรงพยาบาลนครพิงค์** และ **ศูนย์มะเร็งขอนตาล** ออกแบบให้สามารถทำงานและโฮสต์บน **GitHub Pages** ได้ทันทีโดยไม่ต้องใช้ Server Backend!

---

## 🌟 จุดเด่นและฟีเจอร์หลัก (Key Features)

1. **Executive Dual-Mode View Switcher (การแสดงผล 2 โหมดสำหรับผู้บริหาร):**
   * 📊 **โหมดที่ 1: ปริมาณการใช้งานจริงรายวัน (Daily Telemetry - 91 วัน)** สลับเลือกหน่วยระหว่าง **ปริมาตร ($m^3$)** และ **น้ำหนัก (Kg)** ได้
   * 🗓️ **โหมดที่ 2: สถิติสะสมรายเดือน (Monthly History - 31 เดือน)** ก.ย. 2566 – มี.ค. 2569
   * 🛡️ **โหมดที่ 3: แผนก๊าซสำรอง & SOP Zero Failure** สรุปสถานีจ่ายสำรอง 8 จุด (162 ท่อ)
2. **Live Excel Import & Drag-Drop Module (SheetJS Engine):**
   * ลากไฟล์ Excel โทรมาตร (`NPPH10011-History-*.xlsx` หรือ `NPPH20011-History-*.xlsx`) วางบนเบราว์เซอร์ เพื่อคำนวณและอัปเดตกราฟแบบ Real-time
3. **100% Client-Side Engine for GitHub Pages:**
   * ใช้ HTML5, Vanilla CSS Glassmorphic Design, Chart.js, SheetJS CDN ทำงานรวดเร็วบน GitHub Pages

---

## 🚀 วิธีนำขึ้น GitHub Pages (Deployment Guide)

1. **สร้าง Repository บน GitHub:**
   * ไปที่ GitHub.com -> คลิก **New Repository** -> ตั้งชื่อเช่น `medical-oxygen-nkp`
2. **อัปโหลดไฟล์ในไดเรกทอรีนี้:**
   * `index.html` (หน้าเว็บหลัก)
   * `README.md` (เอกสารกำกับโปรเจกต์)
   * `.nojekyll` (ไฟล์ป้องกันการบล็อกไบนารีของ GitHub Pages)
3. **เปิดใช้งาน GitHub Pages:**
   * ไปที่ **Settings** -> **Pages**
   * ในส่วน **Branch** เลือก `main` หรือ `master` และโฟลเดอร์ `/ (root)`
   * กด **Save** ระบบจะสร้าง URL สำหรับเข้าใช้งานทันที (เช่น `https://username.github.io/medical-oxygen-nkp/`)

---
*พัฒนาโดย กลุ่มงานวิศวกรรมความปลอดภัยและระบบก๊าซทางการแพทย์ โรงพยาบาลนครพิงค์*
