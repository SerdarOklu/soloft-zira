# Zira: kaynakça (NASA ağırlıklı)

Beş bölüm: (A) NASA veri ürünleri, (B) bu ürünleri tanıtan hakemli makaleler, (C) yöntem, (D) bölgesel bağlam, (E) altyapı. Her kaynağın sonunda Zira'daki yeri yazılıdır: **[platformda]** doğrudan kullanılıyor, **[yöntem]** hesabın dayanağı, **[bağlam]** sorunu anlatmak için.

**Önemli:** Veri seti DOI'leri ve sürüm numaraları yayıncıların sayfalarından teyit edilmelidir; aşağıdakiler bildiğim en güncel biçimlerdir, ben bu oturumda çevrimiçi doğrulama yapmadım. DOI'yi sunumdan önce `https://doi.org/<doi>` adresinde açıp kontrol edin. Sürüm numarası depodaki ürün kimliğiyle (`config/data_sources.yaml`) eşleşmelidir. Emin olmadığım yerleri "[sürümü teyit edin]" diye işaretledim.

Slayta sığmaz; slaytta yalnızca en alttaki **Kısa liste** kullanılır, tamamı ek sayfada ya da README'de durur.

---

## A. NASA veri ürünleri

1. **NASA POWER.** NASA Langley Research Center (LaRC) POWER Project, Prediction Of Worldwide Energy Resources, Daily API v2. https://power.larc.nasa.gov/ **[platformda]** Günlük hava verisi (2001–2025). Zorunlu atıf: *"Bu veriler NASA Langley Araştırma Merkezi (LaRC) POWER Projesi'nden alınmıştır; proje NASA Earth Science/Applied Science Program tarafından finanse edilmektedir."*
2. **MOD13Q1.** Didan, K. (2021). *MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061.* NASA EOSDIS Land Processes DAAC. https://doi.org/10.5067/MODIS/MOD13Q1.061 **[platformda]**
3. **MYD13Q1.** Didan, K. (2021). *MODIS/Aqua Vegetation Indices 16-Day L3 Global 250m SIN Grid V061.* NASA EOSDIS Land Processes DAAC. https://doi.org/10.5067/MODIS/MYD13Q1.061 **[platformda]**
4. **Landsat 8 ve 9, Collection 2 Seviye-2.** U.S. Geological Survey (2020). *Landsat 8–9 Operational Land Imager / Thermal Infrared Sensor Level-2, Collection 2.* USGS EROS. https://doi.org/10.5066/P9OGBGM6 **[platformda]** (NASA/USGS ortak programı; [sürümü teyit edin])
5. **NASADEM (SRTM).** NASA JPL (2020). *NASADEM Merged DEM Global 1 arc second V001.* NASA EOSDIS Land Processes DAAC. https://doi.org/10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001 **[platformda]** Rakım ve eğim.
6. **SMAP, 9 km günlük toprak nemi.** O'Neill, P. E., Chan, S., Njoku, E. G., Jackson, T., Bindlish, R., Chaubell, J. *SMAP Enhanced L3 Radiometer Global and Polar Grid Daily 9 km EASE-Grid Soil Moisture (SPL3SMP_E).* NASA National Snow and Ice Data Center DAAC. [sürüm ve DOI için NSIDC ürün sayfasına bakın] **[platformda, bölgesel çapraz kontrol]**
7. **GPM IMERG, günlük, Final.** Huffman, G. J., Stocker, E. F., Bolvin, D. T., Nelkin, E. J., Tan, J. *GPM IMERG Final Precipitation L3 1 day 0.1 degree x 0.1 degree (GPM_3IMERGDF).* NASA Goddard Earth Sciences Data and Information Services Center (GES DISC). [sürümü teyit edin; DOI biçimi: 10.5067/GPM/IMERGDF/DAY/<sürüm>] **[platformda, çapraz kontrol]** Eylül 2025 sonrası için Late run (GPM_3IMERGDL) kullanılır; bunu da belirtin.
8. **GRACE ve GRACE-FO mascon.** NASA JPL. *JPL GRACE and GRACE-FO Mascon Ocean, Ice, and Hydrology Equivalent Water Height, CRI Filtered, RL06.3 (Version 04).* NASA Physical Oceanography DAAC (PO.DAAC). Ürün kimliği: `TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4`. [DOI için PO.DAAC sayfasına bakın] **[platformda, bölgesel eğilim]**
9. **NASA GIBS.** NASA Global Imagery Browse Services, NASA ESDIS Project'in parçası. https://earthdata.nasa.gov/gibs **[bağlam]** Önizleme görüntüleri; doğrulama çalışmasında eğilim kontrolü için kullanıldı. Atıf: *"Bu çalışma, NASA'nın Earth Science Data and Information System (ESDIS) projesinin parçası olan Global Imagery Browse Services (GIBS) tarafından sunulan görüntüleri kullanmıştır."*
10. **NASA Earthdata.** NASA Earthdata, https://www.earthdata.nasa.gov/ **[platformda]** SMAP, GPM ve GRACE dosyalarının oturum açılarak okunduğu ortak giriş. Jeton sunucuda tutulur.
11. **ECOSTRESS.** NASA JPL. ECOSTRESS evapotranspirasyon ve su stresi ürünleri, NASA LP DAAC. **[bağlam]** Zira'da bağlı değildir; yalnızca sonraki adım olarak anılır.

