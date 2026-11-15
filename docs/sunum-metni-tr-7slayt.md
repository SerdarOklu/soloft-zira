# Zira: sunum metni (7 slayt, Türkçe)

Platformun 15 Kasım 2026 durumuna göre. 7 slayt; son slayt simülasyon videosudur. Formül sayfası, kaynakça ve ayrıntılı notlar [sunum-metni-tr.md](sunum-metni-tr.md) dosyasındadır (14 slaytlık sürüm); soru-cevapta oradan yararlanın.

Doldurulacaklar: takım adı, depo bağlantısı, yapay zekâ araçlarının adları, video dosyası.
Süre: 6 dk anlatım + 2 dk video.

---

## SLAYT 1 / 7 · KAPAK

**NASA SPACE APPS CHALLENGE 2026 · FIELD SHIFT: ADAPTING FARMS WITH NASA DATA**

# Zira
**Bu tarlanın suyu hangi rotasyonu taşır?**

Ekim kararı gününde tarlanın toprağındaki kullanılabilir suyu milimetre olarak gösterir ve üç rotasyonu 24 sezonluk NASA verisiyle karşılaştırır.

[Takım adı] · Canlı platform: zira.soloftindustries.com

**Konuşmacı notları**
Zira, kıraç tarım arazileri için bir karar destek platformudur. Ziraat mühendisleri ve kooperatifler için yapıldı; çiftçi sonucu WhatsApp'tan kısa bir mesaj olarak alır. Zira karar vermez; ziraat mühendisinin ve çiftçinin kararını destekler. Platform canlıdır: giriş yapıp tarla çizebilir, NASA verisini çekebilir, tarlanın geçmişini uydudan okuyabilir ve rotasyonları karşılaştırabilirsiniz.

---

## SLAYT 2 / 7 · SORUN

# Takvime göre planlanan tarım, suya göre değil

| | |
|---|---|
| **740+** | Konya Kapalı Havzası'nda kayıtlı obruk |
| **3,4 cm / yıl** | Yeraltı suyu depolama kaybı (GRACE tabanlı çalışma) |
| **245 – 534 mm** | Demo konumunda 25 sezonun en kurağından en yağışlısına sezonluk yağış |

Yağış daha az öngörülebilir, su daha kıt. Takvime bağlı bir rotasyon 245 mm'lik sezonda da 534 mm'lik sezonda da aynı şekilde ekilir. Çiftçinin elinde rotasyonları kendi tarlası için tartabileceği sade bir araç yok.

*Kaynaklar: Konya Teknik Üniversitesi Obruk Araştırma Merkezi (NTV/İHA, 17 Ağustos 2026) · Khorrami, Arık ve Gündüz 2021 · NASA POWER*

**Konuşmacı notları**
İlk hedefimiz Konya Kapalı Havzası'nın yarı kurak iklimi ve kuru tarım. Araştırmacılar yeraltı suyu düşüşünü yoğun pompajla, obrukların yayılmasını da bununla ilişkilendiriyor. Yaygın rotasyon ise sabit: bir yıl buğday, bir yıl nadas. GRACE verisini geniş bölge (yaklaşık 300 km) için kendimiz okuduğumuzda toplam su depolaması 2002–2022 arasında yılda 0,46 cm azalıyor; 3,4 cm ise çalışmanın havza içi yeraltı suyu tahminidir. İki rakam farklı şeyleri ölçer, birbirinin yerine konmaz. 245–534 mm demo konumunun NASA POWER kaydından gelir.

---

## SLAYT 3 / 7 · ÇÖZÜM

# Tek soru, üç modül, üç kullanıcı

> "Ekim kararı gününde toprak kaç mm kullanılabilir su tutuyor ve bu suyla üç rotasyon nasıl davranıyor?"

| 1 · Tarla Hafızası | 2 · Su Kasası | 3 · Zira Kartı |
|---|---|---|
| Son on sezonun hangisi ekili, hangisi nadas? Uydudan okunur, mühendis doğrular. | Karar gününde kullanılabilir su (mm), aralıkla; sensör varsa sensörle düzeltilir. | A, B, C rotasyonu: 24 sezonun kaçında su yetti, neden, hangi kanıtla. |

**Mühendis** doğrular ve onaylar · **Kooperatif** çiftçileri ve tarlaları yönetir · **Çiftçi** WhatsApp'tan kısa mesaj alır.
**Mühendis onayı olmadan hiçbir mesaj çiftçiye gitmez.**

**Konuşmacı notları**
Üç modül bir zincir: Tarla Hafızası rotasyon A'yı belirler, Su Kasası bugünkü suyu verir, Zira Kartı karşılaştırır. Roller sunucuda zorlanır: çiftçi başkasının tarlasını ya da mühendis ekranlarını menüden gizlenmekle değil, API'nin reddetmesiyle göremez. Tek motor her tarla için çalışır; tarlalar arasında değişen her şey Tarla Profili'nde durur, kodda değil.

