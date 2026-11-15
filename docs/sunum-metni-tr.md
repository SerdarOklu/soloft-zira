# Zira: sunum metni (14 slayt, Türkçe)

Platformun 15 Kasım 2026 durumuna göre. 14 slayt, ardından formül sayfası, kaynakça ve sunum öncesi kontrol listesi. Son slayt (14) simülasyon videosudur.

Bu sürümde "prototip / planlı" etiketleri kaldırıldı; anlatı tek bir ürün üzerinden akar: **platform** (canlı, zira.soloftindustries.com) ve **simülasyon** (videoda). Jüri sorarsa söylenecek dürüst sınırlar (MODIS piksel boyutu, geçici ajronomi değerleri, sensör verisinin simüle olması) slayt 11 ve 13'te açıkça duruyor; bunları silmeyin, jüri bunları sorar ve siz önce söylemiş olursunuz.

Sunumdan önce doldurulacaklar: takım adı, depo bağlantısı, kullanılan yapay zekâ araçlarının adları, video dosyası.

Önerilen süre: 7 dk anlatım + 2 dk video = 9 dk. Her slayt için yaklaşık 30 sn; slayt 7, 9 ve 14 biraz daha uzun.

---

## SLAYT 1 / 14 · KAPAK

**NASA SPACE APPS CHALLENGE 2026 · FIELD SHIFT: ADAPTING FARMS WITH NASA DATA**

# Zira
**Bu tarlanın suyu hangi rotasyonu taşır?**

Zira, ekim kararı gününde bir tarlanın toprağında kullanılabilir kaç milimetre su olduğunu gösterir ve üç rotasyonu 24 sezonluk NASA verisiyle karşılaştırır.

[Takım adı] · Canlı platform: zira.soloftindustries.com

**Konuşmacı notları**
Zira, kıraç tarım arazileri için bir karar destek platformudur. Ziraat mühendisleri ve kooperatifler için yapıldı; çiftçi sonucu WhatsApp'tan kısa ve sade bir mesaj olarak alır. Zira karar vermez; ziraat mühendisinin ve çiftçinin kararını destekler. Bugün size üç şey göstereceğiz: uydudan okunan tarla geçmişi, tarlanın suyu, ve bu suyla üç rotasyonun nasıl davrandığı. Sonunda bunların hepsinin çalıştığı simülasyonu videoda izleyeceksiniz.

---

## SLAYT 2 / 14 · SORUN

# Takvime göre planlanan tarım, suya göre değil

| | |
|---|---|
| **740+** | Konya Kapalı Havzası'nda kayıtlı obruk |
| **3,4 cm / yıl** | Yeraltı suyu depolama kaybı (GRACE tabanlı bir çalışmaya göre) |
| **245 – 534 mm** | Demo konumunda 25 sezonun en kurağından en yağışlısına sezonluk yağış |

- Yağış daha az öngörülebilir, su daha kıt, toprak sağlığı geriliyor.
- Bir yerde toprağı iyileştiren ürün, başka bir yerde fazla su tüketebilir.
- Takvime bağlı bir rotasyon 245 mm'lik sezonda da 534 mm'lik sezonda da aynı şekilde ekilir.
- Çiftçinin elinde rotasyonları kendi tarlası için tartabileceği sade bir araç yok.

*Kaynaklar: Konya Teknik Üniversitesi Obruk Araştırma Merkezi (NTV/İHA, 17 Ağustos 2026) · Khorrami, Arık ve Gündüz 2021 · NASA POWER*

**Konuşmacı notları**
İlk hedefimiz Konya Kapalı Havzası'nın yarı kurak iklimi ve kuru tarım. Araştırmacılar yeraltı suyundaki düşüşü sulama amaçlı yoğun pompajla ilişkilendiriyor, obrukların yayılmasını da buna bağlıyor. Buna rağmen yaygın rotasyon sabit: bir yıl buğday, bir yıl nadas. NASA GRACE ve GRACE-FO verisini geniş bölge (yaklaşık 300 km) için kendimiz okuduğumuzda toplam su depolaması 2002–2022 arasında yılda 0,46 cm azalıyor. Bu geniş bir alandaki bütün suyun toplamıdır; 3,4 cm ise çalışmanın havza içindeki yeraltı suyu tahminidir. İki rakam farklı şeyleri ölçer, birbirinin yerine konmamalı. 245–534 mm değeri demo konumuna aittir ve NASA POWER'ın 25 sezonluk yağış kaydından gelir.

---

## SLAYT 3 / 14 · KİMİN İÇİN

# Üç kullanıcı, tek gerçek

| Ziraat mühendisi | Kooperatif | Çiftçi |
|---|---|---|
| Tarlayı çizer, uydu geçmişini doğrular, kuralları onaylar, mesajları onaylar | Çiftçi hesaplarını açar, tarlaları çiftçilere bağlar, sensör düğümlerini yönetir | WhatsApp'tan kısa mesaj alır; "Tarlam" ekranında suyunu ve gönderilmiş mesajları görür |

**Zira karar vermez.** Mühendis onayı olmadan hiçbir mesaj çiftçiye gitmez. Çiftçi, mühendisin görmediği taslağı hiçbir zaman görmez.

Roller sunucuda zorlanır: çiftçi başkasının tarlasını, başka kullanıcıyı ya da mühendis ekranlarını menüden gizlenmekle değil, API'nin reddetmesiyle göremez.