## B. Mission ve ürün makaleleri (NASA verisinin bilimsel dayanağı)

12. Entekhabi, D., ve ark. (2010). The Soil Moisture Active Passive (SMAP) Mission. *Proceedings of the IEEE*, 98(5), 704–716. https://doi.org/10.1109/JPROC.2010.2043918 **[bağlam]**
13. Hou, A. Y., ve ark. (2014). The Global Precipitation Measurement Mission. *Bulletin of the American Meteorological Society*, 95(5), 701–722. https://doi.org/10.1175/BAMS-D-13-00164.1 **[bağlam]**
14. Tapley, B. D., Bettadpur, S., Ries, J. C., Thompson, P. F., Watkins, M. M. (2004). GRACE measurements of mass variability in the Earth system. *Science*, 305(5683), 503–505. https://doi.org/10.1126/science.1099192 **[bağlam]**
15. Landerer, F. W., ve ark. (2020). Extending the global mass change data record: GRACE Follow-On instrument and science data performance. *Geophysical Research Letters*, 47, e2020GL088306. https://doi.org/10.1029/2020GL088306 **[bağlam]**
16. Watkins, M. M., Wiese, D. N., Yuan, D.-N., Boening, C., Landerer, F. W. (2015). Improved methods for observing Earth's time variable mass distribution with GRACE using spherical cap mascons. *Journal of Geophysical Research: Solid Earth*, 120, 2648–2671. https://doi.org/10.1002/2014JB011547 **[bağlam]**
17. Rodell, M., ve ark. (2018). Emerging trends in global freshwater availability. *Nature*, 557, 651–659. https://doi.org/10.1038/s41586-018-0123-1 **[bağlam]**
18. Roy, D. P., ve ark. (2014). Landsat-8: Science and product vision for terrestrial global change research. *Remote Sensing of Environment*, 145, 154–172. https://doi.org/10.1016/j.rse.2014.02.001 **[bağlam]**
19. Masek, J. G., ve ark. (2020). Landsat 9: Empowering open science and applications through continuity. *Remote Sensing of Environment*, 248, 111968. https://doi.org/10.1016/j.rse.2020.111968 **[bağlam]**
20. Vermote, E., Justice, C., Claverie, M., Franch, B. (2016). Preliminary analysis of the performance of the Landsat 8/OLI land surface reflectance product. *Remote Sensing of Environment*, 185, 46–56. https://doi.org/10.1016/j.rse.2016.04.008 **[yöntem]** Yüzey yansıması dönüşümünün dayanağı.
21. Huete, A., ve ark. (2002). Overview of the radiometric and biophysical performance of the MODIS vegetation indices. *Remote Sensing of Environment*, 83, 195–213. https://doi.org/10.1016/S0034-4257(02)00096-2 **[yöntem]**
22. Farr, T. G., ve ark. (2007). The Shuttle Radar Topography Mission. *Reviews of Geophysics*, 45, RG2004. https://doi.org/10.1029/2005RG000183 **[bağlam]**
23. Fisher, J. B., ve ark. (2020). ECOSTRESS: NASA's next generation mission to measure evapotranspiration from the International Space Station. *Water Resources Research*, 56, e2019WR026058. https://doi.org/10.1029/2019WR026058 **[bağlam]**
24. Gelaro, R., ve ark. (2017). The Modern-Era Retrospective Analysis for Research and Applications, Version 2 (MERRA-2). *Journal of Climate*, 30, 5419–5454. https://doi.org/10.1175/JCLI-D-16-0758.1 **[bağlam]** Kulu doğrulama çalışmasındaki MERRA-2 karşılaştırması.
25. Rodell, M., ve ark. (2004). The Global Land Data Assimilation System. *Bulletin of the American Meteorological Society*, 85, 381–394. https://doi.org/10.1175/BAMS-85-3-381 **[bağlam]**
26. Tucker, C. J. (1979). Red and photographic infrared linear combinations for monitoring vegetation. *Remote Sensing of Environment*, 8, 127–150. https://doi.org/10.1016/0034-4257(79)90013-0 **[yöntem]** NDVI.

## C. Su dengesi ve ürün su kullanımı (yöntem)