---

## SLAYT 4 / 7 · NASA VERİSİ

# Her kaynağın tek bir görevi var, kendi ölçeğinde

| Kaynak | Görevi | Ölçek |
|---|---|---|
| **NASA POWER** | Günlük hava, 2001–2025 (tarla başına 9.131 gün) | ~50 km |
| **MODIS MOD13Q1 / MYD13Q1** | Tarla poligonunun içinden NDVI: 10 sezon ekili mi nadas mı (~450 görüntü) | 250 m, 16 günlük |
| **SMAP · GPM IMERG** | Toprak nemi ve yağış için bağımsız çapraz kontrol (r = 0,61) | 9 km · ~10 km |
| **GRACE / GRACE-FO** | Havza su depolama eğilimi | ~300 km, aylık |
| **Landsat 8/9** | 30 m'ye geçiş için sonraki adım | 30 m |

Veri Merkezi hangi kaynağın gerçekten bağlı olduğunu gösterir; bağlı olmayan kaynak asla sağlıklı gösterilmez.

**Konuşmacı notları**
Ölçek kuralları: POWER bölgesel yeniden analizdir, tarla ölçümü değildir. SMAP 9 km'lik ortalamadır. GRACE hiçbir zaman bir parselin altındaki yeraltı suyu değildir. İki yağış kaynağı asla toplanmaz: biri girdi, öteki çapraz kontroldür. MODIS'i Earth Engine yerine NASA MOD13Q1/MYD13Q1 sürüm 061 ürünlerinden, Microsoft Planetary Computer'ın açık STAC kataloğundan, hesap gerektirmeden okuyoruz. Bir MODIS pikseli yaklaşık 6 ha'dır; bu yüzden Landsat sonraki adımımız. Attribution: Hava verisi NASA LaRC POWER Projesi'nden alınmıştır; proje NASA Earth Science/Applied Science Program tarafından finanse edilmektedir. NASA GIBS, NASA ESDIS'in parçasıdır.

---

## SLAYT 5 / 7 · NASIL ÇALIŞIYOR

# Uydudan tarlaya: geçmiş, su, rotasyon

**Tarla Hafızası:** sezonun (1 Mart – 30 Eylül) en yüksek NDVI'ı ≥ 0,40 ise *ekili*, değilse *nadas*, yeterli temiz görüntü yoksa *bilinmiyor*. NDVI = (NIR − Kırmızı) / (NIR + Kırmızı)

**Su Kasası (günlük FAO-56):**
- ET₀ = [0,408 Δ (Rₙ − G) + γ · 900/(T + 273) · u₂ (eₛ − eₐ)] / [Δ + γ (1 + 0,34 u₂)]
- ETc = Kc × ET₀ · TAW = 1000 (θFC − θWP) Zr
- S(t) = min(TAW, max(0, S(t−1) + Peff + I − ETa − R − D)) · ETa = Ks × Kc × ET₀

**Üç rotasyon, aynı hava, aynı toprak, aynı başlangıç suyu:** A doğrulanmış geçmişi tekrarlar · B yalnızca 1 Ekim'de S ≥ 0,50 × TAW ise eker · C nadasların her ikincisinde baklagil eker. Sezon, Σ ETa ÷ Σ ETc ≥ 0,70 ise **"su yetti"**.

**Konuşmacı notları**
Kendi icat ettiğimiz bir model değil: FAO-56 standardı. ET₀, Kc, TAW/RAW ve stres hesabı FAO-56'nın basılı örnekleriyle test edildi (Örnek 18: Uccle, ET₀ = 3,88 mm/gün). Her sonuç üç kez hesaplanır (toprak kapasitesi düşük/orta/yüksek, yağış payı ±0,10) ve aralıkla gösterilir; tek sayı kesinlik izlenimi verir. Eşikler (0,70, 0,50, 1 Ekim, NDVI 0,40), ürün aşama süreleri (FAO-56 Tablo 11) ve sulama verimi ayrı yapılandırmada kaynağıyla yazılıdır, kartta "geçici" etiketi taşır, ziraat mühendisi onayıyla yerel değerlere çekilir. Sezon sayısı: 2001–2025 kaydından 24 tam sezon çıkar. Semboller ve tam formüller için formül sayfasına bakın.

---

## SLAYT 6 / 7 · SONUÇLAR VE SENSÖR

# Ne buluyoruz, ve yeri ölçünce ne değişiyor

**Platformdaki demo tarlası (1 Ekim 2025, kışlık buğday, tınlı toprak, kapasite 279 mm):** kullanılabilir su 202 mm (aralık 154–249). Su yeterli sezon: A 12'de 6, B 7'de 6, C 18'de 11.

