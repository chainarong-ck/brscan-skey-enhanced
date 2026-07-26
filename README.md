# Brother brscan-skey Enhanced

โปรแกรมเสริมสำหรับจัดการปุ่ม Scan to File, Scan to Image และ Scan to
Email ของเครื่องสแกน Brother บน Linux โดย override การทำงานผ่านไฟล์ของ
ผู้ใช้ และไม่แก้ไขไฟล์ใด ๆ ภายในไดรเวอร์ Brother

## รูปแบบการติดตั้ง

ตัวโปรแกรม Python ถูกติดตั้งส่วนกลาง ทำให้ผู้ใช้ทุกคนเรียก
`brscan-skey-config` ได้ สคริปต์สแกนที่ผู้ใช้ไม่ต้องแก้ไขจะมีเพียงชุดเดียว:

```text
<prefix>/lib/brscan-skey-enhanced/
├── configurator/
├── script/
│   ├── scan-common.sh
│   ├── brother-scan-to-file.sh
│   ├── brother-scan-to-email.sh
│   └── brother-scan-to-image.sh
├── scantofile.config
├── scantoemail.config
└── scantoimage.config
```

เมื่อใช้แพ็กเกจ DEB/RPM ค่า `<prefix>` คือ `/usr` ส่วน `install.sh`
ใช้ `/usr/local`

ใน home ของผู้ใช้แต่ละคนจะเก็บเฉพาะค่าและไฟล์ที่ใช้เปิด override:

```text
~/.brscan-skey/                    # เมื่อเปิดส่วนเสริม
├── settings.ini
├── scantofile.config
├── scantoemail.config
└── scantoimage.config
```

`settings.ini` เป็นค่าของผู้ใช้แต่ละคนและจะไม่ถูกเขียนทับเมื่ออัปเดต
โปรแกรม ส่วนไฟล์ `.config` เป็นไฟล์ที่โปรแกรมจัดการให้และจะถูกอัปเดตจาก
รุ่นที่ติดตั้งทุกครั้งที่เปิด configurator ไฟล์เหล่านี้เรียกสคริปต์
ส่วนกลาง แต่สคริปต์ยังใช้ `$HOME` ของผู้ใช้ที่เรียกจึงอ่านค่ากับบันทึก
ผลลัพธ์แยกกันตามผู้ใช้

ไฟล์ส่วนกลางจะอยู่ใน `<prefix>/lib/brscan-skey-enhanced` และมี launcher
อยู่ใน `<prefix>/bin` โปรแกรมไม่คัดลอกหรือแก้ไฟล์ใน
`/opt/brother/scanner/brscan-skey/` ไม่ว่าจะติดตั้งด้วยวิธีใด

## ความสามารถ

- บันทึกเอกสารที่สแกนเป็น PDF หรือ JPEG เมื่อมี ImageMagick
- บันทึกเป็น TIFF โดยอัตโนมัติเมื่อไม่มี ImageMagick
- รองรับกระจกสแกนและ ADF แบบสองหน้า
- ตั้งค่าความละเอียดและขนาดกระดาษแยกตามปุ่มได้
- เปิดหรือปิด override ทั้งหมดได้จากสวิตช์เดียวใน GUI
- มีหน้าต่างตั้งค่า GTK 3 และ Qt 6
- เก็บ TIFF ต้นฉบับไว้หากการแปลงไฟล์ไม่สำเร็จ
- บันทึกผลลัพธ์ไว้ใน `~/brscan`

## สิ่งที่ต้องมี

- Linux และ Python 3.9 ขึ้นไป
- ไดรเวอร์เครื่องสแกน Brother พร้อม `brscan-skey`
- GUI อย่างใดอย่างหนึ่ง:
  - GTK 3 พร้อม PyGObject (แนะนำ) หรือ
  - PySide6/PyQt6
- ImageMagick ที่มีคำสั่ง `magick` (ImageMagick 7) หรือ `convert`
  (ImageMagick 6) เป็นส่วนเสริมสำหรับแปลง TIFF เป็น PDF/JPEG
- `xdg-open` และ `xdg-email` เป็นส่วนเสริม