**Konuşmacı notları**
Bir karar destek aracı, karar zincirindeki herkesin yerini bilmelidir. Mühendis uzmanlığı getirir ve son sözü söyler. Kooperatif ölçek getirir: yüzlerce çiftçiyi tek panelden yönetir. Çiftçi ise sonucu sade bir dille alır. Üç rol de canlı platformda çalışıyor; yönetici, mühendis, kooperatif ve çiftçi hesapları giriş yaptıklarında farklı ekranlara düşer.

---

## SLAYT 4 / 14 · ÇÖZÜM

# Tek soru, üç modül

> "Ekim kararı gününde toprak kaç milimetre kullanılabilir su tutuyor ve bu suyla üç rotasyon nasıl davranıyor?"

| MODÜL 1 · Tarla Hafızası | MODÜL 2 · Su Kasası | MODÜL 3 · Zira Kartı |
|---|---|---|
| Tarla son on sezonun hangisinde ekiliydi, hangisinde nadas? Uydu bitki örtüsünden okunur, mühendis doğrular. | Karar gününde kök bölgesindeki kullanılabilir su, mm olarak, belirsizlik aralığıyla; sensör varsa sensörle düzeltilir. | Her rotasyon için: 24 sezonun kaçında su yetti, neden, hangi kanıtla, yerelde neye bakılmalı. |

**Ekranlar:** Genel Bakış · Tarlalar · Tarla Hafızası · Su Kasası · Rotasyon ve Zira Kartı · Veri Merkezi · WhatsApp Mesajları · Kullanıcılar ve Kooperatif · Tarlam (çiftçi)

**Konuşmacı notları**
Üç modül bir zincir: Tarla Hafızası "bu tarlada ne ekiliyordu" sorusunu cevaplar ve rotasyon A'yı belirler; Su Kasası "bugün toprakta ne kadar su var" sorusunu; Zira Kartı "bu suyla hangi rotasyon yeter" sorusunu. Tek motor her tarla için çalışır; tarlalar arasında değişen her şey Tarla Profili'nde durur, kodda değil.

---

## SLAYT 5 / 14 · NASA VERİSİ

# Her kaynağın tek bir görevi var, kendi ölçeğinde

| Kaynak | Zira'daki görevi | Ölçek | Durum |
|---|---|---|---|
| **NASA POWER** | Günlük hava: yağış, sıcaklık, nem, rüzgâr, radyasyon, basınç | ~50 km, günlük | **Platformda** · 2001–2025, tarla başına 9.131 gün |
| **MODIS MOD13Q1 / MYD13Q1** | Tarla geçmişi: ekili mi nadas mı | 250 m, 16 günlük (Terra + Aqua) | **Platformda** · tarla poligonunun içinden, 10 sezon, ~450 görüntü |
| **Landsat 8/9** | Poligon içi NDVI (30 m): Tarla Hafızası yeterli sezonu kapsıyorsa Landsat'ı tercih eder | 30 m, ~16 günlük | **Platformda** · Collection 2 Seviye-2, Landsat 9 2022'den beri |
| **SMAP** | Yüzey toprak nemi (üst 5 cm), modelle eğilim karşılaştırması | 9 km, günlük | **Platformda** · NASA Earthdata; demo tarlada son 60 gün, sabah ortalaması 0,098 m³/m³ |
| **GPM IMERG** | POWER yağışına karşı çapraz kontrol | ~10 km, günlük | **Platformda** · NASA Earthdata; 60 günde IMERG 56 mm, POWER 57 mm, r = 0,46 (Eylül 2025 sonrası hızlı Late sürümü) |
| **GRACE / GRACE-FO** | Havza su depolama eğilimi | ~300 km, aylık | **Platformda** · 2002'den günümüze (261 ay), NASA Earthdata; demo hücrede 2003'ten beri −0,73 cm/yıl |
| **SRTM (NASADEM)** | Tarla rakımı ve eğimi | 30 m | **Platformda** |

Veri Merkezi hangi kaynağın gerçekten bağlı olduğunu gösterir; bağlı olmayan bir kaynak asla sağlıklı gösterilmez.

**Konuşmacı notları**
Kendimize koyduğumuz ölçek kuralları: POWER bölgesel yeniden analizdir, tarlanın ölçümü değildir. SMAP 9 km'lik hücrenin ortalamasıdır, tek tarlanın ürününü göremez. GRACE geniş bir alandaki toplam su depolamasıdır, hiçbir zaman bir parselin altındaki yeraltı suyu değildir. Aynı GPM pikseline düşen tarlalar ayrı yağış gözlemi değildir. İki yağış kaynağı asla toplanmaz: POWER girdi, GPM IMERG çapraz kontroldür. SMAP, GPM ve GRACE modelin girdisi değil, bölgesel kontrolüdür ve ekranlar bunu söyler. SMAP yalnızca üst 5 cm'yi görür, Su Kasası 1,8 m'ye kadar kök bölgesini modeller; ikisi sayı olarak değil eğilim olarak (birlikte kuruyor ve ıslanıyor mu) karşılaştırılır. ECOSTRESS bağlı değildir ve Veri Merkezi bunu böyle gösterir. Earthdata verileri sunucudaki bir Earthdata jetonuyla okunur; jeton yaklaşık 60 günde dolar ve dolunca bu üç kaynak "bağlı değil" görünür, asla sağlıklı gösterilmez.

