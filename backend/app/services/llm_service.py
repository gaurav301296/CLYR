"""
CLYR LLM Service — Generates personalized vernacular credit analysis letters.

Output format: A structured letter (not JSON) that combines:
- Bloomberg/McKinsey depth (specific numbers, data-backed, prioritized)
- Friend-over-chai tone (simple, warm, no jargon)
- Truly Indian vernacular (not translated English — local tone, local metaphors)
"""

import os
import re
import json
import time
import hashlib
import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# In-memory cache for LLM responses
_llm_cache: dict[str, dict] = {}
_CACHE_MAX_SIZE = 50


def _get_cache_key(raw_text: str) -> str:
    return hashlib.sha256(raw_text[:8000].encode()).hexdigest()


# ─── Language Tone Profiles ───────────────────────────────────────────────
# Each language has a tone profile that makes it sound LOCAL, not translated.

TONE_PROFILES = {
    "en": {
        "greeting": "Dear {name},",
        "intro": "I've gone through your credit report carefully. Your score is {score} — {health_summary}. Don't worry, I'll explain exactly what's going on and what you can do about it.",
        "issue_intro": "Here's what I found:",
        "issue_label": "Problem #{n}",
        "score_impact": "This is pulling your score down by approximately {impact} points.",
        "what_to_do": "Here's exactly what to do:",
        "timeline": "Expected timeline: {days} days",
        "score_projection": "If you fix all of this, here's where your score could be:",
        "current": "Current",
        "after_fixes": "After fixes",
        "closing": "I know this looks like a lot, but take it one step at a time. Fix the first issue this week, and you'll already be on your way. You've got this.",
        "signoff": "— CLYR",
        "number_format": "western",  # 1,00,000
        "currency": "₹",
    },
    "hi": {
        "greeting": "{name} जी,",
        "intro": "मैंने आपकी CIBIL रिपोर्ट बारीकी से देखी। आपका स्कोर {score} है — {health_summary}। चिंता न करें, मैं आपको बताता/बताती हूँ कि क्या समस्या है और इसे कैसे ठीक किया जाए।",
        "issue_intro": "मैंने जो समस्याएं पकडी हैं वो ये हैं:",
        "issue_label": "समस्या #{n}",
        "score_impact": "इस एक समस्या के कारण आपका स्कोर लगभग {impact} अंक नीचे है।",
        "what_to_do": "ये करें — सटीक तरीका:",
        "timeline": "इसमें लगभग {days} दिन लगेंगे",
        "score_projection": "अगर आप सभी समस्याएं हल करते हैं, तो आपका स्कोर ऐसा हो सकता है:",
        "current": "अभी",
        "after_fixes": "सब ठीक करने के बाद",
        "closing": "मैं समझता/समझती हूँ कि ये बहुत लग रहा है, लेकिन एक एक करके करें। इस हफ्ते पहली समस्या हल करें, और आप रास्ते पर होंगे।",
        "signoff": "— CLYR",
        "number_format": "indian",  # 1,00,000
        "currency": "₹",
    },
    "bn": {
        "greeting": "{name} জী,",
        "intro": "আমি আপনার CIBIL রিপোর্ট ভালো করে দেখেছি। আপনার স্কোর {score} — {health_summary}। চিন্তা করবেন না, আমি বলছি কী সমস্যা আছে এবং কী করতে হবে।",
        "issue_intro": "আমি যে সমস্যাগুলো খুঁজে পেয়েছি:",
        "issue_label": "সমস্যা #{n}",
        "score_impact": "এই একটা সমস্যার জন্য আপনার স্কোর প্রায় {impact} পয়েন্ট কমে গেছে।",
        "what_to_do": "ঠিক এইভাবে করবেন:",
        "timeline": "আনুমানিক {days} দিন লাগবে",
        "score_projection": "সব ঠিক করলে আপনার স্কোর এমন হতে পারে:",
        "current": "এখন",
        "after_fixes": "সব ঠিক করার পর",
        "closing": "অনেক বেশি মনে হচ্ছে, জানি। কিন্তু একটু একটু করে করুন। এই সপ্তাহে প্রথম সমস্যাটা সমাধান করুন, আপনি পথে আসবেন।",
        "signoff": "— CLYR",
        "number_format": "indian",
        "currency": "₹",
    },
    "te": {
        "greeting": "{name} గారు,",
        "intro": "మీ CIBIL రిపోర్ట్ నిజంగా చిన్నగా చూశాను. మీ స్కోర్ {score} — {health_summary}. బాధపడకండి, ఏమి సమస్య మరియు దాన్ని ఎలా పరిష్కరించాలో చెప్తాను.",
        "issue_intro": "నేను కనుగొన్న సమస్యలు:",
        "issue_label": "సమస్య #{n}",
        "score_impact": "ఈ ఒక్క సమస్య వల్ల మీ స్కోర్ దాదాపు {impact} పాయింట్లు తగ్గిపోయింది.",
        "what_to_do": "ఇలా చేయండి — ఖచ్చితమైన మార్గం:",
        "timeline": "దాదాపు {days} రోజులు పడుతుంది",
        "score_projection": "మీరు అన్ని సమస్యలు పరిష్కరిస్తే, మీ స్కోర్ ఇలా ఉంటుంది:",
        "current": "ప్రస్తుతం",
        "after_fixes": "అన్నీ పరిష్కరించిన తర్వాత",
        "closing": "చాలా ఎక్కువ అనిపిస్తుంది, అర్థమైంది. కానీ ఒక్కొక్కటి చేయండి. ఈ వారం మొదటి సమస్య పరిష్కరించండి, మీరు మార్గంలో ఉంటారు.",
        "signoff": "— CLYR",
        "number_format": "indian",
        "currency": "₹",
    },
    "mr": {
        "greeting": "{name} जी,",
        "intro": "मी तुमची CIBIL रिपोर्ट बारकाईने पाहिली. तुमचा स्कोर {score} आहे — {health_summary}. काळजी करू नका, काय समस्या आहे आणि ती कशी सारवायची हे सांगतो/सांगते.",
        "issue_intro": "मला ज्या समस्या सापडल्या:",
        "issue_label": "समस्या #{n}",
        "score_impact": "या एका समस्येमुळे तुमचा स्कोर अंदाजे {impact} अंक कमी आहे.",
        "what_to_do": "हे करा — अचूक पद्धत:",
        "timeline": "अंदाजे {days} दिवस लागतील",
        "score_projection": "जर तुम्ही सर्व समस्या सोडवल्या, तर तुमचा स्कोर असा असू शकतो:",
        "current": "आत्ता",
        "after_fixes": "सर्व सोडवल्यानंतर",
        "closing": "खूप जास्त वाटते, मला माहीत आहे. पण एक एक करून करा. या आठवड्यात पहिली समस्या सोडवा, आणि तुम्ही मार्गावर आहात.",
        "signoff": "— CLYR",
        "number_format": "indian",
        "currency": "₹",
    },
    "ta": {
        "greeting": "{name} அவர்களே,",
        "intro": "உங்கள் CIBIL அறிக்கையை நன்றாக பார்த்தேன். உங்கள் ஸ்கோர் {score} — {health_summary}. கவலைப்பட வேண்டாம், என்ன பிரச்சனை என்றும் எப்படி சரிசெய்வது என்றும் சொல்கிறேன்.",
        "issue_intro": "நான் கண்டுபிடித்த பிரச்சனைகள்:",
        "issue_label": "பிரச்சனை #{n}",
        "score_impact": "இந்த ஒரு பிரச்சனையால் உங்கள் ஸ்கோர் சுமார் {impact} புள்ளிகள் குறைந்திருக்கிறது.",
        "what_to_do": "இப்படி செய்யுங்கள் — சரியான வழி:",
        "timeline": "சுமார் {days} நாட்கள் ஆகும்",
        "score_projection": "நீங்கள் எல்லாவற்றையும் சரிசெய்தால், உங்கள் ஸ்கோர் இப்படி இருக்கும்:",
        "current": "இப்போது",
        "after_fixes": "எல்லாம் சரிசெய்த பிறகு",
        "closing": "நிறைய இருக்கிறது என்று தெரிகிறது, எனக்கும் தெரியும். ஆனா ஒவ்வொன்றாக செய்யுங்கள். இந்த வாரம் முதல் பிரச்சனையை சரிசெய்யுங்கள், நீங்கள் பாதையில் இருப்பீர்கள்.",
        "signoff": "— CLYR",
        "number_format": "indian",
        "currency": "₹",
    },
    "gu": {
        "greeting": "{name} જી,",
        "intro": "મેં તમારી CIBIL રિપોર્ટ ધ્યાનથી જોઈ. તમારો સ્કોર {score} છે — {health_summary}. ચિંતા કરશો નહીં, શું સમસ્યા છે અને તે કેવી રીતે ઠીક કરવી તે સમજાવું.",
        "issue_intro": "મેં જે સમસ્યાઓ જોઈ:",
        "issue_label": "સમસ્યા #{n}",
        "score_impact": "આ એક સમસ્યાને કારણે તમારો સ્કોર લગભગ {impact} અંક નીચે છે.",
        "what_to_do": "આ કરો — ચોક્કસ રીત:",
        "timeline": "લગભગ {days} દિવસ લાગશે",
        "score_projection": "જો તમે બધી સમસ્યાઓ હલ કરશો, તો તમારો સ્કોર આવો હોઈ શકે:",
        "current": "હમણાં",
        "after_fixes": "બધું ઠીક કર્યા પછી",
        "closing": "ઘણું બધું લાગે છે, હું સમજું છું. પણ એક એક કરીને કરો. આ અઠવાડિયે પહેલી સમસ્યા હલ કરો, અને તમે માર્ગ પર છો.",
        "signoff": "— CLYR",
        "number_format": "indian",
        "currency": "₹",
    },
    "kn": {
        "greeting": "{name} ಅವರೆ,",
        "intro": "ನಿಮ್ಮ CIBIL ವರದಿಯನ್ನು ಚೆನ್ನಾಗಿ ನೋಡಿದ್ದೇನೆ. ನಿಮ್ಮ ಸ್ಕೋರ್ {score} — {health_summary}. ಚಿಂತೆ ಮಾಡಬೇಡಿ, ಏನು ಸಮಸ್ಯೆ ಮತ್ತು ಅದನ್ನು ಹೇಗೆ ಸರಿಪಡಿಸುವುದು ಎಂದು ಹೇಳುತ್ತೇನೆ.",
        "issue_intro": "ನಾನು ಕಂಡುಕೊಂಡ ಸಮಸ್ಯೆಗಳು:",
        "issue_label": "ಸಮಸ್ಯೆ #{n}",
        "score_impact": "ಈ ಒಂದು ಸಮಸ್ಯೆಯಿಂದ ನಿಮ್ಮ ಸ್ಕೋರ್ ಸುಮಾರು {impact} ಅಂಕೆಗಳು ಕಡಿಮೆಯಾಗಿದೆ.",
        "what_to_do": "ಇದನ್ನು ಮಾಡಿ — ನಿಖರವಾದ ವಿಧಾನ:",
        "timeline": "ಸುಮಾರು {days} ದಿನಗಳು ಬೇಕಾಗುತ್ತದೆ",
        "score_projection": "ನೀವು ಎಲ್ಲಾ ಸಮಸ್ಯೆಗಳನ್ನು ಪರಿಹರಿಸಿದರೆ, ನಿಮ್ಮ ಸ್ಕೋರ್ ಹೀಗಿರಬಹುದು:",
        "current": "ಈಗ",
        "after_fixes": "ಎಲ್ಲವನ್ನೂ ಪರಿಹರಿಸಿದ ನಂತರ",
        "closing": "ತುಂಬಾ ಇದೆ ಅನಿಸುತ್ತದೆ, ನನಗೂ ಗೊತ್ತು. ಆದರೆ ಒಂದೊಂದಾಗಿ ಮಾಡಿ. ಈ ವಾರ ಮೊದಲ ಸಮಸ್ಯೆಯನ್ನು ಪರಿಹರಿಸಿ, ನೀವು ದಾರಿಯಲ್ಲಿರುತ್ತೀರಿ.",
        "signoff": "— CLYR",
        "number_format": "indian",
        "currency": "₹",
    },
    "ml": {
        "greeting": "{name} അവർകൾ,",
        "intro": "നിങ്ങളുടെ CIBIL റിപ്പോർട്ട് ഞൻ നന്നായി നോട്ടു. നിങ്ങളുടെ സ്കോർ {score} — {health_summary}. വിഷമിക്കേണ്ട, എന്താണ് പ്രശ്നം എന്നും അത് എങ്ങനെ പരിഹരിക്കാം എന്നും പറയാം.",
        "issue_intro": "ഞാൻ കണ്ടെത്തിയ പ്രശ്നങ്ങൾ:",
        "issue_label": "പ്രശ്നം #{n}",
        "score_impact": "ഈ ഒരു പ്രശ്നം കാരണം നിങ്ങളുടെ സ്കോർ ഏകദേശം {impact} പോയിന്റ് കുറഞ്ഞിരിക്കുന്നു.",
        "what_to_do": "ഇത് ചെയ്യുക — കൃത്യമായ രീതി:",
        "timeline": "ഏകദേശം {days} ദിവസം വേണ്ടി വരും",
        "score_projection": "എല്ലാ പ്രശ്നങ്ങളും പരിഹരിച്ചാൽ, നിങ്ങളുടെ സ്കോർ ഇത്തരം ആകാം:",
        "current": "ഇപ്പോൾ",
        "after_fixes": "എല്ലാം പരിഹരിച്ച ശേഷം",
        "closing": "വളരെ കൂടുതൽ ആയി തോന്നുന്നു, എനിക്കും മനസ്സിലാകുന്നു. പക്ഷേ ഒന്നൊന്നായി ചെയ്യുക. ഈ ആഴ്ച ആദ്യ പ്രശ്നം പരിഹരിക്കുക, നിങ്ങൾ വഴിയിലാകും.",
        "signoff": "— CLYR",
        "number_format": "indian",
        "currency": "₹",
    },
    "pa": {
        "greeting": "{name} ਜੀ,",
        "intro": "ਮੈਂ ਤੁਹਾਡੀ CIBIL ਰਿਪੋਰਟ ਚੰਗੀ ਤਰ੍ਹਾਂ ਵੇਖੀ। ਤੁਹਾਡਾ ਸਕੋਰ {score} ਹੈ — {health_summary}। ਫਿਕਰ ਨਾ ਕਰੋ, ਕੀ ਸਮੱਸਿਆ ਹੈ ਅਤੇ ਇਸਨੂੰ ਕਿਵੇਂ ਠੀਕ ਕਰਨਾ ਹੈ ਇਹ ਦੱਸਦਾ/ਦੱਸਦੀ ਹਾਂ।",
        "issue_intro": "ਮੈਂ ਜੋ ਸਮੱਸਿਆਵਾਂ ਲੱਭੀਆਂ:",
        "issue_label": "ਸਮੱਸਿਆ #{n}",
        "score_impact": "ਇਸ ਇੱਕ ਸਮੱਸਿਆ ਕਰਕੇ ਤੁਹਾਡਾ ਸਕੋਰ ਲਗਭਗ {impact} ਅੰਕ ਘੱਟ ਹੈ।",
        "what_to_do": "ਇਹ ਕਰੋ — ਸਹੀ ਤਰੀਕਾ:",
        "timeline": "ਲਗਭਗ {days} ਦਿਨ ਲੱਗਣਗੇ",
        "score_projection": "ਜੇ ਤੁਸੀਂ ਸਾਰੀਆਂ ਸਮੱਸਿਆਵਾਂ ਹੱਲ ਕਰੋ, ਤਾਂ ਤੁਹਾਡਾ ਸਕੋਰ ਇਹ ਹੋ ਸਕਦਾ ਹੈ:",
        "current": "ਹੁਣ",
        "after_fixes": "ਸਭ ਠੀਕ ਕਰਨ ਤੋਂ ਬਾਅਦ",
        "closing": "ਬਹੁਤ ਜ਼ਿਆਦਾ ਲੱਗਦਾ ਹੈ, ਮੈਨੂੰ ਪਤਾ ਹੈ। ਪਰ ਇੱਕ ਇੱਕ ਕਰਕੇ ਕਰੋ। ਇਹ ਹਫ਼ਤੇ ਪਹਲੀ ਸਮੱਸਿਆ ਹੱਲ ਕਰੋ, ਅਤੇ ਤੁਸੀਂ ਰਾਹ ਤੇ ਹੋਵੋਗੇ।",
        "signoff": "— CLYR",
        "number_format": "indian",
        "currency": "₹",
    },
}