สำหรับ Debian/Ubuntu สามารถติดตั้ง GTK frontend และเครื่องมือที่จำเป็นได้
ด้วย:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 imagemagick xdg-utils
```

ชื่อแพ็กเกจอาจต่างกันตาม Linux distribution โปรแกรมจะเลือก `magick`
ก่อนและ fallback ไปใช้ `convert` บนระบบที่ยังเป็น ImageMagick 6

## ติดตั้งด้วยแพ็กเกจ DEB

ใช้กับ Debian และ Ubuntu โดยสร้างแพ็กเกจแบบ architecture-independent:

```bash
sudo apt install dpkg-dev
./packaging/build-deb.sh
sudo apt install ./dist/brscan-skey-enhanced_1.0.0-1_all.deb
```

`apt` จะติดตั้ง GTK 3 frontend และ dependency ที่จำเป็นตาม metadata
ของแพ็กเกจให้ ส่วน ImageMagick และ `xdg-utils` เป็น recommended packages

## ติดตั้งด้วยแพ็กเกจ RPM

ใช้กับ Fedora และ AlmaLinux:

```bash
sudo dnf install rpm-build
./packaging/build-rpm.sh
sudo dnf install ./dist/brscan-skey-enhanced-1.0.0-1*.noarch.rpm
```

สคริปต์จะสร้างทั้ง binary RPM แบบ `noarch` และ source RPM ใน `dist/`
แพ็กเกจ DEB/RPM ใช้ GTK 3 เป็น frontend เริ่มต้น แต่ยังเรียก
`brscan-skey-config --qt` ได้เมื่อติดตั้ง PySide6 หรือ PyQt6 เพิ่มเอง

เวอร์ชันแพ็กเกจอ่านจากไฟล์ `VERSION` ทั้งสองรูปแบบจึงใช้หมายเลขรุ่นเดียวกัน

> ไม่แนะนำให้ติดตั้งด้วยแพ็กเกจพร้อมกับ `install.sh` เนื่องจาก
> `/usr/local/bin` มาก่อน `/usr/bin` ใน `$PATH` โดยทั่วไป หากเคยใช้
> `install.sh` ให้รัน `sudo ./uninstall.sh` ก่อนติดตั้ง DEB/RPM

## ติดตั้งด้วย install.sh

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
ของผู้ใช้นั้นโดยอัตโนมัติ การติดตั้งซ้ำจะแทนที่เฉพาะโฟลเดอร์โปรแกรม
ส่วนกลาง เพื่อไม่ให้ไฟล์ที่เลิกใช้แล้วค้างอยู่

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

### เปิดหรือปิดการทำงานของส่วนเสริม

สวิตช์ **Use enhanced scan actions** ด้านบนของหน้าต่างควบคุม override
ทั้งสามปุ่มพร้อมกัน และมีผลทันทีโดยไม่ต้องกด Save:

- **ON** ใช้ Scan to File, Image และ Email ของโปรแกรมนี้
- **OFF** ปิด override ทั้งหมดและกลับไปใช้การทำงานเดิมของไดรเวอร์ Brother

เมื่อปิด โปรแกรมจะนำไฟล์ `.config` ที่จัดการเองทั้งสามไฟล์ออกจาก
`~/.brscan-skey` ทำให้ Brother กลับไปใช้ค่าเดิมของไดรเวอร์ ส่วน
`settings.ini` และสคริปต์ส่วนกลางจะยังอยู่ จึงเปิดกลับเมื่อใดก็ได้โดย
ค่าโปรไฟล์เดิมไม่หาย ขณะที่สวิตช์เป็น **OFF** รายละเอียดของแต่ละ
โปรไฟล์และปุ่มคืนค่าเริ่มต้นจะถูกปิดไว้เพื่อป้องกันการแก้ไขโดยไม่ตั้งใจ

สถานะเปิด/ปิดเป็นค่าของผู้ใช้แต่ละคนและเก็บใน `[general]` ของ
`~/.brscan-skey/settings.ini` ค่าเริ่มต้นหลังเปิด configurator ครั้งแรกคือ
เปิดใช้งาน หากบริการ `brscan-skey` ที่กำลังทำงานยังใช้ค่าเดิม ให้ปิดและ
เริ่ม `brscan-skey` ใหม่หนึ่งครั้ง

แต่ละโปรไฟล์รองรับ:

- ความละเอียด 100, 150, 200, 300, 400, 600 หรือ 1200 DPI
- ขนาดกระดาษ A3, A4, A5, A6, Letter หรือ Legal
- การสแกนสองหน้าผ่าน ADF

รายการข้างต้นเป็นตัวเลือกกลางที่ไดรเวอร์ `brscan-skey` รองรับ
ความละเอียด ขนาดกระดาษ และ Duplex ที่ใช้งานได้จริงขึ้นอยู่กับรุ่น
เครื่องสแกน

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
พร้อมแนบ PDF ให้อัตโนมัติ หากไม่มี `xdg-email` ไฟล์ PDF จะยังถูกเก็บไว้
ใน `~/brscan` โฟลเดอร์และไฟล์สแกนที่โปรแกรมสร้างจะอนุญาตให้เฉพาะ
ผู้ใช้เจ้าของบัญชีเข้าถึง

หากไม่มี ImageMagick โปรแกรมจะเก็บ TIFF โดยไม่ถือว่าเป็นข้อผิดพลาด
และโปรไฟล์ Email จะแนบ TIFF แทน PDF สำหรับ Scan to Image แบบหลายหน้า
โปรแกรมจะสร้าง JPEG แยกตามหน้าโดยเติม `-0`, `-1`, ... ต่อท้ายชื่อไฟล์

ดู log ล่าสุดได้ด้วย:

```bash
journalctl -t brscan-skey
```

## อัปเดต

สำหรับ DEB ให้อัปเกรดด้วยไฟล์แพ็กเกจรุ่นใหม่:

```bash
sudo apt install ./dist/brscan-skey-enhanced_<version>_all.deb
```

สำหรับ RPM:

```bash
sudo dnf upgrade ./dist/brscan-skey-enhanced-<version>.noarch.rpm
```

หากติดตั้งด้วย `install.sh` ให้ดึง source รุ่นใหม่แล้วรันตัวติดตั้งซ้ำ:

```bash
git pull
sudo ./install.sh
```

`settings.ini` เดิมของผู้ใช้จะยังอยู่ ส่วนไฟล์ override จะอัปเดตจาก
โปรแกรมส่วนกลางเมื่อผู้ใช้เปิด configurator

## ถอนการติดตั้ง

แนะนำให้ผู้ใช้แต่ละคนปิดสวิตช์ **Use enhanced scan actions** ก่อน
ถอนการติดตั้ง ตัวถอนการติดตั้งจะไม่ไล่แก้ไฟล์ใน home ของผู้ใช้ แต่หากมี
ไฟล์ override ค้างอยู่ ไฟล์นั้นจะตรวจพบว่าสคริปต์ส่วนกลางถูกลบแล้ว
ลบตัวเอง และปล่อยให้ไดรเวอร์ Brother กลับไปใช้การทำงานเดิม

```bash
sudo apt remove brscan-skey-enhanced     # เมื่อติดตั้งด้วย DEB
sudo dnf remove brscan-skey-enhanced     # เมื่อติดตั้งด้วย RPM
sudo ./uninstall.sh                      # เมื่อติดตั้งด้วย install.sh
```

ตัวถอนการติดตั้งจะลบเฉพาะโปรแกรมส่วนกลาง และเก็บ
`~/.brscan-skey/settings.ini` รวมถึงไฟล์ของผู้ใช้ไว้เพื่อป้องกันข้อมูลสูญหาย

## สัญญาอนุญาต

เผยแพร่ภายใต้ MIT License ดูรายละเอียดในไฟล์ `LICENSE`

## ตรวจสอบ source

รันชุดทดสอบก่อนเผยแพร่หรือหลังแก้ไข:

```bash
python3 -m unittest discover -s tests -v
bash -n install.sh uninstall.sh bin/* script/*.sh packaging/*.sh *.config
./packaging/build-deb.sh
./packaging/build-rpm.sh
```
