# Zira: sunum metni (Türkçe, canlı platformun 15 Kasım 2026 durumuna göre)

Bu dosya, 7 slaytlık sunumun ve formül sayfasının Türkçe metnidir. Her durum etiketi (CANLI,
PROTOTİP, PLANLI) projenin gerçek durumunu yansıtır; etiketi değiştirmeden önce platformda
doğrulayın.

## Önce okuyun: ilk metne göre ne değişti

| Konu | İlk metin | Şimdi |
| --- | --- | --- |
| Tarla Hafızası | Prototip | **Canlı platformda**: MODIS NDVI, tarla poligonunun içinden, 10 sezon |
| Su Kasası | Platformda "planlı" | **Canlı** |
| Rotasyon ve Zira Kartı | Platformda "planlı" | **Canlı** (A/B/C, aralıklı, yazdırılabilir) |
| WhatsApp | "Kart WhatsApp ile gider" (elle) | **Canlı**: mühendis onayı bekleyen taslak kuyruğu, Green API ile gönderim |
| Veri Merkezi | Yalnızca POWER | POWER ve MODIS bağlı; diğerleri açıkça "bağlı değil" |
| Sezon sayısı | 25 | Platformda **24 tam sezon** (2001–2025 kaydında 2025 sezonu henüz bitmiyor) |
| Strateji A | Tarla Hafızası'ndan | Canlı: doğrulanmış geçmiş ya da ekrandan seçilen rotasyon |
| Ürün aşama süreleri | "Onay bekliyor" | **Geçici başlangıç değerleri** (FAO-56 Tablo 11), kartta "geçici" yazar |
| Prototipte kalanlar | Hepsi | SMAP / MERRA-2 doğrulaması, GRACE, GLDAS, VIIRS, FAO-33 verim kuralı, çift Kc, 6 koşuluk aralık |

**Sunumdan önce doldurulacaklar:** takım adı, depo bağlantısı, kullanılan yapay zekâ araçlarının
adları, prototip bağlantısı. Depo şu an **özel**; "açık kaynak" yazacaksanız teslimden önce
herkese açık yapılmalı ve özel `@soloft/uds` bağımlılığı çözülmeli (karar 0005).

---

## SLAYT 1 / 7 · KAPAK

**NASA SPACE APPS CHALLENGE 2026 · FIELD SHIFT: ADAPTING FARMS WITH NASA DATA**

# Zira

**Bu tarlanın suyu hangi rotasyonu taşır?**

Zira, ekim kararı gününde bir tarlanın toprağının tutabildiği kullanılabilir suyu gösterir ve üç
rotasyonu 24 sezonluk NASA verisiyle karşılaştırır. Çalışan bir platformdur.

[Takım adı] · Canlı platform: **zira.soloftindustries.com**

**Konuşmacı notları**

Zira, kıraç tarım arazileri için bir karar destek aracıdır. Ziraat mühendisleri ve kooperatifler
için yapıldı; çiftçi sonucu kısa, sade bir kart olarak WhatsApp'tan alır. Zira karar vermez;
ziraat mühendisinin ve çiftçinin kararını destekler. Platform şu an canlıdır: giriş yapıp tarla
çizebilir, 25 yıllık NASA verisini çekebilir, tarlanın ekili ya da nadas geçmişini uydudan okuyabilir,
kullanılabilir suyu görebilir ve üç rotasyonu karşılaştırabilirsiniz.

---

## SLAYT 2 / 7 · SORUN

# Sorun: takvime göre planlanan tarım, suya göre değil

| | |
| --- | --- |
| **740+** | Konya Kapalı Havzası'nda kayıtlı obruk |
| **3,4 cm** | Yılda kaybedilen yeraltı suyu depolaması (GRACE tabanlı bir çalışmaya göre) |
| **245–534 mm** | Demo konumunda 25 sezonun en kurağından en yağışlısına sezonluk yağış |

- Yağış daha az öngörülebilir, su daha kıt, toprak sağlığı geriliyor.
- Bir yerde toprağı iyileştiren ürün, başka bir yerde fazla su tüketebilir.
- Çiftçinin elinde, bir rotasyonu ötekiyle tarlaya özgü biçimde tartabileceği sade bir araç yok.

**Takvime bağlı bir rotasyon, 245 mm'lik sezonda da 534 mm'lik sezonda da aynı şekilde ekilir.**

Kaynaklar: Konya Teknik Üniversitesi Obruk Araştırma Merkezi (NTV/İHA, 17 Ağustos 2026) ·
Khorrami, Arık ve Gündüz 2021 · NASA POWER

**Konuşmacı notları**