def _format_amount(amount: int, lang: str) -> str:
    """Format amount in Indian numbering system with ₹ symbol."""
    if amount == 0:
        return "₹0"
    s = str(amount)
    if len(s) <= 3:
        return f"₹{s}"
    last_three = s[-3:]
    remaining = s[:-3]
    out = []
    while len(remaining) > 2:
        out.append(remaining[-2:])
        remaining = remaining[:-2]
    if remaining:
        out.append(remaining)
    out.reverse()
    return f"₹{','.join(out)},{last_three}"


def _get_health_summary(score: int, lang: str) -> str:
    """Get a simple, non-technical health summary."""
    summaries = {
        "en": {
            "excellent": "this is great — lenders will love you",
            "good": "this is decent, but there's room to improve",
            "fair": "this needs work — some lenders may reject you",
            "poor": "this is concerning, but it's fixable",
        },
        "hi": {
            "excellent": "ये बहुत अच्छा है — लोन मिल जाएगा",
            "good": "ये ठीक है, लेकिन और बेहतर हो सकता है",
            "fair": "इसमें सुधार चाहिए — कुछ बैंक लोन नहीं देंगे",
            "poor": "ये चिंता की बात है, लेकिन ठीक हो सकता है",
        },
        "bn": {
            "excellent": "এটা দারুণ — লোন পাবেন সহজেই",
            "good": "এটা ভালো, কিন্তু আরো উন্নতি করা যায়",
            "fair": "এটা উন্নতি দরকার — কিছু ব্যাংক লোন দিতে অস্বীকার করতে পারে",
            "poor": "এটা উদ্বেগজনক, কিন্তু ঠিক করা যায়",
        },
        "te": {
            "excellent": "ఇది చాలా బాగుంది — లోన్ సులభంగా వస్తుంది",
            "good": "ఇది బాగుంది, కానీ ఇంకా మెరుగుపరచవచ్చు",
            "fair": "ఇది మెరుగుపరచాలి — కొన్ని బ్యాంకులు లోన్ ఇవ్వకపోవచ్చు",
            "poor": "ఇది ఆందోళనకరం, కానీ సరిపడుతుంది",
        },
        "mr": {
            "excellent": "हे छान आहे — लोन सहज मिळेल",
            "good": "हे ठीक आहे, पण आणखी चांगले होऊ शकते",
            "fair": "यात सुधारणा करावी — काही बँका लोन देणार नाहीत",
            "poor": "हे काळजीचे आहे, पण सारवता येते",
        },
        "ta": {
            "excellent": "இது மிகவும் நல்லது — கடன் எளிதாக கிடைக்கும்",
            "good": "இது நன்றாக உள்ளது, ஆனாலும் மேலும் மேம்படுத்தலாம்",
            "fair": "இதை மேம்படுத்த வேண்டும் — சில வங்கிகள் கடன் கொடுக்க மறுக்கலாம்",
            "poor": "இது கவலையாக இருக்கிறது, ஆனால் சரிசெய்ய முடியும்",
        },
        "gu": {
            "excellent": "આ ખૂબ સરસ છે — લોન સહેજથી મળશે",
            "good": "આ સારું છે, પણ હજુ સુધારી શકાય છે",
            "fair": "આમાં સુધારો જોઈએ — કેટલાક બેંકો લોન નહીં આપે",
            "poor": "આ ચિંતાજનક છે, પણ ઠીક કરી શકાય",
        },
        "kn": {
            "excellent": "ಇದು ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ — ಸುಲಭವಾಗಿ ಸಾಲ ಸಿಗುತ್ತದೆ",
            "good": "ಇದು ಒಳ್ಳೆಯದು, ಆದರೆ ಇನ್ನೂ ಉತ್ತಮಪಡಿಸಬಹುದು",
            "fair": "ಇದನ್ನು ಉತ್ತಮಪಡಿಸಬೇಕು — ಕೆಲವು ಬ್ಯಾಂಕುಗಳು ಸಾಲ ನೀಡದಿರಬಹುದು",
            "poor": "ಇದು ಚಿಂತೆಯ ವಿಷಯ, ಆದರೆ ಸರಿಪಡಿಸಬಹುದು",
        },
        "ml": {
            "excellent": "ഇത് വളരെ നല്ലതാണ് — ലോൺ എളുപ്പത്തിൽ കിട്ടും",
            "good": "ഇത് നല്ലതാണ്, പക്ഷേ ഇനിയും മെച്ചപ്പെടുത്താം",
            "fair": "ഇത് മെച്ചപ്പെടുത്തണം — ചില ബാങ്കുകൾ ലോൺ നൽകില്ല",
            "poor": "ഇത് ആശങ്കാജനകമാണ്, പക്ഷേ പരിഹരിക്കാം",
        },
        "pa": {
            "excellent": "ਇਹ ਬਹੁਤ ਵਧੀਆ ਹੈ — ਲੋਨ ਆਸਾਨੀ ਨਾਲ ਮਿਲੇਗੀ",
            "good": "ਇਹ ਠੀਕ ਹੈ, ਪਰ ਹਾਲੇ ਵੀ ਸੁਧਾਰ ਹੋ ਸਕਦਾ ਹੈ",
            "fair": "ਇਸ ਵਿੱਚ ਸੁਧਾਰ ਚਾਹੀਦਾ ਹੈ — ਕੁਝ ਬੈਂਕ ਲੋਨ ਨਹੀਂ ਦੇਣਗੇ",
            "poor": "ਇਹ ਚਿੰਤਾ ਦੀ ਗੱਲ ਹੈ, ਪਰ ਠੀਕ ਹੋ ਸਕਦਾ ਹੈ",
        },
    }
    lang_summaries = summaries.get(lang, summaries["en"])
    if score >= 750:
        return lang_summaries["excellent"]
    elif score >= 700:
        return lang_summaries["good"]
    elif score >= 620:
        return lang_summaries["fair"]
    else:
        return lang_summaries["poor"]