27. Allen, R. G., Pereira, L. S., Raes, D., Smith, M. (1998). *Crop evapotranspiration: guidelines for computing crop water requirements.* FAO Irrigation and Drainage Paper 56. Roma: FAO. https://www.fao.org/4/x0490e/x0490e00.htm **[yöntem]** ET₀ (Penman–Monteith), Kc eğrisi, TAW/RAW, Ks, Tablo 11, 12, 19 ve 22.
28. Doorenbos, J., Kassam, A. H. (1979). *Yield response to water.* FAO Irrigation and Drainage Paper 33. Roma: FAO. **[yöntem]** Göreli verim kuralı (Kulu doğrulama çalışması).

## D. Bölgesel bağlam

29. Khorrami, B., Arık, F., Gündüz, O. (2021). Land deformation and sinkhole occurrence in response to the fluctuations of groundwater storage. *GIScience & Remote Sensing*, 58(8), 1518–1542. https://doi.org/10.1080/15481603.2021.2000349 **[bağlam]** 3,4 cm/yıl yeraltı suyu kaybı ve obruk ilişkisi.
30. NTV / İHA (17 Ağustos 2026). *Konya Ovası'nda alarm: sayı 740'ı aştı.* https://www.ntv.com.tr/yerel-haberler/galerikonya-ovasinda-alarm-sayi-740i-asti-1737722 **[bağlam]** Konya Teknik Üniversitesi Obruk Araştırma Merkezi açıklaması.

## E. Altyapı

31. Microsoft Planetary Computer, açık STAC kataloğu. https://planetarycomputer.microsoft.com/ **[platformda]** Landsat, MODIS ve NASADEM, hesap gerektirmeden bu katalogdan okunur. Veriyi üreten NASA/USGS'tir; katalog yalnızca barındırır.
32. NASA Common Metadata Repository (CMR). https://cmr.earthdata.nasa.gov/ **[platformda]** SMAP, IMERG ve GRACE dosyalarının bulunduğu arama servisi.

---

## Kısa liste (slayta konacak, 8 kaynak)

1. NASA LaRC POWER Project, Daily API v2. https://power.larc.nasa.gov/
2. Didan, K. (2021). MOD13Q1 / MYD13Q1 V061. NASA LP DAAC. doi:10.5067/MODIS/MOD13Q1.061
3. USGS/NASA (2020). Landsat 8–9 Collection 2 Level-2. doi:10.5066/P9OGBGM6
4. NASA JPL (2020). NASADEM V001. NASA LP DAAC. doi:10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001
5. NASA NSIDC SMAP SPL3SMP_E · NASA GES DISC GPM IMERG · NASA PO.DAAC GRACE-FO Mascon RL06.3
6. Allen ve ark. (1998). FAO Irrigation and Drainage Paper 56.
7. Khorrami, Arık ve Gündüz (2021). GIScience & Remote Sensing 58(8).
8. NASA GIBS / ESDIS; Microsoft Planetary Computer (barındırma)

## Atıf cümleleri (slayt altına ya da README'ye)

- **TR:** "Hava verisi NASA Langley Araştırma Merkezi (LaRC) POWER Projesi'nden alınmıştır; proje NASA Earth Science/Applied Science Program tarafından finanse edilmektedir. MODIS, Landsat, NASADEM, SMAP, GPM IMERG ve GRACE-FO verileri NASA Earthdata ve USGS üzerinden, ilgili veri merkezlerinin (LP DAAC, NSIDC DAAC, GES DISC, PO.DAAC) ürünleri olarak kullanılmıştır. Görüntüler NASA GIBS (ESDIS) aracılığıyla sunulmuştur."
- **EN:** "Weather data were obtained from the NASA Langley Research Center (LaRC) POWER Project, funded through the NASA Earth Science/Applied Science Program. MODIS, Landsat, NASADEM, SMAP, GPM IMERG and GRACE-FO data were used through NASA Earthdata and USGS, as products of the LP DAAC, NSIDC DAAC, GES DISC and PO.DAAC. Imagery was provided through NASA GIBS, part of NASA ESDIS."

## Atıf yaparken dikkat

- Kendi çalışmanızda GRACE'i parsel ölçeğinde yorumlamadığınızı, SMAP'ın yalnızca üst 5 cm'yi gördüğünü ve MODIS pikselinin yaklaşık 6 ha olduğunu belirten cümleleri kaynakçanın yanında tutun; jüri ölçek hatasını ilk orada arar.
- NASA logosunu ya da "NASA onaylı" gibi bir ifadeyi kullanmayın; NASA verisi kullandığınızı söylemek yeterlidir.
- Earthdata kaynaklı üç ürün jeton süresi dolduğunda canlı platformda "bağlı değil" görünür; sunum günü ekranla slaytı çelişkiye düşürmemek için jetonu önceden yenileyin.