İlk hedefimiz Konya Kapalı Havzası'nın yarı kurak karasal iklimi ve kuru tarım. Araştırmacılar
yeraltı suyundaki düşüşü sulama için yapılan yoğun pompajla ilişkilendiriyor, obrukların
yayılmasını da buna bağlıyor. Buna rağmen yaygın rotasyon sabit: bir yıl buğday, bir yıl nadas.
NASA GRACE ve GRACE-FO verisini geniş bölge (yaklaşık 300 km) için kendimiz okuduğumuzda toplam su
depolaması 2002–2022 arasında yılda 0,46 cm azalıyor. Bu rakam geniş bir alandaki bütün suyun
toplamıdır; 3,4 cm ise çalışmanın havza içindeki yeraltı suyu için tahminidir. İki rakam farklı
şeyleri ölçer, birbirinin yerine konmamalı. **245–534 mm** değeri demo konumuna aittir ve NASA
POWER'ın 25 sezonluk yağış kaydından gelir.

---

## SLAYT 3 / 7 · ÇÖZÜM

# Çözüm: tek soru, üç modül

> "Ekim kararı gününde toprak kaç milimetre kullanılabilir su tutuyor ve bu suyla üç rotasyon nasıl
> davranıyor?"

| MODÜL 1 · Tarla Hafızası | MODÜL 2 · Su Kasası | MODÜL 3 · Zira Kartı |
| --- | --- | --- |
| Tarla son on sezonun hangisinde ekiliydi, hangisinde nadas? Uydu bitki örtüsü verisinden okunur, kullanıcı ya da ziraat mühendisi doğrular. **CANLI** | Karar gününde kök bölgesindeki kullanılabilir su, milimetre olarak, belirsizlik aralığıyla. **CANLI** | Her rotasyon için: 24 sezonun kaçında su yetti, neden, hangi kanıtla, neyin yerelde incelenmesi gerekiyor. **CANLI** |

**ALTI EKRAN + MESAJLAR** · Genel Bakış · Tarlalar · Tarla Hafızası · Su Kasası · Rotasyon ve Zira
Kartı · Veri Merkezi · **WhatsApp Mesajları** (mühendis onay kuyruğu)

**KURAL:** Zira karar vermez; ziraat mühendisinin ve çiftçinin kararını destekler.

**Konuşmacı notları**

