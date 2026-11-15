# ZİRA – Jüri Sunumu Konuşma Metni (4 konuşmacı, ~5 dakika)

Dayanak: 7 slaytlık sunum metni ([presentation-text-en-7slides.md](presentation-text-en-7slides.md)). Sayılar o dosyayla birebir aynıdır.

| Sıra | Konuşmacı | Slayt | Süre | Ton |
|---|---|---|---|---|
| 1 | Açılış | 1–2 | 0:00–0:50 | Sıcak, sakin, sade |
| 2 | Orta (Serdar) | 3–4 | 0:50–2:00 | Kendinden emin, teknik olarak kesin |
| 3 | Formül sayfası | 5 | 2:00–3:00 | Net, anlaşılır, güvenilir |
| 2 | Orta (Serdar), devam | 6 | 3:00–4:05 | Kendinden emin, dürüst |
| 4 | Kapanış | 7 | 4:05–5:00 | Samimi, ilham verici, güçlü |

---

## KONUŞMACI 1 – AÇILIŞ
**0:00–0:50 · Slayt 1–2 · Sıcak, sakin, sade**

İyi akşamlar, değerli jüri üyeleri.

Tarım, yalnızca yiyecek yetiştirmek değildir. Aileler, kuşaklar ve geleceğimiz demektir.

Ama bugün çiftçilerimiz ciddi bir sorunla karşı karşıya: su azalıyor, yağış ise eskisi kadar tahmin edilebilir değil. Konya Kapalı Havzası'nda yedi yüzden fazla obruk kayıtlara geçti. Yer altı suyu her yıl çekiliyor.

Üstelik ekim kararı çoğu zaman takvime bakılarak veriliyor. Aynı tarla, 245 milimetrelik kurak bir sezonda da, 534 milimetrelik yağışlı bir sezonda da aynı şekilde ekiliyor.

Her ekim kararı önemlidir. Ve bazen o kararı vermek için gereken bilgi, eldeki araçlarla görünür değildir.

Biz, teknolojinin bunu değiştirebileceğine inanıyoruz.

İşte bu yüzden Zira'yı geliştirdik.

Şimdi nasıl çalıştığını anlatsın.

---

## KONUŞMACI 2 – ORTA (SERDAR)
**0:50–2:00 · Slayt 3–4 · Kendinden emin, teknik olarak kesin**

Teşekkürler.

Değerli jüri, bir çiftçi toprağının geleceğini kumar masasına bırakmak zorunda kalmamalı.

Zira'nın tek bir sorusu var: "Ekim kararı günü, toprak bitkinin yararlanabileceği kaç milimetre su tutuyor ve üç farklı münavebe bu suyla nasıl davranır?"

Bu soruyu üç modülle yanıtlıyoruz: Tarla Hafızası, Su Kasası ve Zira Kartı.

Tarla Hafızası, uydu görüntülerinden son on sezonda tarlanın ekili mi, nadasta mı olduğunu okur. Su Kasası, karar gününde köklerin ulaşabildiği suyu milimetre cinsinden, bir aralıkla birlikte verir. Zira Kartı ise üç münavebeyi aynı hava ve aynı toprakla karşılaştırır.

Bunu yaparken yalnızca NASA verisi kullanıyoruz ve her kaynağın tek bir görevi var.

Günlük hava verisi NASA POWER'dan gelir. Yaklaşık 50 kilometrelik çözünürlüğü olduğu için onu tarla ölçümü değil, bölgesel veri olarak ele alıyoruz.

Ekili ve nadas ayrımını Landsat ile 30 metrede yapıyoruz. Bulutlu dönemlerde MODIS devreye giriyor.

SMAP, GPM ve GRACE ise modele girdi değil, bölgesel çapraz kontrol. Bağlı olmayan bir kaynağı da asla sağlıklıymış gibi göstermiyoruz.

Ve bir şeyi açıkça söyleyeyim: Biz çiftçinin tecrübesinin yerine geçmeye gelmedik. O tecrübeye verinin gücünü katmaya geldik.

Şimdi bu hesabın arkasındaki bilimi arkadaşım anlatacak.

---

## KONUŞMACI 3 – FORMÜL SAYFASI
**2:00–3:00 · Slayt 5 · Net, anlaşılır, güvenilir**

Teşekkürler.

Bu sayfa, Zira'nın kendi icat ettiği bir model olmadığını gösteriyor. Dayanağımız FAO-56 standardı.

Önce Tarla Hafızası. Her sezonun, yani 1 Mart ile 30 Eylül arasının, en yüksek NDVI değerine bakıyoruz. NDVI, yakın kızılötesi ile kırmızı bandın farkının toplamına oranı. Değer 0,40 ve üzerindeyse sezon "ekili", altındaysa "nadas". Yeterince temiz görüntü yoksa uydurmuyoruz, "bilinmiyor" diyoruz.

Sonra Su Kasası. Günlük hesap yapıyoruz. Referans buharlaşma-terleme ET₀ formülüyle başlıyoruz. Bunu bitki katsayısıyla çarpıp bitkinin su talebi ETc'yi buluyoruz. Toprağın tutabildiği kullanılabilir su TAW, tarla kapasitesi ile solma noktası farkının kök derinliğiyle çarpımı. Her gün su deposu şu şekilde güncelleniyor: önceki depo, artı etkili yağış ve sulama, eksi gerçek buharlaşma-terleme, yüzey akışı ve derine sızma. Depo sıfırın altına inemez, TAW'ın üstüne çıkamaz.

