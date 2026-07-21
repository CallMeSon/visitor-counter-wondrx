# Design System

Gaya visual: portfolio/personal brand yang hangat, bold, dan editorial. Kombinasi background krem lembut dengan aksen warna berani (lime dan ungu) serta tipografi besar yang tegas.

## 1. Warna (Color Palette)

### Base
| Nama | Hex | Penggunaan |
|---|---|---|
| Cream Background | `#FBF8F3` | Warna dasar utama halaman |
| White | `#FFFFFF` | Card, panel, area kontras terang |
| Near Black | `#020002` | Teks utama, headline, ikon gelap |

### Aksen
| Nama | Hex | Penggunaan |
|---|---|---|
| Lime Accent | `##FF7200` | Highlight, badge, elemen dekoratif utama |
| Deep Purple | `##017187` | Aksen sekunder, gradient, elemen dekoratif |
| Warm Orange Blob | `##F59121` (ke arah oranye) | Gradient blob dekoratif di hero |

Catatan: palet ini cenderung earthy dan playful, bukan gaya dark mode neon. Kontras utama datang dari teks hitam pekat di atas krem, ditambah aksen lime yang mencolok sebagai penanda perhatian (Call to Action, highlight, dot indicator).

## 2. Tipografi

- Headline: sans-serif tebal (bold/black weight), ukuran sangat besar, tight letter-spacing, sering multi-baris untuk statement utama.
- Body text: sans-serif regular, ukuran sedang, warna abu gelap ke hitam, line-height longgar untuk keterbacaan.
- Skala:
  - H1: 56-96px, bold, warna Near Black
  - H2: 32-48px, bold
  - Body: 16-18px, regular
  - Label/Badge text: 12-14px, medium, uppercase atau sentence case

## 3. Layout & Spacing

- Container lebar dengan padding horizontal besar (generous whitespace).
- Section dipisahkan dengan jarak vertikal besar (80-120px antar section).
- Grid untuk kartu fitur/layanan: 2-3 kolom di desktop, 1 kolom di mobile.
- Navbar berbentuk pill (rounded full), mengambang di atas konten, dengan background putih atau krem sedikit lebih terang dari body.

## 4. Komponen

### Badge/Tag
- Bentuk pill (rounded full).
- Berisi dot kecil (bulat, warna lime atau hijau) di sisi kiri.
- Contoh isi teks: "Available for freelance".
- Background putih dengan border tipis, kontras terhadap background krem.

### Button
- Primary: rounded full (pill shape), background gelap (near black atau deep green/olive), teks putih.
- Bisa disertai ikon panah kecil di sisi kanan.
- Secondary/outline: border tipis, background transparan atau putih.

### Card
- Rounded corner besar (16-24px radius).
- Background putih di atas base krem untuk menciptakan layer/kontras lembut.
- Shadow halus, tidak terlalu tebal.
- Bisa memuat ikon di kotak kecil bersudut membulat sebagai elemen visual utama kartu.

### Dekorasi
- Blob gradient organik (bentuk tidak beraturan, blur) sebagai elemen dekoratif di sudut section, terutama hero.
- Warna blob: oranye hangat, ungu, atau kombinasi gradient lembut.
- Ikon bintang (star) kecil digunakan sebagai aksen dekoratif dekat headline.

## 5. Nada Visual (Design Personality)

- Hangat, personal, approachable (bukan korporat kaku).
- Bold namun tetap clean, karena banyak whitespace.
- Kontras tinggi antara teks hitam pekat dan background krem lembut membuat headline terasa kuat tanpa perlu warna gelap penuh (dark mode).
- Aksen lime dan ungu dipakai secukupnya sebagai penanda visual (badge, highlight, ilustrasi), bukan dominan di seluruh halaman.

## 6. Contoh Token CSS

```css
:root {
  --color-bg: #FBF8F3;
  --color-surface: #FFFFFF;
  --color-text: #020002;
  --color-accent-lime: #C8DC3C;
  --color-accent-purple: #5B4B8A;
  --color-accent-orange: #FBD08E;

  --radius-pill: 999px;
  --radius-card: 20px;

  --font-heading: "Inter", "Helvetica Neue", sans-serif;
  --font-body: "Inter", sans-serif;

  --spacing-section: 96px;
}
```