Attribution: Hava verisi NASA Langley Araştırma Merkezi (LaRC) POWER Projesi'nden alınmıştır; proje NASA Earth Science/Applied Science Program tarafından finanse edilmektedir. NASA GIBS, NASA ESDIS'in parçası olarak sunulan görüntüler kullanılmıştır.

---

## SLAYT 6 / 14 · MODÜL 1: TARLA HAFIZASI

# Uydu, tarlanın son on yılını okur

1. Tarla haritada çizilir; poligonun içindeki her Landsat 8/9 pikseli (30 m) ve MODIS pikseli (250 m) alınır.
2. Landsat'ta kalite bandı temiz işaretleyen pikseller (dolgu, bulut, sirüs, gölge ve kar dışarıda), MODIS'te güvenilirliği "iyi" ya da "sınırda" olanlar tutulur; dışarıda kalanlar sayılır.
3. Sezonun (1 Mart – 30 Eylül) **en yüksek NDVI'ı ≥ 0,40** ise **ekili**, altındaysa **nadas**; yeterli temiz görüntü yoksa **bilinmiyor**.
4. Landsat, on sezonun en az altısında karar verebiliyorsa geçmiş Landsat'tan, değilse MODIS'ten çıkarılır; ekran hangisinin kullanıldığını söyler, kullanıcı istediğini seçebilir. Her sezon için güven düzeyi hesaplanır; mühendis ya da kullanıcı doğrular. Doğrulanmış geçmiş rotasyon A olur.

NDVI = (NIR − Kırmızı) / (NIR + Kırmızı)

**Konuşmacı notları**
Earth Engine projemiz olmadan MODIS'i NASA'nın MOD13Q1 (Terra) ve MYD13Q1 (Aqua) sürüm 061 ürünlerinden, Microsoft Planetary Computer'ın herkese açık STAC kataloğundaki bulut için optimize GeoTIFF'lerden okuyoruz; hesap ya da anahtar gerekmiyor. Her görüntü için poligonun içindeki pikselleri alıyoruz. Ekranda her sezonun tepe NDVI'ı ve temiz görüntü sayısı görünür; düşük güvenli sezonlar işaretlenir ve bilinmeyenler kullanıcıya bırakılır. Bu şeffaflık bilinçli: sistem emin olmadığı yerde tahmin yürütmez, sorar.

Landsat 30 m'de birkaç hektarlık bir tarla düzinelerce piksel içerir; MODIS'te bir avuç. Bu yüzden küçük parsellerde Landsat tercih edilir. Tek tıkla "Getir" MODIS ile iki Landsat platformunu kuyruğa alır. Landsat 9'un sahneleri 2022'den başlar; öncesi hata değil, boş sonuçtur. Sınır: bir MODIS pikseli yaklaşık 6 hektardır, komşu pikseller sinyale karışır; iki sensör de ekili ile nadası ayırır, ürün türünü ve kış–yaz ayrımını bilmez. 30 m'lik piksel daha saf olduğundan en iyi NDVI eşiği muhtemelen 0,40'tan yüksektir; bunu ancak geçmişi bilinen tarlalarla kalibrasyon belirler. Güven formülü: min(1, |tepe NDVI − 0,40| / 0,20) × min(1, temiz görüntü sayısı / 13).

---

## SLAYT 7 / 14 · MODÜL 2: SU KASASI

# Günlük FAO-56 su dengesi: toprakta kaç mm su var?

| Adım | Formül |
|---|---|
| Atmosferin su talebi | ET₀ = [ 0,408 Δ (Rₙ − G) + γ · 900/(T + 273) · u₂ (eₛ − eₐ) ] / [ Δ + γ (1 + 0,34 u₂) ] |
| Bitki su ihtiyacı | ETc = Kc × ET₀ |
| Toprak kapasitesi | TAW = 1000 (θFC − θWP) Zr ; RAW = p × TAW |
| Günlük denge | S(t) = min( TAW, max( 0, S(t−1) + Peff + I − ETa − R − D ) ) |
| Su stresi | ETa = Ks × Kc × ET₀ ; Ks = 1 (S ≥ (1 − p) TAW), değilse S / ((1 − p) TAW) |

**Çıktı:** karar gününde kök bölgesindeki kullanılabilir su (mm), düşük–yüksek aralığıyla; günlük depo ve ET₀ grafikleri.

**Konuşmacı notları**
Kendi icat ettiğimiz bir model değil: FAO'nun uluslararası standardı olan FAO-56. ET₀, Kc eğrisi, TAW/RAW ve stres hesabı platformda FAO-56'nın basılı örnekleriyle test edildi (Örnek 18: Uccle, 6 Temmuz, ET₀ = 3,88 mm/gün). Semboller: ET₀ referans evapotranspirasyon; Kc bitki katsayısı; TAW kök bölgesinde toplam kullanılabilir su; p stres başlamadan kullanılabilen pay; S kök bölgesi deposu; Peff etkili yağış; Ks stres katsayısı.

Belirsizlik: her sonuç üç kez hesaplanır; toprağın metre başına kullanılabilir suyunun düşük, orta ve yüksek değeriyle, yağış payı da 0,10 aynı yönde kaydırılarak. Kart orta sonucu, düşükten yükseğe aralıkla gösterir. Tek sayı yerine aralık göstermek bir tasarım ilkesi: tek sayı kesinlik izlenimi verir.

---

## SLAYT 8 / 14 · MODÜL 3: ÜÇ ROTASYON, ZİRA KARTI

# Aynı tarla, aynı hava, aynı toprak: yalnızca rotasyon değişir