# ─── The Letter Prompt ────────────────────────────────────────────────────

LETTER_PROMPT_TEMPLATE = """You are CLYR — an expert credit report analyst who explains complex credit reports in simple, friendly language to Indian consumers.

Your job: Analyze the credit report below and write a PERSONALIZED LETTER to the customer in {language}.

TONE:
- Like a smart friend who works in banking, explaining over chai
- Simple words, no jargon. If you must use a technical term, explain it in brackets.
- Warm but direct. Don't sugarcoat problems, but don't scare them either.
- Use Indian numbering (lakh, crore) and Indian context (CIBIL, RBI, etc.)

LANGUAGE: {language}
- If Hindi: Use Devanagari script, conversational Hindi (not formal shuddh Hindi)
- If Bengali: Use Bangla script, conversational tone
- If Telugu: Use Telugu script, conversational tone
- If Tamil: Use Tamil script, conversational tone
- If Marathi: Use Devanagari script, conversational Marathi
- If Gujarati: Use Gujarati script, conversational tone
- If Kannada: Use Kannada script, conversational tone
- If Malayalam: Use Malayalam script, conversational tone
- If Punjabi: Use Gurmukhi script, conversational tone
- If English: Use simple English, Indian context

OUTPUT FORMAT (follow this structure exactly):

---LETTER_START---
GREETING: [Warm greeting in their language, use their name if found]

INTRO: [2-3 sentences: their score, what it means in plain terms, reassurance that it's fixable]

[For each issue found, in priority order (most damaging first):]

ISSUE #[n]:
WHAT: [What's wrong — specific account, specific amount, specific problem, in 1-2 sentences]
IMPACT: [How many points this is costing them, and why it matters]
ACTION: [Exact steps to fix this — day by day if possible. Include: who to contact, what to say, what documents needed, expected timeline]
TIMELINE: [How many days this will take to resolve]
SUCCESS_CHANCE: [High/Medium/Low — be honest]

[After all issues:]

SCORE_PROJECTION:
Current: [score]
After fixing all issues: [realistic projected score range]
Timeline: [realistic timeline in days/weeks]

CLOSING: [Encouraging closing — 2-3 sentences. Make them feel like they can do this.]

DISPUTE_LETTERS:
[For each issue, include a ready-to-send dispute letter that the customer can copy and send to the bank/CIBIL. Each letter should be:
- Addressed to the correct entity (bank or CIBIL)
- Include specific account details from the report
- State the problem clearly
- Request specific action
- Include relevant RBI/CIBIL rules if applicable
- Be in the same language as the letter]
---LETTER_END---

RULES:
1. ONLY include issues actually found in the report. NEVER fabricate issues.
2. Be SPECIFIC — use actual account names, actual amounts, actual dates from the report.
3. Every action step must be something the customer can do THEMSELVES — no "consult a lawyer" or "hire a CA."
4. Include specific RBI rules, CIBIL processes, or bank procedures where relevant.
5. If the score is good (750+), say so and give maintenance tips instead of problem-solving.
6. If no issues found, write a positive letter with maintenance advice.
7. Keep the letter under 2000 words total.
8. Output ONLY the letter content between ---LETTER_START--- and ---LETTER_END---.

CREDIT REPORT TEXT:
{report_text}
"""