Üçüncü olarak üç münavebe. A tarlanın doğrulanmış geçmişini tekrarlar. B, 1 Ekim'de depo TAW'ın yüzde 50'sinden fazlaysa eker. C, her ikinci nadas sezonuna baklagil koyar. Üçü de aynı hava, aynı toprak ve aynı başlangıç suyuyla çalışır.

Bir sezon, gerçek buharlaşma-terlemenin su talebine oranı 0,70 ve üzerindeyse "su yetti" sayılır.

Eşikleri şimdilik geçici olarak etiketliyoruz ve ziraat mühendisi onayıyla yerel değerlere taşıyoruz. Bunu da ekranda gösteriyoruz.

Sonuçlara arkadaşıma geçiyorum.

---

## KONUŞMACI 2 – ORTA (SERDAR), DEVAM
**3:00–4:05 · Slayt 6 · Kendinden emin, dürüst**

Teşekkürler.

Platformdaki örnek tarlada, 1 Ekim 2025 için kış buğdayında bitkinin yararlanabileceği su 202 milimetre. Aralık 154 ile 249 arası. Tek bir sayı vermiyoruz, çünkü tek sayı sahte bir kesinlik hissi yaratır.

Üç münavebeyi karşılaştırınca "su yetti" sezonları şöyle: A için 12'de 6, B için 7'de 6, C için 18'de 11. Yani yalnızca tek bir başarılı yıla değil, 24 tamamlanmış sezonun değişen koşullarına bakıyoruz. Veri 2001'den 2025'e uzanıyor.

Modelimizi bağımsız bir yere karşı da sınadık. Kulu çalışmasında su modelimiz NASA SMAP ve MERRA-2 toprak nemiyle 0,61 korelasyon gösterdi.

Sensör tarafı ise bir sonraki adımımız. Şu anki sensör gösterimimiz simüle edilmiş okumalara dayanıyor ve ekranda "simüle" olarak etiketli. Gerçek donanım aynı şemayla bağlanacak, sunucu kodu değişmeyecek. Örnek senaryoda model 231 milimetre derken sensör 140 milimetre gösteriyor. Aradaki farkı yan yana gösteriyoruz.

Son olarak şunu vurgulamak istiyorum: Hiçbir mesaj, ziraat mühendisi onayı olmadan çiftçiye ulaşmıyor. Karar günü, 20 milimetreyi aşan yağış ya da stres günü olduğunda taslak hazırlanıyor, mühendis onaylıyor, çiftçi WhatsApp'tan kısa bir mesaj alıyor.

Çünkü teknolojinin insan uzmanlığını ortadan kaldırmaması, güçlendirmesi gerektiğine inanıyoruz.

Kapanışı arkadaşıma bırakıyorum.

---

## KONUŞMACI 4 – KAPANIŞ
**4:05–5:00 · Slayt 7 · Samimi, ilham verici, güçlü**

Peki, Zira neden önemli?

Çünkü her tarlanın ardında bir aile var.

Her hasadın ardında bir yıllık emek var.

Ve her ekim kararının ardında bir sorumluluk var.

Havayı kontrol edemeyiz. Yer altı suyunu bir gecede artıramayız. Ama elimizdeki verilerle daha bilgili kararlar verebiliriz.

Sınırlarımızı da biliyoruz ve saklamıyoruz: Bitki evre uzunlukları ve eşikler geçici, ziraat mühendisi onayını bekliyor. Sensör verisi simülatörden geliyor. Landsat ve MODIS ekili ile nadası ayırıyor, ürün türünü değil. Bir sonraki adımımız, bir kooperatifin gerçek tarlaları, yerel kalibrasyon ve gerçek sensör donanımı.

Çünkü bilimde güvenilirlik, kendi sisteminin sınırlarını bilmekle başlar.

Vizyonumuz, kuşaklardan gelen tarım bilgisini modern teknolojinin gücüyle buluşturmak. Çiftçilerin topraklarını anlamasına, kaynaklarını korumasına ve gelecek için daha dirençli seçimler yapmasına yardım etmek.

Değerli jüri,

Biz çiftçiye nasıl çiftçilik yapacağını söylemek için teknoloji geliştirmiyoruz.

Onların tecrübesinin, bilgisinin ve kararlarının arkasında daha iyi bir bilgi olsun diye geliştiriyoruz.

Çünkü toprağı korurken, yalnızca bir hasadı korumuyoruz.

Kuşakları koruyoruz.

Bu, Zira.

Teşekkür ederiz.

---

## Notlar
- Toplam yaklaşık 700 kelime; sakin tempoda 5 dakikaya sığar. Sıkışırsanız Konuşmacı 2'nin NASA kaynakları paragrafını kısaltın.
- Konuşmacı 1'in "yer altı suyu çekiliyor" ifadesi için sayısal iddia (3,4 cm/yıl) ile GRACE'in bölgesel 0,46 cm/yıl değeri farklı şeyleri ölçer; konuşmada rakam vermedik, soru gelirse ayırın.
- "24 sezon" platformun tamamlanmış sezon sayısı, "25 sezon" kaydın uzunluğudur.
- Slayt 6'daki 202 mm (örnek tarla) ile 231 → 140 mm (sensör senaryosu) farklı koşullardan gelir; demo videosuyla uyumlu olduğunu kontrol edin.
- Kulu'daki 0,61 korelasyon doğrulama çalışmasına aittir, platform örnek tarlasına değil.