| A · Mevcut rotasyon | B · Suya bağlı esnek | C · Baklagilli |
|---|---|---|
| Doğrulanmış geçmişi tekrarlar (örn. buğday–nadas) | 1 Ekim'de kasa ≥ %50 TAW ise eker, değilse nadas bırakır | Nadas yıllarının her ikincisinde baklagil eker |

**Bir sezon "su yetti"** sayılır: Σ ETa ÷ Σ ETc ≥ 0,70

Kartın her strateji bloğunda aynı beş alan: **neden önerildi · dayandığı veri · beklenen fayda · bilgi boşluğu · yerelde incelenmesi gereken risk.** Kart yazdırılabilir; her rakam aralıkla gelir.

**Platformdaki demo tarlasında (1 Ekim 2025, kışlık buğday, tınlı toprak, kapasite 279 mm):**
- Kullanılabilir su 198 mm (aralık 152–243)
- Su, A için 12 ekimin 4'ünde, B için 7 ekimin 7'sinde, C için 18 ekimin 9'unda yetti

**Konuşmacı notları**
Karşılaştırma adil olsun diye üç rotasyon bir ısınma sezonundan sonra aynı depodan başlar; ısınma simüle edilir, sayılmaz. Bir sezon yalnızca günlerinin en az %95'inde tam veri varsa sayılır; böylece platformda 2001–2025 kaydı 24 tam sezona bölünür. Bu sayılar geçici başlangıç değerleriyle üretildi: ürün aşama süreleri (FAO-56 Tablo 11), ekim tarihi, sulama verimi ve NDVI eşiği ayrı bir yapılandırma dosyasında kaynağıyla yazılıdır, kartta "geçici" etiketi taşır ve ziraat mühendisi onayıyla yerel değerlere çekilir. Mühendis onaylamadıkça hiçbir ürün kesin öneri olarak gösterilmez. Rotasyon C'de baklagil olarak şimdilik mercimek kullanılıyor çünkü nohut için FAO-56 Tablo 11'de aşama süreleri yok.

---

## SLAYT 9 / 14 · UYDU + YER: SENSÖR MODU

# Uydu bölgeyi görür, sensör tarlayı ölçer

**Sensör modu:**
1. 10, 30, 60 ve 100 cm derinliklerde toprak nemi düğümleri, gerçek donanımla aynı şemayla `POST /sensors/{düğüm}/readings` ucuna veri gönderir.
2. Ham okuma, tarlaya özgü **kalibrasyonla** (gravimetrik örnek: solma noktası + tarla kapasitesi) kullanılabilir su payına çevrilir. Kalibrasyon yoksa sensöre güvenilmez.
3. Her derinliğin payı temsil ettiği katmanla ağırlıklanır ve kök bölgesi TAW'ı ile çarpılarak **karar günü deposu** olur; modelin deposunun yerini alır.
4. Aralık daralır: sensör okuması ± TAW'ın %10'u.
5. Bir düğüm 48 saat susarsa tarla **otomatik olarak uydu moduna** döner.

**Ekranda "uydu ile sensör" yan yana:** örnek senaryoda model 198 mm derken sensör 138 mm (kapasite 279 mm) gösteriyor; fark ekranda görünür.

**Konuşmacı notları**
Bu, uydu ve yeryüzü arasındaki köprü. Uydu ve model bölgesel bir tahmindir; sensör tarlanın kendi ölçümüdür. İkisi birleştiğinde hem güven hem de doğruluk artar. Sensör mesajı ışığında kasa değeri değişir, aralık daralır ve kullanıcı ikisini yan yana görür. Gösterdiğimiz okumalar, gerçek donanımın göndereceği şemayla çalışan sensör simülatöründen gelir ve ekranlarda "simüle" olarak işaretlenir; donanıma geçildiğinde backend'de tek satır değişmez. Mevcut %10 bandı, gerçek bir toprakta kalibrasyon hatasından belirlenecek bir başlangıç değeridir. Sensör mesajı, sensör düğümü başına bir anahtarla doğrulanır (ortak anahtar sunucuda tanımlıdır).

---

## SLAYT 10 / 14 · MESAJ AKIŞI VE KOOPERATİF PANELİ

# Olaydan çiftçinin telefonuna: mühendis onayıyla

**Zira bir olay görünce taslak yazar:**
- Ekim kararı günü · bir günde ≥ 20 mm yağış · kök altına ≥ 5 mm su inmesi (yıkanma uyarısı) · hassas dönemde 5. ve 15. stres günü · hasatta sezon özeti

**Akış:** olay → modelin o günkü sayılarıyla taslak → **mühendis düzenler, onaylar ya da reddeder** → Green API ile WhatsApp.

> "Ekim kararı, 1 Eki 2025. Toprakta 95 mm kullanılabilir su var (kapasite 279 mm); bu, 140 mm eşiğinin altında. Alışılmış rotasyonunuzda bu yıl kışlık buğday var, ama esnek kurala göre tarla nadasa bırakılır. Ekmeden önce ziraat mühendisinizle konuşun. Zira karar vermez; ziraat mühendisinin ve çiftçinin kararını destekler."

**Kooperatif paneli:** çiftçi hesabı aç/kapat, geçici şifre ver, her tarlayı bir çiftçiye bağla, kendi organizasyonunun dışını görme.
**Çiftçi ekranı "Tarlam":** tek ekran: karar gününde kullanılabilir su, aralığı, **gönderilmiş** mesajlar.