def _try_llm_parse(raw_text: str, language: str = "en") -> dict | None:
    """Generate a personalized letter using the LLM."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key == "placeholder":
        return None

    cache_key = _get_cache_key(raw_text + language)
    if cache_key in _llm_cache:
        logger.info("LLM cache hit")
        return _llm_cache[cache_key]

    try:
        from openai import OpenAI, RateLimitError, APIError

        base_url = os.environ.get("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
        model = os.environ.get("OPENAI_MODEL", "gemini-2.0-flash")

        client = OpenAI(api_key=api_key, base_url=base_url, timeout=90)

        prompt = LETTER_PROMPT_TEMPLATE.format(
            language=language,
            report_text=raw_text[:8000]
        )

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4000,
            )
        except RateLimitError:
            logger.warning("Gemini rate limit hit. Falling back to regex parser.")
            return None
        except APIError as e:
            logger.error(f"Gemini API error: {e}")
            return None

        content = response.choices[0].message.content.strip()

        # Extract letter content
        if "---LETTER_START---" in content and "---LETTER_END---" in content:
            letter = content.split("---LETTER_START---")[1].split("---LETTER_END---")[0].strip()
        else:
            letter = content

        # Also extract structured data for the dispute letters section
        result = {
            "letter": letter,
            "language": language,
            "raw_llm_output": content,
        }

        if len(_llm_cache) >= _CACHE_MAX_SIZE:
            oldest_key = next(iter(_llm_cache))
            del _llm_cache[oldest_key]
        _llm_cache[cache_key] = result

        return result

    except Exception as e:
        logger.error(f"LLM parse failed: {e}")
        return None


def _regex_fallback_parse(raw_text: str, language: str = "en") -> dict:
    """Fallback regex-based parser when LLM is unavailable."""
    import re

    score = 650
    customer_name = "Valued Customer"
    issues = []

    # Extract score
    score_match = re.search(r'(?:cibil|score|rating)\s*(?:is|:|of)?\s*:?\s*\b([3-8]\d{2})\b', raw_text, re.IGNORECASE)
    if score_match:
        score = int(score_match.group(1))

    # Extract name
    name_match = re.search(r'(?:consumer\s+)?name\s*:?\s*([^\n:]{3,50})', raw_text, re.IGNORECASE)
    if name_match:
        customer_name = name_match.group(1).strip()
        customer_name = re.sub(r'\s+', ' ', customer_name)

    # Parse accounts
    raw_lines = raw_text.split('\n')
    accounts = []
    current_account = None

    for line in raw_lines:
        match = re.match(r'^\s*ACCOUNT\s*(\d+)?\s*:\s*(.+)$', line, re.IGNORECASE)
        if match:
            name = match.group(2).strip()
            if not any(name.upper().startswith(kw) for kw in ["TYPE", "STATUS", "SANCTIONED", "CURRENT", "PAYMENT", "REMARK", "BALANCE"]):
                if current_account:
                    accounts.append(current_account)
                current_account = {
                    "name": name, "type": "", "sanctioned_amount": "",
                    "current_balance": "", "payment_status": "", "remarks": "", "raw_lines": [line.strip()]
                }
                continue
        if current_account:
            current_account["raw_lines"].append(line.strip())
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.upper().strip()
                val = val.strip()
                if "TYPE" in key: current_account["type"] = val
                elif "SANCTIONED" in key: current_account["sanctioned_amount"] = val
                elif "BALANCE" in key: current_account["current_balance"] = val
                elif "STATUS" in key: current_account["payment_status"] = val
                elif "REMARK" in key: current_account["remarks"] = val
    if current_account:
        accounts.append(current_account)

    for account in accounts:
        status_desc = (account["remarks"] or account["payment_status"] or "").strip()
        remarks_upper = account["remarks"].upper()
        status_upper = account["payment_status"].upper()
        is_negative = any(kw in remarks_upper or kw in status_upper for kw in ["WRITTEN OFF", "WRITTEN-OFF", "WRITE OFF", "SETTLED", "SETTLEMENT", "LOSS"])
        is_late = any(kw in remarks_upper or kw in status_upper for kw in ["LATE PAYMENT", "DELAYED", "OVERDUE", "DPD", "DAYS PAST DUE"])

        if is_negative or is_late:
            amount_str = ""
            for val in [account["current_balance"], account["sanctioned_amount"]]:
                if val:
                    num_match = re.search(r'([\d,]+)', val)
                    if num_match:
                        amount_str = num_match.group(1)
                        break
            amount_val = 0
            if amount_str:
                clean_digits = re.sub(r'[^\d]', '', amount_str)
                if clean_digits:
                    amount_val = int(clean_digits)

            raw_name = account["name"]
            acronyms = {"HDFC", "SBI", "ICICI", "HSBC", "PNB", "BOB", "AXIS"}
            words = []
            for w in raw_name.split():
                w_upper = w.upper()
                words.append(w_upper if w_upper in acronyms else w.capitalize())
            account_title = " ".join(words)

            if is_negative:
                issue_type = "Red"
                impact = "High"
                details = f"Account shows negative status '{status_desc}'"
                action = "Contact bank for settlement/NOC"
            else:
                issue_type = "Yellow"
                impact = "Medium"
                details = f"Overdue payment history: {status_desc}"
                action = "Pay overdue amount immediately"

            issues.append({
                "account": account_title,
                "type": issue_type,
                "details": details[:150],
                "action": action,
                "impact": impact,
                "amount": amount_val,
            })

    # Build a simple letter from regex data
    tone = TONE_PROFILES.get(language, TONE_PROFILES["en"])
    health_summary = _get_health_summary(score, language)

    letter_parts = []
    letter_parts.append(tone["greeting"].format(name=customer_name))
    letter_parts.append("")
    letter_parts.append(tone["intro"].format(score=score, health_summary=health_summary))
    letter_parts.append("")

    if issues:
        letter_parts.append(tone["issue_intro"])
        letter_parts.append("")
        for i, issue in enumerate(issues, 1):
            letter_parts.append(f"{tone['issue_label'].format(n=i)}: {issue['account']}")
            letter_parts.append(f"  {issue['details']}")
            if issue['amount'] > 0:
                letter_parts.append(f"  Amount: {_format_amount(issue['amount'], language)}")
            letter_parts.append(f"  {tone['score_impact'].format(impact='30-50' if issue['type'] == 'Red' else '15-25')}")
            letter_parts.append(f"  {tone['what_to_do']}: {issue['action']}")
            letter_parts.append("")
    else:
        letter_parts.append("Good news — no major issues found in your report!")
        letter_parts.append("")

    letter_parts.append(tone["closing"])
    letter_parts.append("")
    letter_parts.append(tone["signoff"])

    return {
        "letter": "\n".join(letter_parts),
        "language": language,
        "score": score,
        "customer_name": customer_name,
        "issues": issues,
        "raw_llm_output": None,
    }


def generate_credit_summary(raw_text: str, language: str = "en") -> dict:
    """
    Main entry point. Generates a personalized credit analysis letter.
    
    Returns dict with:
    - letter: The full letter text (the product)
    - language: Language used
    - score: Extracted credit score
    - customer_name: Extracted name
    - issues: List of issues found
    """
    if not raw_text or len(raw_text.strip()) == 0:
        raise ValueError("Text cannot be empty")

    # Normalize language
    lang = language.lower().strip()
    if lang not in TONE_PROFILES:
        lang = "en"

    # Try LLM first
    llm_result = _try_llm_parse(raw_text, lang)
    if llm_result:
        return llm_result

    # Fallback to regex
    return _regex_fallback_parse(raw_text, lang)


def clear_llm_cache():
    _llm_cache.clear()
