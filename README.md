# Persyaratan untuk menjalankan Dot & Boxes kami:
- Python (minimal versi 3.14)
- Microsoft Visual Studio Code
- Komputer/laptop atau Virtual Machine
--
# Cara untuk menjalankan aplikasi:
- Buka aplikasi Microsoft Visual Studio Code
- Klik "File" yang ada di layar bagian kiri atas disamping logo visual studio code.
- lalu klik "Open File..." dan cari lokasi file kami "dab_prototype.py"
- Setelah load, klik tombol play ("▶" segitiga menunjuk ke kanan) pada layar bagian kanan atas. Mohon dipencet sekali saja supaya tidak ada antrian pada aplikasi kami.
- Setelak klik, Tunggu sampai tertampil sebuah pop up frame dengan judul "Dots and Boxes" dan tombol "Easy (3x3)" "Hard (4x4)" dll.
--
# Cara bermain Dot & Boxes kami:
## Basis
- Klik tombol "Easy (3x3)" atau "Hard (4x4)" untuk bermain.
	- Easy (3x3) = Game Dot & Boxes dengan 4 kotak (2x2 kotak)
	- Hard (4x4) = Game Dot & Boxes dengan 9 kotak (3x3 kotak)
- Pemain(anda) selalu memulai giliran pertama sebelum AI.
Pemain(anda) = hijau, AI = merah.
- Klik pada garis di antara dua titik untuk menggambarkan garis
	- Jika Anda berhasil menutup satu kotak (membuat keempat sisinya), kotak tersebut akan berwarna sesuai pemain (hijau untuk Anda, merah untuk AI), dan Anda mendapat giliran lagi.
	- Jika kotak tidak tertutup, giliran berpindah ke AI.
- Permainan berakhir ketika semua garis sudah terisi. Pemenang ditentukan dari jumlah kotak terbanyak yang berhasil dimiliki oleh masing-masing pemain.
## Timer
- Timer adalah mode di mana terdapat batas waktu pada permainan Dot & Boxes. Jika waktu habis, permainan akan berhenti secara otomatis. Pemenang ditentukan berdasarkan jumlah kotak yang telah dikumpulkan hingga waktu berakhir.
- Untuk memulaikan mode Timer, Pada "[0]min [0]sec", ubahkan angka 0 menjadi angka apapun untuk memulakian mode timer.

# Jika tidak memiliki persyaratan, untuk mendapatkan file persyaratannya:
## Python
- buka website https://www.python.org/downloads
- klik kata yang sesuai dengan OS pada computer/laptop anda "Looking for Python with a different OS? Python for Windows, Linux/Unix, macOS, Android, other"
  Misal: jika OS computer/laptop anda tipe macOS, klik kata "macOS"
- Lihat di baris bagian "Stable Releases" lalu klik "Download ________"
	"________" berarti tulisan biru yang digaris Bawah kuning, tulisan pada "______" ini tergantung tipe OS anda:
	- Jika Windows, ada yang tertulis "Windows installer (64-bit)" dan lain-lain.
	- Jika macOS, tertulis "macOS 64-bit universal2 installer"
	- Jika Linux, tertulis "Gzipped source tarball" dan ada yang "XZ compressed source tarball"

## Visual Studio Code
- buka website https://code.visualstudio.com/Download
- Klik tombol biru download sesuai gambaran diatas dan tertulis tipe OS dibawah