**Konuşmacı notları**
Çiftçiye giden her mesaj kısa, Türkçe ve altında aynı cümle var: "Zira karar vermez." Taslaklar mühendisin kuyruğunda bekler; hiçbir mesaj onaysız çıkmaz. Kooperatif panelinin amacı ölçek: bir kooperatif kullanıcısı kendi organizasyonundaki çiftçileri açar, tarlaları bağlar; yönetici her yerde aynısını yapabilir. Çiftçi yalnızca gönderilmiş mesajları ve kendi tarlasını görür. [Sunumdan önce Green API eşleştirmesini doğrulayın; çalışmıyorsa "gönderim hazır, eşleştirme bekliyor" deyin.]

---

## SLAYT 11 / 14 · GÜVEN VE ŞEFFAFLIK

# Zira neden güvenilir: kendini kontrol eden bir sistem

| İlke | Nasıl |
|---|---|
| **Aralık, tek sayı değil** | Her sonuç düşük/orta/yüksek koşuyla; sensör varsa aralık daralır |
| **Bilmiyorsa söyler** | NDVI yetersizse sezon "bilinmiyor"; düşük güvenli sezonlar işaretlenir |
| **İnsan onayı** | Mühendis onayı olmadan mesaj çıkmaz; ürün onaysız kesin öneri olmaz |
| **Geçici değerler görünür** | Aşama süreleri, ekim tarihi, eşikler kartta "geçici" etiketiyle kaynağıyla yazılı |
| **Ölçek kuralları** | POWER bölgesel, MODIS 6 ha, GRACE havza ölçeği: hiçbiri tarla ölçümü gibi sunulmaz |
| **Bağımsız kontrol** | Su modeli NASA SMAP ve MERRA-2 toprak neminden bağımsız kontrol edildi (r = 0,61) |
| **Test edilmiş** | FAO-56 basılı örnekleriyle test; 200'den fazla otomatik backend testi |

**Konuşmacı notları**
Bu slayt jüri sorusunu önceden cevaplıyor: "Modele nasıl güveneceğiz?" Cevabımız tek bir doğruluk iddiası değil, bir güven mimarisi. Platformdaki tüm eşikler yapılandırma dosyasında kaynağıyla yazılıdır ve ziraat mühendisinin onayını bekler; biz bunu eksiklik olarak değil, ürünün yerel uzmanla birlikte çalışacağının işareti olarak tasarladık. Bağımsız kontrolde model toprak nemi seyri NASA SMAP ve MERRA-2 ile r = 0,61 uyumlu çıktı. Bu bir eğilim kontrolüdür: SMAP 9 km'lik hücre ortalamasıdır, tarla ölçümü değildir.

---

## SLAYT 12 / 14 · SONUÇLAR

# Kulu doğrulama çalışması: 2016–2026

| | |
|---|---|
| **Tarla Hafızası** | 2016–2026 sezonları ekili ve nadas arasında temiz biçimde değişiyor; VIIRS, kapsadığı iki baharda MODIS ile uyuşuyor |
| **Su Kasası** | 12 Kasım 2026'da 144 mm kapasitenin 13 mm'si |
| **Üç rotasyon** | Su 13 ekimin 6'sında A için, 10'un 5'inde B için, 21'in 3'ünde C için yetti |
| **Aralık** | Altı koşudan çıkar: iki yağış kaynağı × üç toprak kapasitesi |
| **Bağımsız kontrol** | SMAP ve MERRA-2 toprak nemi ile r = 0,61 |
| **Sensör düzeltmesi** | Simülatör verisiyle karar günü suyu 198 mm'den 138 mm'ye iner (kapasite 279 mm) |

Bu çalışma, tek bir 250 m MODIS pikselinde net bir ekili–nadas sinyali olan Kulu'da yapıldı: bilimi derinlemesine sınamak için seçilmiş bir konum, taranmış bir tarla değil.

**Konuşmacı notları**
Çalışmanın kendi ölçütü: bir ekimi FAO-33 göreli verimi 1 − Ky (1 − Ta/Tp) en az %50 ise yeterli sayıyoruz. B, 15 Ekim'de kasada en az 60 mm varsa buğday eker, art arda iki yıldan fazla değil; C, ekim tarihinde kasada en az 40 mm varsa baklagil eker. Aralıklar A için 1–9, B için 3–10, C için 2–7.

Sistem kendini ekranda eleştirir: altı ekili yılın en zayıf bahar yeşermesi 2022'deydi, oysa su modeli en düşük verimi 2024'e veriyor. Bu bir hata gizleme değil, görünür bir uyarı. Platformdaki demo tarlasının sayıları (slayt 8) farklıdır, çünkü konum, toprak ve kurallar farklıdır; ikisini karıştırmıyoruz. Sensör satırı simüle edilmiş veriyle yapılan uçtan uca testin sonucudur.

---

## SLAYT 13 / 14 · ETKİ, SINIRLAR, YOL HARİTASI

# Etki, dürüst sınırlar ve sonraki adım

