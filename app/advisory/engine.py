"""
Empirical Agronomic Advisory Engine.
Generates localized, stage-gated adaptation advisories grounded in
ICAR-NICRA, IRRI, and IPCC AR6 field-trial benchmarks.
Languages supported:
- en: English
- hi: Hindi (हिन्दी)
- ta: Tamil (தமிழ்)
- bn: Bengali (বাংলা)
- pa: Punjabi (ਪੰਜਾਬੀ)
- te: Telugu (తెలుగు)
"""
from typing import Dict, Any, List, Optional


SOLUTIONS_DB = {
    "safe_awd": {
        "id": "safe_awd",
        "category": "drought",
        "evidence_source": "IRRI & ICAR-CRRI Field Trials (2018-2023)",
        "benefit": "Conserves 15-20% irrigation water without yield penalty (IRRI & ICAR-CRRI trials)",
        "translations": {
            "en": {
                "title": "Safe Alternate Wetting and Drying (Safe AWD)",
                "action": "Install a 30 cm perforated plastic or bamboo 'pani pipe' (field water tube) 15 cm below soil surface. Only irrigate when the water table inside the tube drops to 15 cm below soil level.",
                "note": "During flowering/heading, maintain 2-5 cm continuous ponding to protect pollen viability."
            },
            "hi": {
                "title": "सुरक्षित गीला-सूखा सिंचाई (Safe AWD / पानी पाइप)",
                "action": "खेत में 30 सेमी लंबा छिद्रित प्लास्टिक या बांस का 'पानी पाइप' जमीन में 15 सेमी गहराई तक गाड़ें। जब पाइप में पानी का स्तर 15 सेमी नीचे चला जाए, तभी दोबारा पानी दें।",
                "note": "फूल आने (बाली निकलने) के समय खेत में 2-5 सेमी पानी लगातार बनाए रखें।"
            },
            "ta": {
                "title": "பாதுகாப்பான மாறி மாறி நனைத்து உலர்த்தும் முறை (Safe AWD)",
                "action": "வயலில் 30 செ.மீ துளையிடப்பட்ட பிளாஸ்டிக் அல்லது மூங்கில் குழாயை 15 செ.மீ ஆழத்தில் வைக்கவும். குழாயில் நீர்மட்டம் 15 செ.மீ கீழே குறையும் போது மட்டும் அடுத்த பாசனம் செய்யவும்.",
                "note": "பூக்கும் தருணத்தில் பயிருக்கு நீர் பற்றாக்குறை ஏற்படாமல் 2-5 செ.மீ நீர் தேங்குவதை உறுதிசெய்யவும்."
            },
            "bn": {
                "title": "পর্যায়ক্রমিক ভেজানো ও শুকানো পদ্ধতি (Safe AWD)",
                "action": "জমিতে ৩০ সেমি ছিদ্রযুক্ত প্লাস্টিক বা বাঁশের 'পানি পাইপ' ১৫ সেমি মাটির নিচে স্থাপন করুন। পাইপের পানি ১৫ সেমি নিচে নেমে গেলে তবেই পরবর্তী সেচ দিন।",
                "note": "ফুল ফোটার সময় জমিতে ২-৫ সেমি পানি ধরে রাখুন।"
            },
            "pa": {
                "title": "ਸੁਰੱਖਿਅਤ ਪਾਣੀ ਪਾਈਪ ਸਿੰਚਾਈ (Safe AWD)",
                "action": "ਖੇਤ ਵਿੱਚ 30 ਸੈਂਟੀਮੀਟਰ ਦਾ ਛੇਕਾਂ ਵਾਲਾ ਪਾਈਪ 15 ਸੈਂਟੀਮੀਟਰ ਧਰਤੀ ਵਿੱਚ ਗੱਡੋ। ਜਦੋਂ ਪਾਈਪ ਵਿੱਚ ਪਾਣੀ ਦਾ ਪੱਧਰ 15 ਸੈਂਟੀਮੀਟਰ ਹੇਠਾਂ ਚਲਾ ਜਾਵੇ, ਤਦ ਹੀ ਸਿੰਚਾਈ ਕਰੋ।",
                "note": "ਫੁੱਲ ਆਉਣ ਸਮੇਂ ਖੇਤ ਵਿੱਚ 2-5 ਸੈਂਟੀਮੀਟਰ ਪਾਣੀ ਖੜ੍ਹਾ ਰੱਖੋ।"
            },
            "te": {
                "title": "సురక్షిత తడి-పొడి సాగు విధానం (Safe AWD)",
                "action": "పొలంలో 30 సెం.మీ రంధ్రాలున్న ప్లాస్టిక్ లేదా వెదురు పైపును 15 సెం.మీ లోతులో అమర్చండి. పైపులో నీటి మట్టం 15 సెం.మీ దిగువకు పడిపోయినప్పుడు మాత్రమే నీరు పెట్టండి.",
                "note": "పూత దశలో 2-5 సెం.మీ నీరు నిల్వ ఉండేలా చూసుకోండి."
            }
        }
    },
    "drought_varieties_rice": {
        "id": "drought_varieties_rice",
        "category": "drought",
        "evidence_source": "ICAR-NRRI & IRRI South Asia Variety Release Trials",
        "benefit": "+0.8 to 1.0 t/ha yield resilience under water stress (Sahbhagi Dhan, IRRI trials)",
        "translations": {
            "en": {
                "title": "Drought-Tolerant Rice Cultivars (Sahbhagi Dhan / DRR 42 / CR Dhan 201)",
                "action": "For upcoming seasons facing delayed monsoons or canal deficits, deploy certified seeds of Sahbhagi Dhan or DRR Dhan 42. These cultivars mature in 105-115 days and sustain grain-filling under moisture stress.",
                "note": "Seed treatment with Trichoderma (5g/kg) enhances root development and drought resilience."
            },
            "hi": {
                "title": "सूखा-सहनशील धान की किस्में (सहभागी धान / DRR 42 / CR धान 201)",
                "action": "पानी की कमी वाले क्षेत्रों के लिए सहभागी धान या DRR 42 का प्रमाणित बीज उपयोग करें। ये किस्में 105-115 दिनों में पकती हैं और कम पानी में भी सामान्य उत्पादन देती हैं।",
                "note": "ट्राइकोडर्मा (5 ग्राम/किग्रा) से बीज उपचार करने पर जड़ें गहरी जाती हैं और सूखा सहने की क्षमता बढ़ती है।"
            },
            "ta": {
                "title": "வறட்சியைத் தாங்கும் நெல் ரகங்கள் (சகபாகி தான் / DRR 42)",
                "action": "நீர் தட்டுப்பாடு உள்ள பகுதிகளில் சகபாகி தான் அல்லது DRR 42 போன்ற வறட்சியைத் தாங்கும் குறுகிய கால (105-115 நாட்கள்) சான்றளிக்கப்பட்ட விதைகளைப் பயன்படுத்தவும்.",
                "note": "விதைகளை டிரைக்கோடெர்மா மூலம் நேர்த்தி செய்வதால் வேர் வளர்ச்சி தூண்டப்பட்டு வறட்சியைத் தாங்கும்."
            },
            "bn": {
                "title": "খরা-সহনশীল ধানের জাত (সহভাগী ধান / ব্রি ধান ৫৬/৭১)",
                "action": "পানির সংকট প্রবণ এলাকায় খরা-সহনশীল জাত যেমন ব্রি ধান ৫৬ বা সহভাগী ধান চাষ করুন। এগুলো ১০৫-১১৫ দিনে পাকে এবং খরার মধ্যেও ফলন বজায় রাখে।",
                "note": "ট্রাইকোডার্মা দিয়ে বীজ শোধন করলে শিকড় গভীর হয় এবং খরা সহনশীলতা বৃদ্ধি পায়।"
            },
            "pa": {
                "title": "ਸੋਕਾ-ਸਹਿਣਸ਼ੀਲ ਝੋਨੇ ਦੀਆਂ ਕਿਸਮਾਂ (ਸਹਿਭਾਗੀ ਧਾਨ / DRR 42)",
                "action": "ਪਾਣੀ ਦੀ ਘਾਟ ਵਾਲੇ ਇਲਾਕਿਆਂ ਲਈ ਸਹਿਭਾਗੀ ਧਾਨ ਜਾਂ DRR 42 ਵਰਗੀਆਂ ਘੱਟ ਸਮੇਂ ਵਾਲੀਆਂ ਕਿਸਮਾਂ ਬੀਜੋ ਜੋ 105-115 ਦਿਨਾਂ ਵਿੱਚ ਪੱਕਦੀਆਂ ਹਨ।",
                "note": "ਟ੍ਰਾਈਕੋਡਰਮਾ ਨਾਲ ਬੀਜ ਸੋਧ ਕਰਨ ਨਾਲ ਜੜ੍ਹਾਂ ਮਜ਼ਬੂਤ ਹੁੰਦੀਆਂ ਹਨ।"
            },
            "te": {
                "title": "కరువును తట్టుకునే వరి రకాలు (సహభాగి ధాన్ / DRR 42)",
                "action": "నీటి కొరత ఉన్న ప్రాంతాల్లో సహభాగి ధాన్ లేదా DRR 42 వంటి కరువు తట్టుకునే రకాలను సాగు చేయండి. ఇవి 105-115 రోజుల్లో కోతకు వస్తాయి.",
                "note": "ట్రైకోడెర్మతో విత్తన శుద్ధి చేయడం ద్వారా వేరు వ్యవస్థ బలంగా మారి కరువును తట్టుకుంటుంది."
            }
        }
    },
    "submergence_rice": {
        "id": "submergence_rice",
        "category": "flood",
        "evidence_source": "IRRI Sub1 Gene Field Documentation (ICAR-CRRI)",
        "benefit": "Withstands 14 days of complete underwater submergence with +1.0 to 3.0 t/ha yield recovery (IRRI SUB1 trials)",
        "translations": {
            "en": {
                "title": "Submergence-Tolerant Rice (Swarna-Sub1 / Sambha Mahsuri-Sub1)",
                "action": "In flood-prone lowlands and cyclone-affected coastal deltas, adopt Swarna-Sub1 or BINA dhan-11. These varieties carry the SUB1A dormancy gene, halting elongation underwater and reviving upon water recession.",
                "note": "Ensure drainage channels are cleared before peak monsoon storms to prevent waterlogging beyond 14 days."
            },
            "hi": {
                "title": "बाढ़-सहनशील धान (स्वर्णा-सब1 / साम्भा महसूरी-सब1)",
                "action": "जलभराव और बाढ़ प्रभावित क्षेत्रों में 'स्वर्णा-सब1' किस्म लगाएं। यह धान 14 दिनों तक पानी में पूरी तरह डूबे रहने के बाद भी खराब नहीं होता और पानी उतरने पर पुनः बढ़वार शुरू कर देता है।",
                "note": "मानसून पूर्व जल निकासी की नालियों को साफ रखें।"
            },
            "ta": {
                "title": "வெள்ளத்தைத் தாங்கும் நெல் ரகம் (ஸ்வர்ணா-சப்1)",
                "action": "வெள்ளம் மற்றும் அதிக மழை வாய்ப்புள்ள டெல்டா பகுதிகளில் 'ஸ்வர்ணா-சப்1' ரகத்தை நடவு செய்யவும். இது 14 நாட்கள் வரை முழுமையாக நீரில் மூழ்கியிருந்தாலும் அழுகாமல் உயிர்வாழும்.",
                "note": "களத்தில் நீர் தேங்காமல் இருக்க வடிகால் வாய்க்கால்களை தூர்வாரவும்."
            },
            "bn": {
                "title": "বন্যা ও জলমগ্নতা সহনশীল ধান (স্বর্ণা-সাব১ / বিনা ধান-১১)",
                "action": "বন্যাপ্রবণ নিচু জমিতে স্বর্ণা-সাব১ বা বিনা ধান-১১ চাষ করুন। এই জাতগুলো পানির নিচে ১৪ দিন সম্পূর্ণ নিমজ্জিত থাকলেও নষ্ট হয় না এবং পানি কমলে দ্রুত বাড়ে।",
                "note": "পানি দ্রুত নিষ্কাশনের জন্য নিকাশি নালাগুলো পরিষ্কার রাখুন।"
            },
            "pa": {
                "title": "ਹੜ੍ਹ-ਸਹਿਣਸ਼ੀਲ ਝੋਨਾ (ਸਵਰਨਾ-ਸਬ1)",
                "action": "ਹੜ੍ਹਾਂ ਜਾਂ ਜ਼ਿਆਦਾ ਪਾਣੀ ਵਾਲੇ ਇਲਾਕਿਆਂ ਵਿੱਚ ਸਵਰਨਾ-ਸਬ1 ਲਗਾਓ। ਇਹ ਕਿਸਮ 14 ਦਿਨਾਂ ਤੱਕ ਪਾਣੀ ਵਿੱਚ ਡੁੱਬੀ ਰਹਿਣ ਦੇ ਬਾਵਜੂਦ ਬਚੀ ਰਹਿੰਦੀ ਹੈ।",
                "note": "ਬਰਸਾਤ ਤੋਂ ਪਹਿਲਾਂ ਪਾਣੀ ਦੇ ਨਿਕਾਸ ਵਾਲੀਆਂ ਨਾਲੀਆਂ ਸਾਫ਼ ਕਰੋ।"
            },
            "te": {
                "title": "ముంపును తట్టుకునే వరి (స్వర్ణ-సబ్1)",
                "action": "వరదలు మరియు నీరు నిల్వ ఉండే ప్రాంతాల్లో స్వర్ణ-సబ్1 రకాన్ని సాగు చేయండి. ఇది 14 రోజుల పాటు నీటిలో మునిగి ఉన్నా తట్టుకుని తిరిగి పెరుగుతుంది.",
                "note": "మురుగు నీరు త్వరగా బయటకు వెళ్లడానికి డ్రైనేజీ కాలువలను శుభ్రం చేసుకోండి."
            }
        }
    },
    "terminal_heat_wheat": {
        "id": "terminal_heat_wheat",
        "category": "heat",
        "evidence_source": "ICAR-IIWBR Karnal Terminal Heat Shock Benchmarks (2022-2024)",
        "benefit": "Protects against pollen sterility and test weight shriveling during March heat spikes",
        "translations": {
            "en": {
                "title": "Terminal Heat Resilient Wheat (HD 3385 / PBW 826 / DBW 187)",
                "action": "Sow heat-tolerant varieties HD 3385 or PBW 826 in late October / early November. When forecast maximum temperatures exceed 31°C during flowering/grain-fill, provide light evening irrigation or micro-sprinkler misting to cool the canopy.",
                "note": "Timely or early sowing aligns the sensitive anthesis phase with cooler February temperatures, avoiding March heat shock."
            },
            "hi": {
                "title": "गर्मी-रोधी गेहूं किस्में एवं प्रबंधन (HD 3385 / PBW 826 / DBW 187)",
                "action": "मार्च की गर्मी से बचने के लिए HD 3385 या PBW 826 किस्म की समय पर (अक्टूबर अंत से 15 नवंबर) बुवाई करें। बाली निकलने के समय यदि तापमान 31°C से ऊपर जाए तो शाम के समय हल्की सिंचाई या फव्वारा चलाएं।",
                "note": "समय पर या अगेती बुवाई से फूल आने की संवेदनशील अवस्था मार्च की लू से पहले पूरी हो जाती है।"
            },
            "ta": {
                "title": "வெப்பத்தைத் தாங்கும் கோதுமை மற்றும் மேலாண்மை (HD 3385 / DBW 187)",
                "action": "வெப்பத்தைத் தாங்கும் HD 3385 ரகத்தை சரியான நேரத்தில் விதைக்கவும். பூக்கும் தருணத்தில் அதிக வெப்பநிலை இருந்தால் மாலையில் லேசான பாசனம் வழங்கி பயிரை குளிர்விக்கவும்.",
                "note": "முன்கூட்டியே விதைப்பதன் மூலம் மார்ச் மாத கடும் வெப்பத்தின் தாக்கத்தைத் தவிர்க்கலாம்."
            },
            "bn": {
                "title": "তাপ-সহনশীল গম চাষ ও পরিচর্যা (HD 3385 / DBW 187)",
                "action": "মার্চের তীব্র তাপপ্রবাহ থেকে বাঁচতে HD 3385 বা বারি গম ৩৩ সময়মতো বপন করুন। ফুল ফোটার সময় তাপমাত্রা বাড়লে বিকেলে হালকা সেচ দিন।",
                "note": "আগাম বপন করলে শীষ বের হওয়ার সময় উচ্চ তাপমাত্রার ক্ষতি এড়ানো সম্ভব।"
            },
            "pa": {
                "title": "ਗਰਮੀ-ਸਹਿਣਸ਼ੀਲ ਕਣਕ ਅਤੇ ਪ੍ਰਬੰਧਨ (PBW 826 / HD 3385 / DBW 187)",
                "action": "ਮਾਰਚ ਦੀ ਗਰਮੀ ਤੋਂ ਬਚਣ ਲਈ ਪੀਬੀਡਬਲਿਊ 826 ਜਾਂ ਐਚਡੀ 3385 ਦੀ ਬਿਜਾਈ 15 ਨਵੰਬਰ ਤੱਕ ਮੁਕੰਮਲ ਕਰੋ। ਦਾਣਾ ਬਣਨ ਸਮੇਂ ਜੇ ਤਾਪਮਾਨ 31°C ਤੋਂ ਵਧੇ ਤਾਂ ਸ਼ਾਮ ਨੂੰ ਹਲਕਾ ਪਾਣੀ ਲਗਾਓ ਜਾਂ ਫੁਹਾਰਾ ਚਲਾਓ।",
                "note": "ਸਮੇਂ ਸਿਰ ਜਾਂ ਅਗੇਤੀ ਬਿਜਾਈ ਮਾਰਚ ਦੀ ਲੂ ਤੋਂ ਫਸਲ ਦਾ ਬਚਾਅ ਕਰਦੀ ਹੈ।"
            },
            "te": {
                "title": "ఎండ తీవ్రతను తట్టుకునే గోధుమ రకాలు (HD 3385 / DBW 187)",
                "action": "మార్చి నెలలో వచ్చే వడగాల్పుల నుంచి రక్షణకు HD 3385 రకాన్ని సమయానికి విత్తుకోండి. పూత దశలో ఉష్ణోగ్రత పెరిగినప్పుడు సాయంత్రం వేళల్లో తేలికపాటి తడులు ఇవ్వండి.",
                "note": "ముందస్తు విత్తడం ద్వారా మార్చి నెల ఎండల వల్ల వచ్చే నష్టాన్ని తగ్గించవచ్చు."
            }
        }
    },
    "crop_residue_mulch": {
        "id": "crop_residue_mulch",
        "category": "moisture_conservation",
        "evidence_source": "ICAR-CSSRI & CIMMYT Conservation Agriculture Benchmarks",
        "benefit": "Conserves soil moisture and suppresses weeds in zero-till seedbed (ICAR-CSSRI & CIMMYT)",
        "translations": {
            "en": {
                "title": "In-Situ Crop Residue Mulching (Happy Seeder / Surface Retained Mulch)",
                "action": "Retain paddy straw residue on field surface using Happy Seeder / Super Seeder. Mulch blanket protects soil moisture and suppresses weed emergence.",
                "note": "Avoid burning crop stubble; surface retention builds organic carbon and improves soil structure."
            },
            "hi": {
                "title": "फसल अवशेष मल्चिंग (हैप्पी सीडर / पराली आवरण)",
                "action": "हैप्पी सीडर या सुपर सीडर से पराली को खेत में फैलाकर बिना जुताई गेहूं की बुवाई करें। पराली का आवरण मिट्टी की नमी को उड़ने से रोकता है और खरपतवार दबाता है।",
                "note": "पराली कभी न जलाएं; यह जमीन में जैविक कार्बन और जल धारण क्षमता बढ़ाती है।"
            },
            "ta": {
                "title": "பயிர் கழிவு மூடாக்கு முறை (Mulching)",
                "action": "முந்தைய பயிரின் வைக்கோல் அல்லது கழிவுகளை நிலத்தின் மேல் மூடாக்காக பரப்பவும். இது மண்ணின் ஈரப்பதத்தை பாதுகாத்து களைகளைக் கட்டுப்படுத்தும்.",
                "note": "பயிர் கழிவுகளை எரிக்க வேண்டாம்; அவை மண்ணின் நீர்பிடிப்பு திறனை அதிகரிக்கும்."
            },
            "bn": {
                "title": "ফসলের অবশিষ্টাংশের জাবড়া প্রয়োগ (Mulching)",
                "action": "জমির ওপর খড় বা ফসলের অবশিষ্টাংশ বিছিয়ে দিন। এটি মাটির আর্দ্রতা ধরে রাখে এবং আগাছা জন্মাতে বাধা দেয়।",
                "note": "ফসলের অবশিষ্টাংশ পোড়াবেন না; এটি মাটির জৈব পদার্থ ও পানি ধারণ ক্ষমতা বাড়ায়।"
            },
            "pa": {
                "title": "ਪਰਾਲੀ ਦੀ ਸਾਂਭ-ਸੰਭਾਲ ਅਤੇ ਮਲਚਿੰਗ (ਹੈਪੀ ਸੀਡਰ / ਸੁਪਰ ਸੀਡਰ)",
                "action": "ਹੈਪੀ ਸੀਡਰ ਜਾਂ ਸੁਪਰ ਸੀਡਰ ਦੀ ਵਰਤੋਂ ਕਰਕੇ ਪਰਾਲੀ ਨੂੰ ਖੇਤ ਵਿੱਚ ਹੀ ਰੱਖ ਕੇ ਕਣਕ ਬੀਜੋ। ਪਰਾਲੀ ਦੀ ਤਹਿ ਜ਼ਮੀਨ ਦੀ ਸਿਲ੍ਹ ਬਚਾਉਂਦੀ ਹੈ ਅਤੇ ਨਦੀਨਾਂ ਨੂੰ ਰੋਕਦੀ ਹੈ।",
                "note": "ਪਰਾਲੀ ਨੂੰ ਅੱਗ ਨਾ ਲਗਾਓ; ਇਹ ਜ਼ਮੀਨ ਵਿੱਚ ਜੈਵਿਕ ਮਾਦਾ ਅਤੇ ਪਾਣੀ ਜਜ਼ਬ ਕਰਨ ਦੀ ਸ਼ਕਤੀ ਵਧਾਉਂਦੀ ਹੈ।"
            },
            "te": {
                "title": "వ్యర్థాలతో ఆచ్ఛాదన (మల్చింగ్ పద్ధతి)",
                "action": "వరి గడ్డి లేదా పంట వ్యర్థాలను పొలంలో మల్చింగ్‌గా పరచండి. ఇది నేలలో తేమను సంరక్షిస్తుంది మరియు కలుపును అణిచివేస్తుంది.",
                "note": "వ్యర్థాలను తగులబెట్టవద్దు; ఇది భూమిలో సేంద్రీయ కర్బనాన్ని పెంచుతుంది."
            }
        }
    },
    "direct_seeded_rice": {
        "id": "direct_seeded_rice",
        "category": "groundwater",
        "evidence_source": "Punjab Agricultural University (PAU) & IRRI Direct Seeding Guidelines",
        "benefit": "Saves 20-25% groundwater irrigation and cuts labor costs by avoiding puddling",
        "translations": {
            "en": {
                "title": "Direct Seeded Rice (DSR / Tar-Wattar Method)",
                "action": "In groundwater-depleted aquifers (GRACE trend negative), shift from puddled transplantation to DSR using Tar-Wattar drill in pre-conditioned moist soil (first fortnight of June).",
                "note": "Apply pendimethalin (30 EC) pre-emergence herbicide within 24 hours of sowing to control early weeds."
            },
            "hi": {
                "title": "सीधी बिजाई धान (DSR / तर-वत्तर विधि)",
                "action": "गिरते भूजल स्तर वाले क्षेत्रों में कद्दू करके धान लगाने के बजाय 'तर-वत्तर' विधि से धान की सीधी बिजाई करें। इससे 20-25% पानी की बचत होती है।",
                "note": "खरपतवार नियंत्रण हेतु बुवाई के 24 घंटे के भीतर पेंडीमेथालिन का छिड़काव करें।"
            },
            "ta": {
                "title": "நேரடி நெல் விதைப்பு முறை (DSR)",
                "action": "நிலத்தடி நீர்மட்டம் குறைந்துள்ள பகுதிகளில் சேற்று நடவுக்குப் பதிலாக நேரடி நெல் விதைப்பு முறையைப் பின்பற்றவும். இது 20-25% பாசன நீரை மிச்சப்படுத்தும்.",
                "note": "களைகளைக் கட்டுப்படுத்த விதைத்த 24 மணி நேரத்திற்குள் உரிய களைக்கொல்லியைப் பயன்படுத்தவும்."
            },
            "bn": {
                "title": "সরাসরি ধান বপন পদ্ধতি (DSR)",
                "action": "ভূগর্ভস্থ পানির স্তর রক্ষার্থে কাদা না করে সরাসরি বীজ বপন (DSR) পদ্ধতি গ্রহণ করুন। এতে ২০-২৫% সেচের পানি সাশ্রয় হয়।",
                "note": "আগাছা দমনের জন্য বীজ বপনের ২৪ ঘণ্টার মধ্যে আগাছানাশক প্রয়োগ করুন।"
            },
            "pa": {
                "title": "ਝੋਨੇ ਦੀ ਸਿੱਧੀ ਬਿਜਾਈ (ਤਰ-ਵੱਤਰ DSR ਤਕਨੀਕ)",
                "action": "ਡਿੱਗ ਰਹੇ ਧਰਤੀ ਹੇਠਲੇ ਪਾਣੀ ਨੂੰ ਬਚਾਉਣ ਲਈ ਕੱਦੂ ਕਰਨ ਦੀ ਥਾਂ ਤਰ-ਵੱਤਰ ਤਕਨੀਕ ਨਾਲ ਝੋਨੇ ਦੀ ਸਿੱਧੀ ਬਿਜਾਈ ਕਰੋ। ਇਸ ਨਾਲ 20-25% ਪਾਣੀ ਦੀ ਬੱਚਤ ਹੁੰਦੀ ਹੈ।",
                "note": "ਨਦੀਨਾਂ ਦੀ ਰੋਕਥਾਮ ਲਈ ਬਿਜਾਈ ਦੇ 24 ਘੰਟਿਆਂ ਦੇ ਅੰਦਰ ਪੈਂਡੀਮੈਥਾਲਿਨ ਦਾ ਛਿੜਕਾਅ ਲਾਜ਼ਮੀ ਕਰੋ।"
            },
            "te": {
                "title": "వరి నేరుగా విత్తే పద్ధతి (DSR)",
                "action": "భూగర్భ జలాలు తక్కువగా ఉన్న ప్రాంతాల్లో దమ్ము చేసి నాటు వేసే బదులు నేరుగా విత్తే పద్ధతిని చేపట్టండి. దీనివల్ల 20-25% నీరు ఆదా అవుతుంది.",
                "note": "కలుపు నివారణకు విత్తిన 24 గంటల్లోగా తగిన కలుపు మందును పిచికారీ చేయండి."
            }
        }
    },
    "harvest_maturity": {
        "id": "harvest_maturity",
        "category": "harvest",
        "evidence_source": "ICAR-CRRI & SAU Post-Harvest Loss Mitigation Guidelines",
        "benefit": "Prevents 5-15% field shattering and fungal spoilage losses through timely drain and harvest",
        "translations": {
            "en": {
                "title": "Maturity Stage & Harvest Readiness Management",
                "action": "Crop is at physiological maturity/ripening. Drain standing water from fields 10-14 days prior to harvest to facilitate mechanical harvesting and uniform grain drying. Harvest when 80-85% grains turn straw-golden.",
                "note": "For next season: procure certified seeds of stress-tolerant varieties (STRVs) suited to local flood or drought risks."
            },
            "hi": {
                "title": "फसल परिपक्वता एवं कटाई पूर्व प्रबंधन",
                "action": "फसल पकने की अवस्था पर है। कटाई से 10-14 दिन पहले खेत से बचा हुआ पानी निकाल दें ताकि कंबाइन हार्वेस्टर आसानी से चल सके और दाने एकसमान सूखें। जब 80-85% बालियां सुनहरी हो जाएं, तब कटाई करें।",
                "note": "आगामी फसल चक्र के लिए: स्थानीय जलवायु जोखिम (सूखा/बाढ़) अनुसार प्रमाणित तनाव-रोधी बीजों की अग्रिम व्यवस्था करें।"
            },
            "ta": {
                "title": "பயிர் முதிர்ச்சி மற்றும் அறுவடை மேலாண்மை",
                "action": "பயிர் முதிர்ச்சி நிலையை எட்டியுள்ளது. இயந்திர அறுவடை மற்றும் தானியம் சீராக காய்வதற்கு ஏதுவாக அறுவடைக்கு 10-14 நாட்களுக்கு முன்னதாக வயலிலுள்ள தண்ணீரை முழுமையாக வடித்துவிடவும். 80-85% கதிர்கள் பொன்நிறமாக மாறும்போது அறுவடை செய்யவும்.",
                "note": "அடுத்த பருவத்திற்கு: உள்ளூர் வெள்ளம் அல்லது வறட்சி அபாயங்களை எதிர்கொள்ள சான்றளிக்கப்பட்ட அழுத்த-தாங்கும் விதைகளை முன்கூட்டியே திட்டமிடுங்கள்."
            },
            "bn": {
                "title": "ফসল পরিপক্বতা ও কর্তন-পূর্ব ব্যবস্থাপনা",
                "action": "ফসল পরিপক্ব পর্যায়ে রয়েছে। যান্ত্রিক কর্তন ও ধান শুকানোর সুবিধার্থে কাটার ১০-১৪ দিন আগে জমির অতিরিক্ত পানি নিষ্কাশন করুন। ৮০-৮৫% শিষ সোনালী বর্ণ ধারণ করলে ধান কাটুন।",
                "note": "পরবর্তী মৌসুমের জন্য: স্থানীয় ঝুঁকি অনুযায়ী আগাম সহনশীল জাতের প্রত্যয়িত বীজ সংগ্রহ করুন।"
            },
            "pa": {
                "title": "ਫ਼ਸਲ ਪੱਕਣ ਅਤੇ ਵਾਢੀ ਦੀ ਤਿਆਰੀ ਦਾ ਪ੍ਰਬੰਧਨ",
                "action": "ਫ਼ਸਲ ਪੱਕਣ ਦੀ ਅਵਸਥਾ ਵਿੱਚ ਹੈ। ਕੰਬਾਈਨ ਨਾਲ ਕਟਾਈ ਅਤੇ ਦਾਣਿਆਂ ਦੇ ਸੁੱਕਣ ਲਈ ਵਾਢੀ ਤੋਂ 10-14 ਦਿਨ ਪਹਿਲਾਂ ਖੇਤ ਵਿੱਚੋਂ ਪਾਣੀ ਕੱਢ ਦਿਓ। ਜਦੋਂ 80-85% ਸਿੱਟੇ ਸੁਨਹਿਰੀ ਹੋ ਜਾਣ ਤਾਂ ਕਟਾਈ ਸ਼ੁਰੂ ਕਰੋ।",
                "note": "ਅਗਲੇ ਸੀਜ਼ਨ ਲਈ: ਸਥਾਨਕ ਮੌਸਮੀ ਜੋਖਮਾਂ ਅਨੁਸਾਰ ਪ੍ਰਮਾਣਿਤ ਤਣਾਅ-ਸਹਿਣਸ਼ੀਲ ਬੀਜਾਂ ਦਾ ਅਗਾਊਂ ਪ੍ਰਬੰਧ ਕਰੋ।"
            },
            "te": {
                "title": "పంట పరిపక్వత మరియు కోత నిర్వహణ",
                "action": "పంట పరిపక్వ దశకు చేరుకుంది. యంత్రాల ద్వారా కోత మరియు ధాన్యం సమానంగా ఎండటానికి కోతకు 10-14 రోజుల ముందే పొలం నుంచి నీటిని పూర్తిగా తీసివేయండి. 80-85% గింజలు బంగారు రంగులోకి మారినప్పుడు కోయండి.",
                "note": "తదుపరి పంట కాలం కోసం: స్థానిక ముప్పులను తట్టుకునే ధృవీకరించబడిన విత్తనాలను ముందస్తుగా సిద్ధం చేసుకోండి."
            }
        }
    }
}


