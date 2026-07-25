# Brother brscan-skey Enhanced

ชุดสคริปต์ปุ่มสแกนและหน้าต่างตั้งค่าแบบ GTK/Qt สำหรับ Brother
`brscan-skey` บน Linux โดยแยกการตั้งค่าสำหรับ Scan to File, Scan to Image
และ Scan to Email

## ความสามารถ

- บันทึกเอกสารที่สแกนเป็นไฟล์ PDF หรือ JPEG
- รองรับการสแกนจากกระจกสแกนและ ADF แบบสองหน้า
- ตั้งค่าความละเอียดและขนาดกระดาษแยกตามโปรไฟล์ได้
- มีหน้าต่างตั้งค่าให้เลือกใช้ทั้ง GTK 3 และ Qt 6
- เก็บไฟล์ TIFF ต้นฉบับไว้หากการแปลงไฟล์ไม่สำเร็จ
- บันทึกผลลัพธ์ไว้ที่ `~/brscan`

## สิ่งที่ต้องมี

- Linux
- เครื่องสแกน Brother ที่รองรับ `brscan-skey`
- ไดรเวอร์เครื่องสแกนและแพ็กเกจ `brscan-skey` จาก Brother
- Python 3
- ImageMagick (`magick` หรือ `convert`)
- ไลบรารีสำหรับหน้าต่างตั้งค่าอย่างใดอย่างหนึ่ง:
  - GTK 3 พร้อม PyGObject หรือ
  - PySide6/PyQt6
- `xdg-open` และ `xdg-email` เป็นส่วนเสริม จะไม่มีหรือติดตั้งไว้ก็ได้

แพ็กเกจ DEB/RPM และ `install.sh` จะติดตั้ง dependencies แบบโอเพนซอร์ส
ให้โดยอัตโนมัติ แต่ไม่สามารถรวมไดรเวอร์ของ Brother มาให้ได้

## ติดตั้งสำหรับผู้ใช้งานทั่วไป

### 1. ติดตั้งไดรเวอร์ Brother