**Kulu doğrulama çalışması (2016–2026):** ekili–nadas sezonları temiz ayrışıyor; su modeli NASA SMAP ve MERRA-2 toprak nemiyle r = 0,61 uyumlu; su A için 13 ekimin 6'sında, B için 10'un 5'inde, C için 21'in 3'ünde yetti.

**Sensör modu:** 10–100 cm'de dört derinlik, tarlaya özgü kalibrasyon, karar günü deposu modelin yerini alır, aralık daralır. Örnek senaryoda model 231 mm derken sensör **140 mm** gösterir; fark ekranda yan yana görünür. 48 saat sessizlikte tarla otomatik uydu moduna döner.

**Olaydan telefona:** ekim kararı günü, ≥ 20 mm yağış, yıkanma, stres günü, hasat özeti → taslak → **mühendis onayı** → WhatsApp. Çiftçi yalnızca gönderilmiş mesajları ve kendi tarlasını görür.

**Konuşmacı notları**
Platformun ve Kulu çalışmasının sayıları farklıdır, çünkü konum, toprak ve kurallar farklıdır; ikisini karıştırmıyoruz. Kulu, tek bir 250 m MODIS pikselinde net ekili–nadas sinyali olduğu için bilimi derinlemesine sınamak üzere seçildi, taranmış bir tarla değildir. Sistem kendini eleştirir: en zayıf bahar yeşermesi 2022'de, su modeli en düşük verimi 2024'e veriyor; düşük güvenli sezonlar ekranda işaretlenir. Sensör okumaları gerçek donanımın göndereceği şemayla çalışan simülatörden gelir ve ekranlarda "simüle" yazar; donanıma geçişte backend değişmez. Sensör bandı (±%10 TAW) ve eşikler gerçek kalibrasyonla netleşecek başlangıç değerleridir. Mesaj örneği: "Toprakta 95 mm kullanılabilir su var (kapasite 279 mm); bu 140 mm eşiğinin altında… Ekmeden önce ziraat mühendisinizle konuşun. Zira karar vermez." [Green API eşleştirmesini sunumdan önce doğrulayın; çalışmıyorsa "gönderim hazır, eşleştirme bekliyor" deyin.]

---

## SLAYT 7 / 7 · VİDEO, SINIRLAR, SONRAKİ ADIM

# Zira, uçtan uca

▶ **[Video, 2 dk]**: tarla çiz → NASA verisi → Tarla Hafızası → Su Kasası ve sensör simülatörü (231 → 140 mm) → Zira Kartı → mühendis onayı → çiftçinin WhatsApp'ı

| Dürüst sınırlar | Sonraki adım |
|---|---|
| POWER ~50 km, MODIS ~6 ha; ürün türünü bilmez | Landsat 30 m (Earth Engine) |
| Aşama süreleri ve eşikler geçici, mühendis onayı bekliyor | Bir kooperatiften gerçek tarlalar, yerel kalibrasyon |
| Sensör verisi simülatörden; gerçek kalibrasyon yok | Referans toprak nemi probları, gerçek donanım |

**Zira karar vermez: çiftçinin delille karar vermesine yardım eder.**

Açık kaynak: [depo bağlantısı] · Yapay zekâ kullanımı: [kod, arayüz metinleri, mesaj taslağı metinleri ve bu slaytlar yapay zekâ asistanıyla hazırlandı, ekip tarafından gözden geçirildi; araç adlarını yazın] · Yapay zekâ ile üretilmiş görsel yok.

**Konuşmacı notları**
Videoyu başlatmadan: "Şimdi aynı akışı sensör simülatörüyle baştan sona izleyeceksiniz." Video bitince slaytta kalın tek satır kalsın: Zira · zira.soloftindustries.com · [takım adı]. Kapanış: "Zira karar vermez; kararı verenin elini NASA verisinin ışığıyla güçlendirir. Teşekkürler." Doğrulama dört aşamada ilerler: tek koordinat → tek gerçek tarlada üç rotasyon → aynı havzada iki tarla → yerel kalibrasyonla başka iklim; eşikler yeni bölgeye asla kopyalanmaz. Sınırlar sütununu silmeyin: jürinin ilk sorusu budur.

---

## Sunumdan önce kontrol listesi
1. Videoda Kulu'yu tarla olarak ekleyin; test tarlasının (Konya, 32,505 / 37,905) NDVI'ı yıl boyu 0,15–0,26 olduğundan hepsi "nadas" çıkar.
2. Slayt 6'daki 202 mm (demo tarlası) ile 231 → 140 mm (sensör senaryosu) farklı koşullardan gelir; videoda gösterdiğinizle slaydı eşitleyin.
3. Green API QR eşleştirmesi (sunucuda "notAuthorized" idi).
4. Depo özel: "açık kaynak" yazacaksanız karar 0005'i ve özel UDS bağımlılığını çözün, yoksa o ibareyi silin.
5. "24 sezon" platformun, "25 sezon" kayıt uzunluğunun söylemidir; hangisini kastettiğinizi belirtin.