| ETKİ | SINIRLAR (bilerek açık) | SONRAKİ ADIM |
|---|---|---|
| Çiftçinin okuyabileceği, tarla düzeyinde karşılaştırma; ücretsiz NASA verisiyle | POWER ~50 km bölgesel veridir; MODIS pikseli ~6 ha | Bir kooperatiften gerçek tarlalar; her kural için mühendis onayı |
| Daha çok ekim ile daha çok karşılanmayan su arasındaki denge görünür | Aşama süreleri ve eşikler geçici; yerel ajronomi onayı bekliyor | NDVI eşiğinin Landsat için yerel kalibrasyonu; ECOSTRESS (70 m evapotranspirasyon) |
| Mühendis onayı olmadan hiçbir mesaj çiftçiye gitmez | Sensör verisi şimdilik simülatörden; gerçek kalibrasyon yok | Referans toprak nemi probları; gerçek donanım, gravimetrik kalibrasyon |
| Kooperatif ölçeğinde yönetim | Belirsizlik her zaman gösterilir; yerel doğrulama mühendisindir | Aynı havzada iki tarla daha; çiftçi önceliği ve kısıtları girdi olarak |

**Doğrulama dört aşamada:** tek koordinatta boru hattı → tek gerçek tarlada üç rotasyon → aynı havzada iki farklı tarla → yerel kalibrasyonla başka iklim bölgesi. Eşikler ve katsayılar yeni bir bölgeye asla kopyalanmaz.

**Zira karar vermez: çiftçinin delille karar vermesine yardım eder.**

Açık kaynak: [depo bağlantısı] · Yapay zekâ kullanımı: [kod, arayüz metinleri, mesaj taslağı metinleri ve bu slaytlar yapay zekâ asistanıyla hazırlandı ve ekip tarafından gözden geçirildi; araçların adlarını yazın] · Yapay zekâ ile üretilmiş görsel yok.

**Konuşmacı notları**
Sensör donanımı tasarımı: 10, 30, 60 ve 100 cm'de toprak nemi probları, tarla başına üç dört düğüm, güneş panelli LoRaWAN ya da LTE-M, her toprak türü için gravimetrik kalibrasyon. Tarlalar ham sayılar üzerinden birbirleriyle sıralanmaz; her tarla kendi mevcut rotasyonuna göre ve veri güveniyle raporlanır. Sınırlar sütununu silmeyin: jürinin ilk sorusu budur ve doğru cevap, sınırı sizin söylemenizdir.

---

## SLAYT 14 / 14 · VİDEO: SİMÜLASYON

# Zira, uçtan uca

▶ **[Video, 2 dk]**

**Önerilen çekim sırası (video ile slayt metninin örtüşmesi için):**
1. 0:00–0:15 · Harita: tarla çizilir; alan ve merkez otomatik hesaplanır.
2. 0:15–0:35 · Tek tıkla 25 yıllık NASA POWER verisi gelir; yağış grafiği.
3. 0:35–0:55 · Tarla Hafızası: MODIS NDVI, 10 sezon, ekili/nadas, güven düzeyi, doğrulama.
4. 0:55–1:15 · Su Kasası: karar günü kullanılabilir su, aralık; sensör simülatörü başlar, değer 198'den 138 mm'ye iner, "uydu ile sensör" yan yana.
5. 1:15–1:40 · Zira Kartı: A, B, C yan yana, 24 sezon, aralık.
6. 1:40–1:55 · Mesaj taslağı mühendis kuyruğunda; onay; WhatsApp'ta çiftçi.
7. 1:55–2:00 · "Zira karar vermez." + canlı adres.

**Kapanış cümlesi:** "Zira karar vermez; kararı verenin elini, NASA verisinin ışığıyla güçlendirir. Teşekkürler."

**Konuşmacı notları**
Videoyu başlatmadan önce tek cümle: "Şimdi aynı akışı, sensör simülatörüyle birlikte baştan sona izleyeceksiniz." Video bittiğinde slaytta kalın, tek satır: Zira · zira.soloftindustries.com · [takım adı]. Soru-cevap sırasında slayt 11 ve 13'e dönebilmek için sunumun bu iki slaytını işaretleyin.

---

# FORMÜL SAYFASI (slayt değil; sorulursa gösterilecek)

Kaynak: 1–5. bölümler Allen, Pereira, Raes ve Smith (1998), Crop evapotranspiration, FAO Irrigation and Drainage Paper 56. 6–9. bölümler Zira'nın tasarım kurallarıdır; varsayılanları ziraat mühendisi onayını bekler. ET₀, Kc eğrisi, TAW/RAW ve stres hesabı FAO-56'nın basılı örnekleriyle test edilmiştir (Örnek 18: Uccle, 6 Temmuz, ET₀ = 3,88 mm/gün).

## 1. Günlük girdiler
- Doygun buhar basıncı: e°(T) = 0,6108 · exp( 17,27 T / (T + 237,3) ) [kPa, T °C]
- eₛ = ( e°(Tmaks) + e°(Tmin) ) / 2 ; eₐ = (BNortalama / 100) · eₛ
- z yüksekliğindeki rüzgârdan 2 m'deki rüzgâr: u₂ = u_z · 4,87 / ln( 67,8 z − 5,42 ); z = 10 m için u₂ ≈ 0,748 · u₁₀
- BNmin = 100 · eₐ / e°(Tmaks)

