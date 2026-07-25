# Brother brscan-skey Enhanced

โปรแกรมเสริมสำหรับจัดการปุ่ม Scan to File, Scan to Image และ Scan to
Email ของเครื่องสแกน Brother บน Linux โดย override การทำงานผ่านไฟล์ของ
ผู้ใช้ และไม่แก้ไขไฟล์ใด ๆ ภายในไดรเวอร์ Brother

## รูปแบบการติดตั้ง

ตัวโปรแกรม Python ถูกติดตั้งส่วนกลาง ทำให้ผู้ใช้ทุกคนเรียก
`brscan-skey-config` ได้ ส่วนไฟล์ต่อไปนี้จะแยกเก็บใน home ของผู้ใช้แต่ละคน:

```text
~/.brscan-skey/
├── settings.ini
├── scantofile.config
├── scantoemail.config
├── scantoimage.config
└── script/
    ├── load-scan-settings.sh
    ├── brother-scan-to-file.sh
    ├── brother-scan-to-email.sh
    └── brother-scan-to-image.sh
```

`settings.ini` เป็นค่าของผู้ใช้แต่ละคนและจะไม่ถูกเขียนทับเมื่ออัปเดต
โปรแกรม ส่วนไฟล์ `.config` และไฟล์ใน `script/` เป็นไฟล์ที่โปรแกรมจัดการ
ให้และจะถูกอัปเดตจากรุ่นที่ติดตั้งทุกครั้งที่เปิด configurator

ไฟล์ส่วนกลางจะอยู่ที่ `/usr/local/lib/brscan-skey-enhanced` โดยปริยาย
และมี launcher อยู่ใน `/usr/local/bin` โปรแกรมไม่คัดลอกหรือแก้ไฟล์ใน
`/opt/brother/scanner/brscan-skey/`

## ความสามารถ

- บันทึกเอกสารที่สแกนเป็น PDF หรือ JPEG
- รองรับกระจกสแกนและ ADF แบบสองหน้า
- ตั้งค่าความละเอียดและขนาดกระดาษแยกตามปุ่มได้
- มีหน้าต่างตั้งค่า GTK 3 และ Qt 6
- เก็บ TIFF ต้นฉบับไว้หากการแปลงไฟล์ไม่สำเร็จ
- บันทึกผลลัพธ์ไว้ใน `~/brscan`

## สิ่งที่ต้องมี

- Linux และ Python 3
- ไดรเวอร์เครื่องสแกน Brother พร้อม `brscan-skey`
- ImageMagick ที่มีคำสั่ง `magick`
- GUI อย่างใดอย่างหนึ่ง:
  - GTK 3 พร้อม PyGObject (แนะนำ) หรือ
  - PySide6/PyQt6
- `xdg-open` และ `xdg-email` เป็นส่วนเสริม

สำหรับ Debian/Ubuntu สามารถติดตั้ง GTK frontend และเครื่องมือที่จำเป็นได้
ด้วย:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 imagemagick xdg-utils
```

ชื่อแพ็กเกจอาจต่างกันตาม Linux distribution และ ImageMagick บางรุ่นเก่า
อาจยังไม่มีคำสั่ง `magick`

## ติดตั้ง

โคลน repository แล้วรันตัวติดตั้ง:

```bash
git clone https://github.com/chainarong-ck/brscan-skey-enhanced.git
cd brscan-skey-enhanced
sudo ./install.sh
```

ระหว่างติดตั้ง โปรแกรมจะถามว่า frontend เริ่มต้นเป็น GTK 3 หรือ Qt 6
ค่านี้จะใช้เมื่อคลิก **Brother Scan Settings** จากเมนู หรือเรียก
`brscan-skey-config` โดยไม่ระบุ option กด Enter เพื่อเลือก GTK ซึ่งเป็น
ค่าแนะนำ:

```text
Choose the default GUI for Brother Scan Settings:
  1) GTK 3 (recommended)
  2) Qt 6
Selection [1]:
```

สำหรับการติดตั้งแบบอัตโนมัติหรือไม่ต้องการให้แสดงคำถาม ให้ระบุโดยตรง:

```bash
sudo ./install.sh --gui gtk
sudo ./install.sh --gui qt
```

ตัวติดตั้งจะติดตั้งเฉพาะโปรแกรมส่วนกลางลงใน `/usr/local` และจะไม่สร้าง
หรือแก้ไขไฟล์ใน home ของผู้ใช้ เมื่อผู้ใช้แต่ละคนเปิด configurator
ครั้งแรก โปรแกรมจึงจะสร้าง `~/.brscan-skey` และ `settings.ini`
ของผู้ใช้นั้นโดยอัตโนมัติ

## ตั้งค่าของผู้ใช้

เปิดจากเมนูแอปพลิเคชันชื่อ **Brother Scan Settings** หรือเรียก:

```bash
brscan-skey-config
```

สามารถบังคับ frontend สำหรับการเปิดครั้งใดครั้งหนึ่งได้ด้วย:

```bash
brscan-skey-config --gtk
brscan-skey-config --qt
```

เมื่อไม่ระบุ `--gtk` หรือ `--qt` โปรแกรมจะใช้ค่าที่เลือกไว้ตอนติดตั้ง
ส่วน option ทั้งสองใช้ override เฉพาะการเปิดครั้งนั้นและไม่เปลี่ยน
ค่าเริ่มต้น

ค่าที่บันทึกจะอยู่ที่ `~/.brscan-skey/settings.ini` ของผู้ใช้ที่เปิด
โปรแกรมเท่านั้น จึงใช้โปรแกรมส่วนกลางร่วมกันได้โดยไม่ใช้ค่าปะปนกัน

แต่ละโปรไฟล์รองรับ:

- ความละเอียด 100, 150, 200, 300 หรือ 600 DPI
- ขนาดกระดาษ A4, A5, Letter หรือ Legal
- การสแกนสองหน้าผ่าน ADF

## ใช้งาน

เริ่มบริการปุ่มสแกน Brother ใน session ของผู้ใช้:

```bash
brscan-skey
```

ตรวจสอบว่าเครื่องสแกนลงทะเบียนอยู่:

```bash
brscan-skey -l
```

เมื่อกด File, Image หรือ Email บนเครื่องสแกน ผลลัพธ์จะอยู่ใน:

```text
~/brscan
```

โปรไฟล์ Email จะสร้าง PDF แล้วเปิดหน้าต่างเขียนอีเมลผ่าน `xdg-email`
หากมีติดตั้งไว้ ปัจจุบันจะแสดงตำแหน่งไฟล์ในเนื้อหาอีเมล แต่ไม่แนบไฟล์
ให้อัตโนมัติ

ดู log ล่าสุดได้ด้วย:

```bash
journalctl -t brscan-skey
```

## อัปเดต

ดึง source รุ่นใหม่แล้วรันตัวติดตั้งซ้ำ:

```bash
git pull
sudo ./install.sh
```

`settings.ini` เดิมของผู้ใช้จะยังอยู่ ส่วนไฟล์ override คงที่จะอัปเดตเมื่อ
ผู้ใช้เปิด configurator

## ถอนการติดตั้ง

```bash
sudo ./uninstall.sh
```

ตัวถอนการติดตั้งจะลบเฉพาะโปรแกรมส่วนกลาง และเก็บ
`~/.brscan-skey/settings.ini` รวมถึงไฟล์ของผู้ใช้ไว้เพื่อป้องกันข้อมูลสูญหาย