ดาวน์โหลด Scanner Driver และ **Scanner Setting file (`brscan-skey`)**
สำหรับเครื่องสแกนรุ่นที่ใช้งานจาก
[Brother Support](https://support.brother.com/) และติดตั้งให้เรียบร้อย

ตรวจสอบว่าเครื่องสแกนถูกพบด้วยคำสั่ง:

```bash
brscan-skey -l
```

### 2. ติดตั้ง Brother brscan-skey Enhanced

ดาวน์โหลดแพ็กเกจล่าสุดจากหน้า
[GitHub Releases](https://github.com/chainarong-ck/brscan-skey-enhanced/releases)

สำหรับ Ubuntu, Debian และ Linux Mint ให้ดาวน์โหลดไฟล์ `.deb`
แล้วดับเบิลคลิกเพื่อติดตั้ง หรือใช้คำสั่ง:

```bash
sudo apt install ./brscan-skey-enhanced_*_all.deb
```

สำหรับ Fedora ให้ดาวน์โหลดไฟล์ `.rpm` แล้วดับเบิลคลิกเพื่อติดตั้ง
หรือใช้คำสั่ง:

```bash
sudo dnf install ./brscan-skey-enhanced-*.noarch.rpm
```

ตัวติดตั้งจะสำรอง configuration เดิมของ Brother, เชื่อมปุ่ม Scan to File,
Image และ Email และเพิ่ม “Brother Scan Settings” ลงในเมนูแอปพลิเคชัน

### ติดตั้งจาก source ด้วยคำสั่งเดียว

ใช้วิธีนี้เมื่อต้องการติดตั้งเวอร์ชันล่าสุดที่ยังไม่ได้ออก Release:

```bash
git clone https://github.com/chainarong-ck/brscan-skey-enhanced.git
cd brscan-skey-enhanced
./install.sh
```

สคริปต์จะขอรหัสผ่าน `sudo` เมื่อต้องติดตั้ง dependencies และไฟล์ระบบ

ตรวจสอบความพร้อมหลังติดตั้ง:

```bash
brscan-skey-enhanced-check
```

หากติดตั้งโปรแกรมก่อนไดรเวอร์ Brother ให้เชื่อมปุ่มสแกนภายหลังด้วย:

```bash
sudo brscan-skey-enhanced-integrate install
```

## การตั้งค่าโปรไฟล์สแกน

เปิด “Brother Scan Settings” จากเมนูแอปพลิเคชัน หรือใช้คำสั่ง:

```bash
brscan-skey-settings
```

สำหรับการพัฒนาสามารถเปิด frontend โดยตรงได้เช่นกัน

```bash
python3 -m configurator.gtk_gui
python3 -m configurator.qt_gui
```

แต่ละโปรไฟล์รองรับการตั้งค่าดังนี้:

- ความละเอียด: 100, 150, 200, 300 หรือ 600 DPI
- ขนาดกระดาษ: A4, A5, Letter หรือ Legal
- การสแกนสองหน้าผ่าน ADF

โปรแกรมจะบันทึกค่าของผู้ใช้ไว้ที่
`~/.config/brscan-skey-enhanced/settings.ini` หากอัปเกรดจากเวอร์ชันเดิม
โปรแกรมยังสามารถอ่าน `settings.ini` ที่อยู่ใน repository ได้

## วิธีใช้งาน

เริ่มบริการปุ่มสแกนของ Brother:

```bash
brscan-skey
```

กด File, Image หรือ Email บนเครื่องสแกน แล้วเลือกคอมพิวเตอร์ Linux
ที่ลงทะเบียนไว้ ไฟล์ที่สแกนจะถูกบันทึกไว้ที่:

```text
~/brscan
```

โปรไฟล์ Email จะสร้างไฟล์ PDF และเปิดโปรแกรมเขียนอีเมลเริ่มต้นเมื่อมี
`xdg-email` เพื่อให้ใช้งานได้กับโปรแกรมอีเมลหลายประเภท เนื้อหาอีเมล
จะแสดงตำแหน่งไฟล์ที่บันทึกไว้ แต่จะไม่แนบไฟล์ให้อัตโนมัติ

## การแก้ปัญหา

ตรวจสอบว่าเครื่องสแกนลงทะเบียนอยู่หรือไม่:

```bash
brscan-skey -l
```

ดูข้อความล่าสุดจากสคริปต์:

```bash
journalctl -t brscan-skey
```

หากแปลงเป็น PDF หรือ JPEG ไม่สำเร็จ ไฟล์ TIFF ต้นฉบับจะยังคงอยู่ใน
`~/brscan`

## การถอนการติดตั้ง

แพ็กเกจจะคืนค่า configuration เดิมของ Brother ที่สำรองไว้โดยอัตโนมัติ:

```bash
# Ubuntu/Debian
sudo apt remove brscan-skey-enhanced

# Fedora
sudo dnf remove brscan-skey-enhanced
```

หากติดตั้งจาก source ให้ใช้:

```bash
./uninstall.sh
```

การถอนการติดตั้งจะเก็บค่าผู้ใช้ใน
`~/.config/brscan-skey-enhanced/` ไว้ เผื่อติดตั้งใหม่ภายหลัง

## การทดสอบ

รันชุดทดสอบในเครื่องได้ด้วยคำสั่ง:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
bash tests/test_scan_scripts.sh
bash tests/test_installer.sh
```

GitHub Actions จะรัน unit tests, ตรวจ shell scripts และจำลองขั้นตอนสแกน
ครบทั้ง Scan to File, Image และ Email บน Ubuntu 22.04, Ubuntu 24.04,
Debian 13 และ Fedora 43 ทุกครั้งที่ push หรือเปิด pull request

สร้างแพ็กเกจใน `dist/` ได้ด้วย:

```bash
packaging/build-packages.sh
```

GitHub Actions จะสร้าง DEB และ RPM เป็น artifacts โดยอัตโนมัติ และเมื่อ
push tag เช่น `v0.1.0` ระบบจะสร้าง GitHub Release พร้อมแนบแพ็กเกจทั้งสอง
ชนิดให้ดาวน์โหลด