## 2. Referans evapotranspirasyon
- ET₀ = [ 0,408 Δ (Rₙ − G) + γ · 900 / (T + 273) · u₂ (eₛ − eₐ) ] / [ Δ + γ (1 + 0,34 u₂) ]
- Δ = 4098 · e°(T) / (T + 237,3)² ; γ = 0,000665 · P ; günlük adımda G = 0
- Rₙ = 0,77 Rₛ − Rₙₗ
- Rₙₗ = σ · ( Tmaks,K⁴ + Tmin,K⁴ ) / 2 · ( 0,34 − 0,14 √eₐ ) · ( 1,35 Rₛ / Rₛₒ − 0,35 )
- Rₛₒ = ( 0,75 + 2 × 10⁻⁵ z ) · Rₐ
- T günlük ortalama (°C), P basınç (kPa), Rₛ güneş radyasyonu (MJ m⁻² gün⁻¹), z rakım (m), σ = 4,903 × 10⁻⁹ MJ K⁻⁴ m⁻² gün⁻¹; Rₐ enlem ve yılın gününden hesaplanan atmosfer dışı radyasyondur.

## 3. Bitki evapotranspirasyonu
ETc = Kc × ET₀, dört evreli Kc eğrisiyle (l_ini, l_dev, l_mid, l_late). Sezon ortası iklim düzeltmesi: Kc,mid = Kc,mid(Tablo) + [ 0,04 (u₂ − 2) − 0,004 (BNmin − 45) ] · (h / 3)^0,3. Platformun şimdiki sürümü tablo değerini kullanır, bu düzeltmeyi uygulamaz.

FAO-56 başlangıç değerleri (Tablo 12 ve 22):

| Ürün | Kc başlangıç | Kc orta | Kc son | Kök derinliği (m) | p |
|---|---|---|---|---|---|
| Kışlık buğday | 0,4 donan toprak; 0,7 donmayan | 1,15 | 0,25–0,4 | 1,5–1,8 | 0,55 |
| Arpa | 0,3 | 1,15 | 0,25 | 1,0–1,5 | 0,55 |
| Nohut | 0,4 | 1,00 | 0,35 | 0,6–1,0 | 0,50 |
| Mercimek | 0,4 | 1,10 | 0,30 | 0,6–0,8 | 0,50 |

Geçici aşama süreleri (gün, FAO-56 Tablo 11): kışlık buğday 30 / 140 / 40 / 30 (Akdeniz, Kasım); mercimek 25 / 35 / 70 / 40 (kurak bölge, Ekim–Kasım). Nohut için Tablo 11'de satır yoktur. Konya, tablodaki Akdeniz satırından daha soğuktur; gerçek süreleri ziraat mühendisi girecektir.

## 4. Toprağın su kapasitesi
- TAW = 1000 (θFC − θWP) Zr ; RAW = p · TAW
- p = p(Tablo) + 0,04 (5 − ETc), 0,1 ile 0,8 arasında tutulur
- Dokuya göre kullanılabilir su (FAO-56 Tablo 19): kumlu tın 110–150 mm/m, tın 130–180 mm/m, siltli tın 130–190 mm/m, kil 120–200 mm/m. Orta değer varsayılandır; sınırlar belirsizlik koşularını sürer.

## 5. Günlük su dengesi ve stres
- Sₜ = min( TAW, max( 0, Sₜ₋₁ + Peff + I − ETa − R − D ) )
- ETa = Ks · Kc · ET₀ ; S ≥ (1 − p) · TAW iken Ks = 1; değilse Ks = S / ( (1 − p) · TAW )
- Peff = 0,80 × P (varsayılan); I = uygulanan sulama × sulama verimi; D, o gün TAW'ı aşan miktar
- Nadasta depo günlük 0,25 × P kazanır ve TAW'ı geçemez (varsayılan)

## 6. Sezonlar, karar ve ölçütler
Bir sezon ekim ile hasat arasında sürer, Ocak–Aralık arasında değil. Platformda 2001–2025 kaydı 24 tam sezona bölünür (Kasım'da ekilen kışlık sezon ertesi yıl biter, 2025 ekimi kayıtla tamamlanamaz). Bir sezon yalnızca günlerinin en az %95'inde tam veri varsa sayılır.

- Su yeterli sezon: Σ ETa ÷ Σ ETc ≥ 0,70
- Kritik dönemde stres günü: sezon ortası evresinde Ks < 1 olan günler
- Sezonluk su açığı (mm): Σ (ETc − ETa)
- Sulama ihtiyacı (mm): sezonluk açık ÷ sulama verimi (verim 0,75, geçici)
- Mevcut rotasyondan fark: B ve C'nin her ölçütü eksi A'nın aynı ölçütü

## 7. Strateji kuralları ve belirsizlik
- A: doğrulanmış ya da seçilen sıra, 24 sezon boyunca tekrarlanır.
- B: karar gününde (kışlık ürünler için 1 Ekim) S ≥ 0,50 × TAW ise planlanan ürünü eker; değilse nadas.
- C: A gibi, ama nadas sezonlarının her ikincisine baklagil.
- Üçü de bir ısınma sezonundan sonra 0,50 × TAW'dan başlar; ısınma simüle edilir, sayılmaz.
- Belirsizlik: toprağın metre başına kullanılabilir suyunun düşük, orta, yüksek değeriyle üç koşu; etkili yağış payı ve nadas verimi 0,10 aynı yönde kaydırılır.

## 8. Uydu işleme
**MODIS (platformda).** MOD13Q1 ve MYD13Q1 sürüm 061, NDVI = 0,0001 × DN. Her görüntüde tarla poligonunun içindeki pikseller alınır (poligona değenler dahil); piksel güvenilirliği 0 (iyi) ya da 1 (sınırda) olanlar tutulur, 2 (kar) ve 3 (bulut) ile eksik değerler dışarıda kalır. Her görüntü için ortalama ve ortanca NDVI, temiz piksel sayısı ve dışarıda kalan pay saklanır. Sezon = hasat yılının 1 Mart – 30 Eylül penceresi. En yüksek NDVI ≥ 0,40 ise ekili, değilse nadas; temiz görüntü 5'ten azsa bilinmiyor (Landsat'ta sezonda en az 4 temiz sahne). Güven = min(1, |tepe NDVI − 0,40| / 0,20) × min(1, temiz görüntü sayısı / 13). Eşik geçicidir; bilinen geçmişli yerel tarlalarla kalibre edilecektir.