Üç rotasyon aynı tarlada, aynı hava, aynı toprak ve aynı başlangıç suyuyla karşılaştırılır. Yalnızca
rotasyon değişir. **A, mevcut rotasyon:** Tarla Hafızası'nda doğrulanan sıra, örneğin buğday sonra
nadas. **B, suya bağlı esnek rotasyon:** ancak karar gününde Su Kasası eşiğin (kapasitenin yarısı)
üstündeyse eker; değilse nadas bırakır. **C, baklagilli rotasyon:** nadas yıllarının her ikincisinde baklagil
(platformda geçici olarak mercimek; nohut için FAO-56 Tablo 11'de aşama süreleri yok). Kartın her
strateji bloğunda aynı beş alan vardır: neden önerildiği, dayandığı veri, beklenen fayda, bilgi
boşluğu ve yerelde incelenmesi gereken risk. Bir ürün, ziraat mühendisi onaylayana kadar kesin
öneri olarak gösterilmez.

**Mesaj akışı (canlı):** Zira, tarlanın suyunda bir olay olunca modelin o günkü sayılarıyla kısa
bir mesaj taslağı yazar. Taslak ziraat mühendisinin kuyruğunda bekler; mühendis düzenler, onaylar ya
da reddeder. **Onaylanmadan hiçbir mesaj çiftçiye gitmez.** Onaylanan mesaj Green API üzerinden
çiftçinin WhatsApp'ına düşer. Mesaj türleri: ekim kararı günü, bir günde 20 mm ve üzeri yağış,
kök altına 5 mm ve üzeri su inmesi (yıkanma uyarısı), hassas dönemde 5. ve 15. stres günü, hasatta
sezon özeti ve tarla kartı. Her mesajın altında "Zira karar vermez" satırı bulunur.

**Tasarım kararı: tek demo, çok tarlalı mimari.** Tek motor her tarla için çalışır; tarlalar
arasında değişen her şey Tarla Profili'nde durur, kodda değil. Çiftçinin eklediği, uydunun göremediği
kısıtlar (su, ekipman, pazar) ve öncelik sıralaması bir sonraki sürümde girdi olacak.

---

## SLAYT 4 / 7 · NASA VERİSİ

# NASA verisi: her kaynağın tek bir görevi var, kendi ölçeğinde

| Kaynak | Zira'daki görevi | Ölçek | Durum |
| --- | --- | --- | --- |
| **NASA POWER** | Günlük hava: yağış, sıcaklık, nem, rüzgâr, radyasyon, basınç | yaklaşık 50 km, günlük | **CANLI** · 2001–2025, tarla başına 9.131 gün |
| **MODIS MOD13Q1 / MYD13Q1** | Bitki örtüsü geçmişi: ekili mi nadas mı | 250 m, 16 günlük (Terra + Aqua ile yaklaşık 8 günde bir) | **CANLI** · tarla poligonunun içinden, 10 sezon, yaklaşık 450 görüntü |
| Landsat 8/9 | Poligon içindeki bitki örtüsü deseni | 30 m | **PLANLI** · Earth Engine projesi gerekiyor (prototipte yalnızca görüntü) |
| GPM IMERG | İkinci yağış kaynağı, çapraz kontrol | yaklaşık 10 km, günlük | PROTOTİP · POWER üzerinden |
| SMAP | Bölgesel toprak nemi kontrolü | 9 km | PROTOTİP · kök bölgesi, 2015'ten beri |
| GRACE / GRACE-FO | Havza su depolama eğilimi | yaklaşık 300 km, aylık | PROTOTİP · 2002–2022 |

**CANLI** = barındırılan platformda çalışıyor · **PROTOTİP** = tarayıcı prototipinde, tek demo
konumunda · **PLANLI** = tanımlı, henüz yapılmadı. Veri Merkezi hangi kaynağın gerçekten bağlı
olduğunu gösterir; bağlı olmayan bir kaynak asla sağlıklı gösterilmez.

**Konuşmacı notları**

Kendimize koyduğumuz ölçek kuralları: POWER bölgesel yeniden analizdir, tarlanın ölçümü değildir.
SMAP 9 km'lik hücrenin ortalamasıdır, tek bir tarlanın ürün geçmişini göremez. GRACE geniş bir
alandaki toplam su depolamasıdır, hiçbir zaman bir parselin altındaki yeraltı suyu değildir. Aynı
GPM pikseline düşen tarlalar ayrı yağış gözlemi değildir. İki yağış kaynağı asla toplanmaz: biri
girdi, öteki çapraz kontroldür.

**MODIS nasıl bağlandı:** Earth Engine projemiz henüz yok. Bu yüzden MODIS NDVI'ı, NASA'nın MOD13Q1
(Terra) ve MYD13Q1 (Aqua) sürüm 061 ürünlerinden, Microsoft Planetary Computer'ın herkese açık STAC
kataloğundaki bulut için optimize GeoTIFF'lerden okuyoruz; hesap ya da anahtar gerekmiyor. Her
görüntü için tarla poligonunun içindeki pikselleri alıyor, piksel güvenilirliği "iyi" ya da "sınırda"
olanları tutuyor, bulut, kar ve eksik pikselleri dışarıda bırakıp sayıyoruz. Bir MODIS pikseli yaklaşık
6 hektardır; küçük parsellerde komşu pikseller sinyale karışır. Bu yüzden Landsat (30 m) hâlâ
hedefimiz ve Earth Engine ile bağlanacak.

**Prototip, platformda olmayanlar:** SMAP, GRACE, GLDAS ve VIIRS, NASA GIBS önizleme görüntülerinden
GIBS'in yayımladığı renk haritalarıyla okunuyor, çünkü bilimsel dosyalar Earthdata girişi
istiyor. Bu bir eğilim kontrolü için yeterlidir, bilim düzeyinde veri çıkarımı değildir.
Prototipte VIIRS, kapsadığı iki baharda MODIS ile uyuşuyor; GLDAS toprak nemi üçüncü bağımsız
kontrol; SRTM rakım ve eğim veriyor. Platformda rakım şimdilik POWER yanıtından geliyor.

NASA'nın Global Imagery Browse Services (GIBS), Earth Science Data and Information System (ESDIS)
parçası olarak sunduğu görüntüleri kullandığımızı belirtiriz. Hava verisi NASA Langley Araştırma
Merkezi (LaRC) POWER Projesi'nden alınmıştır; proje NASA Earth Science/Applied Science Program
tarafından finanse edilmektedir.

---

## SLAYT 5 / 7 · NASIL ÇALIŞIYOR

# Nasıl çalışıyor: günlük FAO-56 su dengesi

| Adım | Formül |
| --- | --- |
| **Atmosferin su talebi** | ET₀ = [ 0,408 Δ (Rn − G) + γ · 900 / (T + 273) · u₂ (eₛ − eₐ) ] / [ Δ + γ (1 + 0,34 u₂) ] |
| **Bitki su ihtiyacı** | ETc = Kc × ET₀ |
| **Toprak kapasitesi** | TAW = 1000 (θFC − θWP) Zr ; RAW = p × TAW |
| **Günlük denge** | S(t) = min( TAW, max( 0, S(t−1) + Peff + I − ETa − R − D ) ) |
| **Su stresi** | ETa = Ks × Kc × ET₀ ; Ks = 1 (S ≥ (1 − p) TAW), değilse S / ((1 − p) TAW) |
| **Karar** | Bir sezon, Σ ETa ÷ Σ ETc ≥ 0,70 ise "su yetti" sayılır |

| TARLA HAFIZASI (canlı) | ÜÇ ROTASYON, AYNI BAŞLANGIÇ (canlı) | KODA GÖMÜLÜ DEĞİL |
| --- | --- | --- |
| NDVI = (NIR − Kırmızı) / (NIR + Kırmızı). Sezonun (1 Mart – 30 Eylül) en yüksek NDVI'ı 0,40 ve üzeriyse **ekili**, altındaysa **nadas**; yeterli temiz görüntü yoksa **bilinmiyor**. Kullanıcı ya da ziraat mühendisi doğrular. | A, doğrulanmış sırayı tekrarlar. B, yalnızca 1 Ekim'de S ≥ 0,50 × TAW ise eker. C, nadas sezonlarının her ikincisinde baklagil eker. | Model değerleri parametre tablosundan okunur. Buradaki her eşik, ziraat mühendisi onayını bekleyen bir başlangıç değeridir. |

**Konuşmacı notları**

Semboller. ET₀: FAO-56 Penman–Monteith denklemiyle referans evapotranspirasyon (mm/gün). Δ: buhar
basıncı eğrisinin eğimi. Rn: net radyasyon. G: toprak ısı akısı, günlük adımda sıfır. γ: psikrometrik
sabit. T: ortalama hava sıcaklığı (°C). u₂: 2 m'deki rüzgâr hızı. eₛ − eₐ: buhar basıncı açığı. Kc:
bitki katsayısı. TAW: kök bölgesindeki toplam kullanılabilir su (mm). θFC ve θWP: tarla kapasitesi ve
solma noktası. Zr: kök derinliği (m). p: bitkinin stres başlamadan kullanabildiği TAW payı. S: kök
bölgesi deposu. Peff: etkili yağış. I: kök bölgesine ulaşan sulama. R: yüzey akışı. D: derine sızma.
Ks: stres katsayısı.

Kc eğrisinin dört evresi var: başlangıç değerinde sabit, doğrusal artış, sezon ortası değerinde
sabit, doğrusal azalış. Kışlık buğday için FAO-56 başlangıç değerleri: donan toprakta 0,4, sezon
ortasında 1,15, sonda 0,25–0,4. Nadasta bitki yoktur; yağışın sabit bir payı (0,25) toprakta kalır.
Üç rotasyon da bir ısınma sezonundan sonra aynı depodan başlar.

**Belirsizlik:** her sonuç üç kez hesaplanır; toprağın metre başına kullanılabilir suyunun düşük, orta
ve yüksek değeriyle, yağış payı da 0,10 aynı yönde kaydırılarak. Kart orta sonucu, düşükten yükseğe
aralıkla gösterir. Sensör yoksa aralık geniş kalır.

**Platformdaki gerçek değerler ve onay durumu.** Bu slayttaki varsayılanlar (0,70, 0,50, karar günü
1 Ekim, etkili yağış payı 0,80, nadas verimi 0,25) tasarım değerleridir ve ziraat mühendisi onayını
bekler. Ayrıca şu başlangıç değerleri **geçici**dir ve kartta "geçici" uyarısıyla görünür: kışlık
buğday için aşama süreleri 30/140/40/30 gün (FAO-56 Tablo 11, Akdeniz, Kasım ekimi), mercimek için
25/35/70/40, ekim tarihi 1 Kasım, sulama verimi 0,75, NDVI ekili eşiği 0,40. Konya, tablodaki
Akdeniz satırından daha soğuktur; gerçek süreleri ziraat mühendisi girecektir.

---

## SLAYT 6 / 7 · BUGÜN NE ÇALIŞIYOR

# Bugün ne çalışıyor: iki parça, tek plan

| CANLI · PLATFORM (zira.soloftindustries.com) | PROTOTİP · ANALİZ MOTORUNUN DERİN DOĞRULAMASI |
| --- | --- |
| Rol tabanlı giriş: yönetici, ziraat mühendisi, kooperatif kullanıcısı | Tarayıcıda, tek demo konumu (Kulu, Konya) |
| Haritada tarla sınırı çizilir; alan ve merkez otomatik hesaplanır | Tarla Hafızası: 2016–2026 sezonları ekili ve nadas arasında temiz biçimde değişiyor |
| Tek tıkla 25 yıllık NASA POWER verisi, yağış grafiği ve yıllık özet | Su Kasası: 12 Kasım 2026'da 144 mm kapasitenin 13 mm'si |
| **Tarla Hafızası:** tarla poligonunun içinden MODIS NDVI, 10 sezon, ekili / nadas kararı, güven düzeyi, kullanıcı doğrulaması | Su 13 ekimin 6'sında A için, 10'un 5'inde B için, 21'in 3'ünde C için yetti |
| **Su Kasası:** karar günü kullanılabilir su, aralıkla, günlük depo ve ET₀ grafikleri | NASA SMAP ve MERRA-2 toprak nemiyle karşılaştırıldı (r = 0,61); 21 otomatik test |
| **Rotasyon ve Zira Kartı:** A, B, C yan yana, 24 sezon, aralık, yazdırılabilir; A, doğrulanmış geçmişten alınabilir | FAO-33 verim kuralı, çift Kc, iki katmanlı toprak kovası |
| **WhatsApp:** olaylardan yazılan taslaklar, mühendis onay kuyruğu, Green API ile gönderim | |
| **Veri Merkezi:** POWER ve MODIS bağlı, diğerleri "bağlı değil" | |
| HTTPS, FastAPI, PostGIS, Celery, Next.js; 203 backend ve 38 frontend testi geçiyor | |

**PLANLI:** prototipin kanıtlarını platforma taşımak (SMAP / MERRA-2 çapraz kontrolü, FAO-33 verim kuralı)
→ Landsat (Earth Engine) → gerçek bir tarla → sensörler ve kooperatif paneli

**Platformun mevcut demo tarlası üzerindeki sayılar (aynı kod, geçici değerlerle):** 1 Ekim 2025'te
kullanılabilir su 202 mm (aralık 154–249; kapasite 279 mm, tınlı toprak, kışlık buğday). Su, A için 12
ekimin 6'sında (aralık 1–9), B için 7 ekimin 6'sında (aralık 1–8), C için 18 ekimin 11'inde (aralık 5–13)
yetti. Bu sayılar prototipin sayılarından farklıdır: konum, toprak ve kurallar farklıdır.

**Konuşmacı notları**

Platform ürün iskeletini ve analizin tamamını kanıtlıyor: gerçek kullanıcılar, gerçek tarla
poligonları, tarih, birim ve kaynağıyla saklanan gerçek NASA verisi; bu verilerden tarlanın geçmişini
çıkarma, suyu sayma, üç rotasyonu karşılaştırma ve kartı yazma, Türkçe ve İngilizce. Prototip ise
bilimi tek konumda daha derin doğruluyor: Kulu yakınlarında, net bir ekili-nadas sinyali için seçilmiş
tek bir 250 m MODIS pikseli. Bu bir tarama yapılmış tarla değildir; sınır, ürün ve çeşit hâlâ bir
çiftçiden gelmelidir.

Prototipin sayıları kendi kural setini kullanır ve platform belirtiminden ayrıntıda farklıdır. Bir
ekimi, FAO-33 göreli verimi 1 − Ky (1 − Ta/Tp) en az %50 ise yeterli sayar. B, 15 Ekim'de kasada en az
60 mm varsa buğday eker; art arda iki yıldan fazla değil. C, ekim tarihinde kasada en az 40 mm varsa
baklagil eker. Aralıkları A için 1–9, B için 3–10, C için 2–7'dir ve altı koşudan çıkar: iki yağış
kaynağı çarpı üç toprak kapasitesi. Motoru platforma taşımak, bu kuralları önce bir ziraat mühendisiyle
netleştirmeyi gerektirir.

Prototip kendini ekranda eleştirir: altı ekili yılın en zayıf bahar yeşermesi 2022'deydi, oysa su
modeli en düşük verimi 2024'e veriyor. Platformun gerçek MODIS verisi üzerinde de bir kontrol var:
her sezon için tepe NDVI ve temiz görüntü sayısı tabloda görünür, düşük güvenli sezonlar işaretlenir ve
bilinmeyenler kullanıcıya bırakılır.

**Mesaj taslağı örneği (canlı):** "Ekim kararı, 1 Eki 2025. Toprakta 95 mm kullanılabilir su var
(kapasite 279 mm); bu, 140 mm eşiğinin altında. Alışılmış rotasyonunuzda bu yıl kışlık buğday var, ama
esnek kurala göre tarla nadasa bırakılır. Ekmeden önce ziraat mühendisinizle konuşun. Zira karar
vermez; ziraat mühendisinin ve çiftçinin kararını destekler." Gönderim, Green API hesabındaki
WhatsApp numarası eşleştirildiğinde etkinleşir. **[Sunumdan önce eşleştirmeyi doğrulayın; çalışmıyorsa
"gönderim hazır, eşleştirme bekliyor" deyin.]**

---

## SLAYT 7 / 7 · ETKİ, SINIRLAR, SONRAKİ ADIM

# Etki, sınırlar ve sonraki adım

| ETKİ | SINIRLAR | SONRAKİ |
| --- | --- | --- |
| Çiftçinin okuyabileceği, tarla düzeyinde bir karşılaştırma, ücretsiz NASA verisiyle | NASA POWER yaklaşık 50 km'lik bölgesel veridir, tarlanın ölçümü değildir | Bir kooperatiften gerçek bir tarla |
| Denge görünür: daha çok ekim, daha çok hasat ve daha çok karşılanmayan su demek | MODIS pikseli yaklaşık 6 ha; ekili ile nadası ayırır, ürün türünü ve kış–yaz ayrımını bilmez | Her kural için ziraat mühendisi onayı; NDVI eşiğinin yerel tarlalarla kalibrasyonu |
| Mühendis onayı olmadan hiçbir mesaj çiftçiye gitmez | Gerçek tarla, toprak analizi ve ziraat mühendisi incelemesi henüz yok; aşama süreleri geçici | Landsat 30 m (Earth Engine); prototipteki SMAP / MERRA-2 çapraz kontrolünün platforma taşınması |
| Çiftçi önceliği ve kısıtları girdi olacak | Belirsizlik her zaman gösterilir; yerel doğrulama ziraat mühendisinindir | Aynı havzada iki tarla daha; referans toprak nemi probları, sensör verisiyle Su Kasası düzeltmesi; kooperatif paneli ve çiftçi görünümü |

**Zira karar vermez: çiftçinin delille karar vermesine yardım eder.**

Açık kaynak: [depo bağlantısı] · Yapay zekâ kullanımı: [kod, arayüz metinleri, mesaj taslağı
metinleri ve bu slaytlar yapay zekâ asistanıyla hazırlandı ve ekip tarafından gözden geçirildi; araçların
adlarını yazın] · Yapay zekâ ile üretilmiş görsel yok.

**Konuşmacı notları**

Doğrulama dört aşamada ilerler: tek bir koordinatta boru hattı testi; tek bir gerçek tarla poligonunda
üç rotasyonun özdeş koşullarda ana demosu; aynı havzada iki farklı tarla; ancak ondan sonra yerel
kalibrasyonla başka bir iklim bölgesi. Eşikler ve bitki katsayıları yeni bir bölgeye asla kopyalanmaz.

Sensör donanımı tasarlandı, yapılmadı: 10, 30, 60 ve 100 cm'de toprak nemi probları, tarla başına
üç dört düğüm, güneş panelli LoRaWAN ya da LTE-M, her toprak türü için gravimetrik kalibrasyon. Bir
düğüm 48 saat susarsa tarla uydu moduna döner ve aralık genişler. Tarlalar ham sayılar üzerinden
birbirleriyle asla sıralanmaz; her tarla kendi mevcut rotasyonuna göre ve veri güveniyle birlikte
raporlanır.

**Şeffaflık notu (canlı platform).** Bu sürümde bilerek geçici bırakılanlar: ürün aşama süreleri, ekim
tarihi, sulama verimi, baklagil seçimi (mercimek) ve NDVI eşiği. Hepsi `config/rotation_demo.yaml`
dosyasında kaynağıyla yazılıdır, kartta "geçici" etiketi taşır ve ziraat mühendisinin onayını bekler.
Strateji B'nin yalnızca A'nın ekili yıllarında karar verdiği ve karar günü ile eşiğin örneklerdeki
15 Ekim ve 60 mm'den farklı olduğu da açık noktalar olarak kayıtlıdır (karar 0012).

---

## FORMÜL SAYFASI (slayt değil)

**Kaynak:** 1–5. bölümler Allen, Pereira, Raes ve Smith (1998), *Crop evapotranspiration*, FAO
Irrigation and Drainage Paper 56. 6–8. bölümler, varsayılanları ziraat mühendisi onayını bekleyen Zira
tasarım kurallarıdır. ET₀, Kc eğrisi, TAW/RAW ve stres hesabı platformda FAO-56'nın basılı örnekleriyle test edilmiştir
(Örnek 18: Uccle, 6 Temmuz, ET₀ = 3,88 mm/gün).

### 1. Günlük girdiler

Doygun buhar basıncı: e°(T) = 0,6108 · exp( 17,27 T / (T + 237,3) ) [kPa, T °C]
eₛ = ( e°(Tmaks) + e°(Tmin) ) / 2 ; eₐ = (BNortalama / 100) · eₛ
z yüksekliğindeki rüzgârdan 2 m'deki rüzgâr: u₂ = u_z · 4,87 / ln( 67,8 z − 5,42 ); z = 10 m için
u₂ ≈ 0,748 · u₁₀
BNmin = 100 · eₐ / e°(Tmaks)

### 2. Referans evapotranspirasyon

ET₀ = [ 0,408 Δ (Rₙ − G) + γ · 900 / (T + 273) · u₂ (eₛ − eₐ) ] / [ Δ + γ (1 + 0,34 u₂) ]
Δ = 4098 · e°(T) / (T + 237,3)² ; γ = 0,000665 · P ; günlük adımda G = 0
Rₙ = 0,77 Rₛ − Rₙₗ
Rₙₗ = σ · ( Tmaks,K⁴ + Tmin,K⁴ ) / 2 · ( 0,34 − 0,14 √eₐ ) · ( 1,35 Rₛ / Rₛₒ − 0,35 )
Rₛₒ = ( 0,75 + 2 × 10⁻⁵ z ) · Rₐ
T günlük ortalama (°C), P basınç (kPa), Rₛ güneş radyasyonu (MJ m⁻² gün⁻¹), z rakım (m),
σ = 4,903 × 10⁻⁹ MJ K⁻⁴ m⁻² gün⁻¹; Rₐ, enlem ve yılın gününden hesaplanan atmosfer dışı radyasyondur.

### 3. Bitki evapotranspirasyonu

ETc = Kc × ET₀, dört evreli Kc eğrisiyle (evre süreleri l_ini, l_dev, l_mid, l_late).
Sezon ortası değerin iklim düzeltmesi: Kc,mid = Kc,mid(Tablo) + [ 0,04 (u₂ − 2) − 0,004 (BNmin − 45) ] · (h / 3)^0,3
(Platformun şimdiki sürümü tablo değerini kullanır, bu düzeltmeyi uygulamaz.)

FAO-56 başlangıç değerleri (Tablo 12 ve 22):

| Ürün | Kc başlangıç | Kc orta | Kc son | Kök derinliği (m) | p |
| --- | --- | --- | --- | --- | --- |
| Kışlık buğday | 0,4 donan toprak; 0,7 donmayan | 1,15 | 0,25–0,4 | 1,5–1,8 | 0,55 |
| Arpa | 0,3 | 1,15 | 0,25 | 1,0–1,5 | 0,55 |
| Nohut | 0,4 | 1,00 | 0,35 | 0,6–1,0 | 0,50 |
| Mercimek | 0,4 | 1,10 | 0,30 | 0,6–0,8 | 0,50 |

Platformdaki **geçici** aşama süreleri (gün, FAO-56 Tablo 11): kışlık buğday 30 / 140 / 40 / 30
(Akdeniz, Kasım); mercimek 25 / 35 / 70 / 40 (kurak bölge, Ekim–Kasım). Nohut için Tablo 11'de satır yoktur.

### 4. Toprağın su kapasitesi

TAW = 1000 (θFC − θWP) Zr ; RAW = p · TAW
p = p(Tablo) + 0,04 (5 − ETc), 0,1 ile 0,8 arasında tutulur
Dokuya göre kullanılabilir su (FAO-56 Tablo 19): kumlu tın 110–150 mm/m, tın 130–180 mm/m, siltli tın
130–190 mm/m, kil 120–200 mm/m. Orta değer varsayılandır; sınırlar belirsizlik koşularını sürer.

### 5. Günlük su dengesi ve stres

Sₜ = min( TAW, max( 0, Sₜ₋₁ + Peff + I − ETa − R − D ) )
ETa = Ks · Kc · ET₀
S ≥ (1 − p) · TAW iken Ks = 1; değilse Ks = S / ( (1 − p) · TAW )
Peff = 0,80 × P (varsayılan); I = uygulanan sulama × sulama verimi; D, o gün TAW'ı aşan miktardır;
nadasta depo, günlük 0,25 × P kazanır ve TAW'ı geçemez (varsayılan).

### 6. Sezonlar, karar ve ölçütler

Bir sezon ekim ile hasat arasında sürer, Ocak–Aralık arasında değil. Platformda 2001–2025 kaydı
**24 tam sezona** bölünür (Kasım'da ekilen bir kışlık sezon ertesi yıl biter, 2025 ekimi kayıtla
tamamlanamaz). Bir sezon yalnızca günlerinin en az %95'inde tam veri varsa sayılır.

Su yeterli sezon: Σ ETa ÷ Σ ETc ≥ 0,70.
Kritik dönemde stres günü: sezon ortası evresinde Ks < 1 olan günler.
Sezonluk su açığı (mm): Σ (ETc − ETa).
Sulama ihtiyacı (mm): sezonluk açık ÷ sulama verimi (ilk yaklaşım; verim 0,75, geçici).
Mevcut rotasyondan fark: B ve C'nin her ölçütü eksi A'nın aynı ölçütü.

### 7. Strateji kuralları ve belirsizlik

A: doğrulanmış ya da seçilen sıra, 24 sezon boyunca tekrarlanır.
B: karar gününde (kışlık ürünler için 1 Ekim) S ≥ 0,50 × TAW ise planlanan ürünü eker; değilse nadas.
C: A gibi, ama nadas sezonlarının her ikincisine baklagil (platformda geçici olarak mercimek) ekilir.
Üçü de bir ısınma sezonundan sonra 0,50 × TAW'dan başlar; ısınma simüle edilir, sayılmaz.
Belirsizlik: toprağın metre başına kullanılabilir suyunun düşük, orta ve yüksek değeriyle üç koşu;
etkili yağış payı ve nadas verimi 0,10 aynı yönde kaydırılır.

### 8. Uydu işleme

**MODIS (canlı).** MOD13Q1 ve MYD13Q1 sürüm 061, NDVI = 0,0001 × DN. Her görüntüde tarla
poligonunun içindeki pikseller alınır (poligona değen pikseller dahil); piksel güvenilirliği 0 (iyi) ya
da 1 (sınırda) olanlar tutulur, 2 (kar) ve 3 (bulut) ile eksik değerler dışarıda kalır. Her görüntü
için ortalama ve ortanca NDVI, temiz piksel sayısı ve dışarıda kalan pay saklanır.
Sezon = hasat yılının 1 Mart – 30 Eylül penceresi. En yüksek NDVI ≥ 0,40 ise **ekili**, değilse
**nadas**; temiz görüntü 5'ten azsa **bilinmiyor**.
Güven = min(1, |tepe NDVI − 0,40| / 0,20) × min(1, temiz görüntü sayısı / 13).
Eşik (0,40) geçicidir ve bilinen geçmişli yerel tarlalarla kalibre edilmelidir.

**Landsat (planlı).** Collection 2 yüzey yansıması: SR = DN × 0,0000275 − 0,2.
NDVI = (NIR − Kırmızı) / (NIR + Kırmızı); Landsat 8/9 için NIR = SR_B5, Kırmızı = SR_B4.
Bulut ve gölge pikselleri QA_PIXEL ile maskelenir; istatistikler tarla poligonunun içinden alınır.

### 9. Tarayıcı prototipinin kuralları (farklı olduğu yerler)

Çift bitki katsayısı (FAO-56), iki katmanlı toprak kovası ve açık toprak buharlaşması.
Yeterli ekim: göreli verim 1 − Ky (1 − Ta / Tp) ≥ %50 (Doorenbos ve Kassam, 1979, FAO Irrigation and
Drainage Paper 33).
B, 15 Ekim'de kasada en az 60 mm varsa buğday eker, art arda iki yıldan fazla değil; C, ekim tarihinde
kasada en az 40 mm varsa baklagil eker.
Altı koşudan aralıklar: iki yağış kaynağı (MERRA-2 düzeltilmiş yağış, GPM IMERG) × üç toprak su kapasitesi.

### Kaynakça

Allen, R. G., Pereira, L. S., Raes, D., Smith, M. (1998). Crop evapotranspiration: guidelines for computing
crop water requirements. FAO Irrigation and Drainage Paper 56.
Doorenbos, J., Kassam, A. H. (1979). Yield response to water. FAO Irrigation and Drainage Paper 33.
Khorrami, B., Arık, F., Gündüz, O. (2021). Land deformation and sinkhole occurrence in response to the
fluctuations of groundwater storage. GIScience & Remote Sensing 58(8), 1518–1542.
https://doi.org/10.1080/15481603.2021.2000349
NTV / İHA (17 Ağustos 2026). Konya Ovası'nda alarm. Sayı 740'ı aştı.
https://www.ntv.com.tr/yerel-haberler/galerikonya-ovasinda-alarm-sayi-740i-asti-1737722
NASA Langley Research Center, POWER Project, Daily API v2. https://power.larc.nasa.gov/
NASA MODIS MOD13Q1 / MYD13Q1 Version 061 (LP DAAC), Microsoft Planetary Computer açık STAC kataloğu
üzerinden. https://planetarycomputer.microsoft.com/
NASA GIBS, NASA ESDIS'in parçası. Tam veri seti listesi ve atıflar için README'ye bakın.

---

## Sunumdan önce kontrol listesi

1. **Gösterilecek tarla:** Prototipin Kulu konumunu platforma tarla olarak ekleyin ve NDVI'ı çekin. Şu anki
   test tarlasının (Konya, 32,505 / 37,905) gerçek MODIS NDVI'ı yıl boyu 0,15–0,26: on sezonun hepsi
   "nadas" çıkıyor, ekili–nadas değişimini göstermez. Prototip Kulu pikselinde net bir değişim
   gösteriyor; bunu platformda henüz denemedim, sunumdan önce deneyin.
2. **Green API:** QR eşleştirmesi tamamlandı mı? Sunucuda durum "notAuthorized" idi; eşleştirmeden
   önce slayt 3 ve 6'daki "gönderim" cümlesini "hazır, eşleştirme bekliyor" olarak söyleyin.
3. **Depo bağlantısı ve "açık kaynak":** depo özel; herkese açık yapılacaksa karar 0005'i ve özel UDS
   bağımlılığını çözün, yapılmayacaksa slayt 7'deki "Açık kaynak" ibaresini kaldırın.
4. **Sayı tutarlılığı:** "24 sezon" platformdaki, "25 sezon" prototipin ve başlıktaki söylemin sayısıdır;
   konuşurken hangisinden söz ettiğinizi belirtin.
5. **Boşlukları doldurun:** takım adı, prototip bağlantısı, kullanılan yapay zekâ araçlarının adları.
