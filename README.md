# Brother brscan-skey Tools

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
- ไดรเวอร์เครื่องสแกนและ `brscan-skey` จาก Brother
- Python 3
- ImageMagick (`magick`)
- ไลบรารีสำหรับหน้าต่างตั้งค่าอย่างใดอย่างหนึ่ง:
  - GTK 3 พร้อม PyGObject หรือ
  - PySide6/PyQt6
- `xdg-open` และ `xdg-email` เป็นส่วนเสริม จะไม่มีหรือติดตั้งไว้ก็ได้

ชื่อแพ็กเกจอาจแตกต่างกันในแต่ละ Linux distribution สำหรับ Debian หรือ
Ubuntu หน้าต่าง GTK มักต้องใช้แพ็กเกจ `python3-gi` และ
`gir1.2-gtk-3.0`

## การติดตั้ง

โคลน repository ไปยัง `~/.brscan-skey`:

```bash
git clone https://github.com/chainarong-ck/brscan-skey-enhanced.git \
  "$HOME/.brscan-skey"
```

กำหนดให้สคริปต์สแกนสามารถเรียกใช้งานได้:

```bash
chmod +x "$HOME/.brscan-skey/script/"*.sh
```

สำรองไฟล์ตั้งค่าปุ่มสแกนเดิมของ Brother ก่อน จากนั้นคัดลอกหรือสร้างลิงก์
ของไฟล์ต่อไปนี้ไว้ในไดเรกทอรีสคริปต์ของ `brscan-skey`:

- `scantofile.config`
- `scantoimage.config`
- `scantoemail.config`

โดยทั่วไปไดเรกทอรีที่ Brother ใช้จะอยู่ที่:

```text
/opt/brother/scanner/brscan-skey/script/
```

ตำแหน่งจริงอาจแตกต่างกันตามรุ่นของไดรเวอร์และ Linux distribution
หลังแก้ไขไฟล์ตั้งค่าแล้วให้เริ่ม `brscan-skey` ใหม่

## การตั้งค่าโปรไฟล์สแกน

เรียกใช้หน้าต่างตั้งค่าแบบใดแบบหนึ่งจากภายในไดเรกทอรีของ repository

GTK 3:

```bash
python3 -m configurator.gtk_gui
```

Qt 6:

```bash
python3 -m configurator.qt_gui
```

แต่ละโปรไฟล์รองรับการตั้งค่าดังนี้:

- ความละเอียด: 100, 150, 200, 300 หรือ 600 DPI
- ขนาดกระดาษ: A4, A5, Letter หรือ Legal
- การสแกนสองหน้าผ่าน ADF

โปรแกรมจะบันทึกค่าประจำเครื่องไว้ใน `settings.ini` หากยังไม่มีไฟล์นี้
โปรแกรมจะใช้ค่าเริ่มต้นที่กำหนดไว้ภายใน

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