**Landsat (platformda).** Collection 2 yüzey yansıması: SR = DN × 0,0000275 − 0,2. NDVI = (NIR − Kırmızı) / (NIR + Kırmızı); Landsat 8/9 için NIR = SR_B5, Kırmızı = SR_B4. Sahne bulutluluğu %70'in altındaki sahneler okunur; dolgu, genişletilmiş bulut, sirüs, bulut, gölge ve kar pikselleri QA_PIXEL ile maskelenir; istatistikler tarla
poligonunun içinden alınır. Landsat, en az 6 sezonda karar verebiliyorsa geçmiş Landsat'tan, değilse MODIS'ten çıkarılır.

## 9. Sensör düzeltmesi
- Kalibrasyon: θ = eğim × ham + kesişim (tarla başına, gravimetrik örnekle)
- Her derinlikte kullanılabilir su payı: (θ − θWP) / (θFC − θWP), 0–1 arasında kırpılır
- Katmanlar sensörler arasında yarı yarıya bölünür; paylar katman kalınlığıyla ağırlıklanır
- Karar günü deposu = ağırlıklı pay × TAW; modelin deposunun yerini alır
- Aralık: sensör okuması ± %10 TAW (geçici)
- Sessizlik: 48 saat okuma yoksa uydu moduna dönüş

## 10. Doğrulama çalışmasının kuralları (Kulu)
Çift bitki katsayısı (FAO-56), iki katmanlı toprak kovası ve açık toprak buharlaşması. Yeterli ekim: göreli verim 1 − Ky (1 − Ta / Tp) ≥ %50 (Doorenbos ve Kassam, 1979, FAO-33). B, 15 Ekim'de kasada en az 60 mm varsa buğday eker, art arda iki yıldan fazla değil; C, ekim tarihinde kasada en az 40 mm varsa baklagil eker. Altı koşudan aralıklar: iki yağış kaynağı (MERRA-2 düzeltilmiş yağış, GPM IMERG) × üç toprak su kapasitesi.

---

## Kaynakça
- Allen, R. G., Pereira, L. S., Raes, D., Smith, M. (1998). Crop evapotranspiration. FAO Irrigation and Drainage Paper 56.
- Doorenbos, J., Kassam, A. H. (1979). Yield response to water. FAO Irrigation and Drainage Paper 33.
- Khorrami, B., Arık, F., Gündüz, O. (2021). Land deformation and sinkhole occurrence in response to the fluctuations of groundwater storage. GIScience & Remote Sensing 58(8), 1518–1542. https://doi.org/10.1080/15481603.2021.2000349
- NTV / İHA (17 Ağustos 2026). Konya Ovası'nda alarm. Sayı 740'ı aştı. https://www.ntv.com.tr/yerel-haberler/galerikonya-ovasinda-alarm-sayi-740i-asti-1737722
- NASA Langley Research Center, POWER Project, Daily API v2. https://power.larc.nasa.gov/
- NASA MODIS MOD13Q1 / MYD13Q1 Version 061 (LP DAAC), Microsoft Planetary Computer açık STAC kataloğu üzerinden. https://planetarycomputer.microsoft.com/
- NASA GIBS, NASA ESDIS'in parçası. Tam veri seti listesi ve atıflar için README'ye bakın.

---

## Sunumdan önce kontrol listesi
1. **Gösterilecek tarla.** Platformdaki test tarlasının (Konya, 32,505 / 37,905) gerçek MODIS NDVI'ı yıl boyu 0,15–0,26: on sezonun hepsi "nadas" çıkıyor, ekili–nadas değişimini göstermez. Videoda Kulu konumunu tarla olarak ekleyip NDVI'ı çekin ve değişimin göründüğünü önceden doğrulayın.
2. **Sayıları ekrandan teyit edin.** Slayt 8, 9 ve 12'deki sayılar canlı Kulu demo tarlasından alındı (198 mm model, 138 mm simüle sensör, karar 0014); videoyu aynı tarlada çekin.
3. **Green API.** QR eşleştirmesi tamamlandı mı? Sunucuda durum "notAuthorized" idi. Tamamlanmadıysa slayt 10'da "gönderim hazır, eşleştirme bekliyor" deyin.
4. **Depo bağlantısı ve "açık kaynak".** Depo özel. Herkese açık yapılacaksa karar 0005'i ve özel UDS bağımlılığını çözün; yapılmayacaksa slayt 13'teki "Açık kaynak" ibaresini kaldırın.
5. **Sayı tutarlılığı.** "24 sezon" platformdaki, "25 sezon" kayıt uzunluğunun söylemidir (2001–2025); konuşurken hangisini kastettiğinizi belirtin.
6. **Boşluklar.** Takım adı, depo bağlantısı, yapay zekâ araçlarının adları, video dosyası.
7. **Test sayısı.** "200'den fazla" ifadesi Faz 6 öncesi 203 teste dayanıyor; Faz 7 testleri eklendi, güncel sayıyı çalıştırıp yazabilirsiniz.