def generate_advisory(
    crop: str,
    risk_scores: Dict[str, Any],
    phenology: Dict[str, Any],
    indicators: Dict[str, Any],
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Selects empirical agronomic solutions matching diagnosed risk levels and phenology stage.
    """
    lang = lang.lower() if lang in ["en", "hi", "ta", "bn", "pa", "te"] else "en"
    crop_lower = crop.lower()

    drought_score = risk_scores.get("drought", 0)
    heat_score = risk_scores.get("heat", 0)
    flood_score = risk_scores.get("flood", 0)
    overall_score = risk_scores.get("overall", 0)

    stage_str = phenology.get("current_phenological_stage", "").lower() if phenology else ""
    is_at_maturity = any(kw in stage_str for kw in ["ripening", "maturity", "mature", "harvesting", "harvest"])

    selected_solutions = []

    # If crop is at physiological maturity / ripening, gate out in-season irrigation advisories
    # and provide harvest timing, drainage, and forward-looking STRV variety planning.
    if is_at_maturity:
        selected_solutions.append(SOLUTIONS_DB["harvest_maturity"])
        if flood_score >= 40 and crop_lower == "rice":
            selected_solutions.append(SOLUTIONS_DB["submergence_rice"])
    else:
        # 1. Drought Stress Interventions
        if drought_score >= 45:
            if crop_lower == "rice":
                selected_solutions.append(SOLUTIONS_DB["safe_awd"])
                selected_solutions.append(SOLUTIONS_DB["drought_varieties_rice"])
            else:
                selected_solutions.append(SOLUTIONS_DB["crop_residue_mulch"])

        # 2. Terminal Heat Interventions
        if heat_score >= 35 or phenology.get("in_heat_sensitive_window", False):
            if crop_lower == "wheat":
                selected_solutions.append(SOLUTIONS_DB["terminal_heat_wheat"])
                selected_solutions.append(SOLUTIONS_DB["crop_residue_mulch"])
            elif crop_lower == "rice" and heat_score >= 50:
                selected_solutions.append(SOLUTIONS_DB["crop_residue_mulch"])

        # 3. Flood / Submergence Interventions
        if flood_score >= 35:
            if crop_lower == "rice":
                selected_solutions.append(SOLUTIONS_DB["submergence_rice"])

        # 4. Long-term Groundwater Conservation
        grace_trend = indicators.get("groundwater_trend", {}).get("regional_trend_cm_per_year")
        if grace_trend is not None and grace_trend < -1.5 and crop_lower == "rice":
            selected_solutions.append(SOLUTIONS_DB["direct_seeded_rice"])

    # If no high risk triggered, provide general best-practice climate-smart agronomy
    if not selected_solutions:
        if is_at_maturity:
            selected_solutions.append(SOLUTIONS_DB["harvest_maturity"])
        elif crop_lower == "rice":
            selected_solutions.append(SOLUTIONS_DB["safe_awd"])
        else:
            selected_solutions.append(SOLUTIONS_DB["crop_residue_mulch"])

    # Deduplicate while preserving order
    seen = set()
    unique_solutions = []
    for s in selected_solutions:
        if s["id"] not in seen:
            seen.add(s["id"])
            unique_solutions.append(s)

    # Format translated output
    cards = []
    for sol in unique_solutions:
        t = sol["translations"].get(lang, sol["translations"]["en"])
        cards.append({
            "id": sol["id"],
            "category": sol["category"],
            "title": t["title"],
            "action": t["action"],
            "management_note": t.get("note"),
            "evidence_base": sol["evidence_source"],
            "quantified_benefit": sol["benefit"]
        })

    # Summary advisory statement in selected language
    summaries = {
        "en": f"Climate adaptation plan for {crop.capitalize()} at {phenology.get('current_phenological_stage', 'current stage')}. Overall risk: {overall_score}/100.",
        "hi": f"{crop.capitalize()} के लिए जलवायु अनुकूलन सलाह (अवस्था: {phenology.get('current_phenological_stage')})। कुल जोखिम: {overall_score}/100।",
        "ta": f"{crop.capitalize()} பயிருக்கான காலநிலை மாற்ற தழுவல் ஆலோசனை (பருவம்: {phenology.get('current_phenological_stage')})। மொத்த அபாயம்: {overall_score}/100।",
        "bn": f"{crop.capitalize()} ফসলের জন্য জলবায়ু অভিযোজন পরামর্শ (পর্যায়: {phenology.get('current_phenological_stage')})। সামগ্রিক ঝুঁকি: {overall_score}/100।",
        "pa": f"{crop.capitalize()} ਲਈ ਜਲਵਾਯੂ ਅਨੁਕੂਲਨ ਸਲਾਹ (ਪੜਾਅ: {phenology.get('current_phenological_stage')})। ਕੁੱਲ ਜੋਖਮ: {overall_score}/100।",
        "te": f"{crop.capitalize()} పంట కోసం వాతావరణ మార్పుల సలహా (దశ: {phenology.get('current_phenological_stage')})। మొత్తం ముప్పు: {overall_score}/100।"
    }

    result = {
        "language": lang,
        "crop": crop_lower,
        "phenological_stage": phenology.get("current_phenological_stage"),
        "overall_risk_score": overall_score,
        "summary": summaries.get(lang, summaries["en"]),
        "recommendations": cards
    }

    if lang != "en":
        result["translation_disclaimer"] = "Machine-translated, verify with local extension"

    return result
