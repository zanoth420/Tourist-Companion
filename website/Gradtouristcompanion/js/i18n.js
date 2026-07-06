/* Internationalization: English (default) + Arabic with RTL.
   Loaded in <head> so lang/dir are set before paint (no flash), mirroring
   theme.js. Static text carries data-i18n / data-i18n-ph / data-i18n-html
   attributes; dynamic JS strings call t(key). applyLang() dispatches a
   'langchange' event so dynamic renderers (nav, itinerary) can rebuild. */

const I18N = {
  en: {
    brand: 'Tourist Companion',
    'nav.home': 'Home', 'nav.programs': 'Programs', 'nav.build': 'Build Trip',
    'nav.mytrips': 'My Trips', 'nav.login': 'Login', 'nav.logout': 'Logout',

    'home.eyebrow': 'Egypt · optimized itineraries',
    'home.h1': 'Egypt, curated for you.',
    'home.hero_p': 'Timeless wonders, planned to your exact budget with real, verified ticket prices — a full day-by-day itinerary in seconds.',
    'home.begin': 'Begin your journey', 'home.browse': 'Browse programs',
    'stat.sites': 'verified sites', 'stat.cities': 'cities',
    'stat.prices': 'official prices', 'stat.tiers': 'visitor price tiers',
    'home.popular': 'Popular programs',
    'home.popular_sub': 'Curated trips — pick one and we compute the optimal itinerary live.',
    'home.how': 'How it works',
    'home.how_sub': 'An exact optimizer, not a guess — and a real schedule you can follow.',
    'home.step1_h': 'Set your budget',
    'home.step1_p': 'Tell us your ticket budget, days, and interests — foreign or Egyptian, adult or student.',
    'home.step2_h': 'We optimize',
    'home.step2_p': 'An exact solver picks the best-rated set of attractions that fits your exact budget.',
    'home.step3_h': 'Follow the plan',
    'home.step3_p': 'Day-by-day, ordered by geography and opening hours — with maps links and calendar export.',
    'home.use_program': 'Use this program',
    'footer.prices': 'Prices from the Egyptian Ministry of Tourism & Antiquities ticket list.',
    'footer.plan_cta': 'Plan your trip →',

    'programs.h1': 'Ready-made programs',
    'programs.sub': 'Curated trip templates — pick one and we compute the optimal itinerary live from official ticket prices. You can tweak everything afterwards.',

    'build.h1': 'Build your trip',
    'build.sub': 'Set your budget and time — we compute the optimal itinerary from officially priced attractions. Prefer a template?',
    'build.sub_link': 'See ready-made programs.',
    'label.budget': 'Budget (EGP, tickets)', 'label.days': 'Days',
    'label.hours': 'Hours / day', 'label.startdate': 'Start date (optional)',
    'label.visitor': 'Visitor', 'opt.foreign': 'Foreign visitor', 'opt.egyptian': 'Egyptian',
    'label.tickettype': 'Ticket type', 'opt.adult': 'Adult', 'opt.student': 'Student',
    'label.spend': 'Spending style', 'opt.value': 'Budget-friendly',
    'opt.balanced': 'Balanced', 'opt.premium': 'Premium (splurge)',
    'label.interests': 'Interests (click to boost)',
    'chip.ancient': 'Ancient Egypt', 'chip.islamic': 'Islamic Cairo',
    'chip.coptic': 'Coptic heritage', 'chip.museum': 'Museums',
    'chip.palace': 'Palaces', 'chip.experience': 'Experiences', 'chip.nature': 'Nature & beaches',
    'build.submit': 'Build my trip',
    'build.footer': 'Prices from the Egyptian Ministry of Tourism & Antiquities ticket list; items marked * are estimates pending verification. 📍 opens the place in Google Maps.',

    'status.computing': 'Computing your optimal itinerary…',
    'summary.places': 'places', 'summary.of': 'of', 'summary.budget': 'budget',
    'summary.day': 'day', 'summary.days': 'days',
    'btn.login_to_save': 'Log in to save', 'btn.save_trip': 'Save this trip',
    'btn.print': 'Print / PDF', 'btn.ics': 'Add to calendar (.ics)', 'label.currency': 'Currency',
    'prompt.name_trip': 'Name this trip:', 'trip.default_name': 'trip',
    'save.ok': 'Trip saved — see', 'save.fail': 'Could not save (are you still logged in?)',
    'reset.all': 'reset all',

    'itin.day': 'Day', 'itin.route': 'Route ↗', 'itin.done_by': 'done by',
    'itin.after_hours': 'may run past closing',
    'itin.couldnt_fit': "Couldn't fit:", 'itin.try_more': 'try more days or hours.',
    'currency.free': 'Free',

    'mytrips.h1': 'My trips',
    'mytrips.sub': 'Your saved itineraries. Click one to see the full day-by-day plan.',
    'mytrips.empty': 'No saved trips yet — build one and hit “Save this trip”.',
    'mytrips.saved': 'saved', 'mytrips.shared': 'shared',
    'btn.view': 'View', 'btn.share': 'Share', 'btn.copy_link': 'Copy link',
    'btn.unshare': 'Unshare', 'btn.delete': 'Delete',
    'confirm.unshare': 'Unshare this trip? The existing link will stop working.',
    'confirm.delete': 'Delete this trip?', 'mytrips.revoked': 'Link revoked.',
    'mytrips.link_copied': 'Share link copied:', 'mytrips.link': 'Share link:',

    'share.subtitle': 'A shared itinerary', 'share.over': 'over',
    'share.in_tickets': 'in tickets',
    'share.invalid': 'This share link is invalid or was revoked by its owner.',
    'share.missing': 'Missing share token.',
    'share.footer': 'Shared via Tourist Companion',

    'login.tab_login': 'Log in', 'login.tab_register': 'Create account',
    'label.name': 'Name', 'label.email': 'Email', 'label.password': 'Password',
    'login.submit_login': 'Log in', 'login.submit_register': 'Create account',
    'login.creating': 'Creating your account…', 'login.logging': 'Logging in…',
    'login.bad_details': 'Please check your details (password must be at least 8 characters).',
  },

  ar: {
    brand: 'رفيق السائح',
    'nav.home': 'الرئيسية', 'nav.programs': 'البرامج', 'nav.build': 'صمّم رحلتك',
    'nav.mytrips': 'رحلاتي', 'nav.login': 'تسجيل الدخول', 'nav.logout': 'تسجيل الخروج',

    'home.eyebrow': 'مصر · خطط سياحية محسّنة',
    'home.h1': 'مصر، مُصمّمة من أجلك.',
    'home.hero_p': 'عجائب خالدة، مُخطّطة على ميزانيتك بالضبط بأسعار تذاكر حقيقية وموثّقة — برنامج يومي كامل في ثوانٍ.',
    'home.begin': 'ابدأ رحلتك', 'home.browse': 'تصفّح البرامج',
    'stat.sites': 'موقع موثّق', 'stat.cities': 'مدينة',
    'stat.prices': 'أسعار رسمية', 'stat.tiers': 'فئات أسعار للزوّار',
    'home.popular': 'أشهر البرامج',
    'home.popular_sub': 'رحلات مختارة — اختر واحدة ونحسب لك البرنامج الأمثل مباشرة.',
    'home.how': 'كيف يعمل',
    'home.how_sub': 'مُحسِّن دقيق لا تخمين — وجدول حقيقي يمكنك اتّباعه.',
    'home.step1_h': 'حدّد ميزانيتك',
    'home.step1_p': 'أخبرنا بميزانية التذاكر وعدد الأيام واهتماماتك — أجنبي أو مصري، بالغ أو طالب.',
    'home.step2_h': 'نُحسِّن الاختيار',
    'home.step2_p': 'خوارزمية دقيقة تختار أفضل مجموعة معالم تناسب ميزانيتك تمامًا.',
    'home.step3_h': 'اتبع الخطة',
    'home.step3_p': 'يومًا بيوم، مرتّبة حسب الموقع ومواعيد العمل — مع روابط الخرائط وتصدير التقويم.',
    'home.use_program': 'استخدم هذا البرنامج',
    'footer.prices': 'الأسعار من قائمة تذاكر وزارة السياحة والآثار المصرية.',
    'footer.plan_cta': 'خطّط لرحلتك →',

    'programs.h1': 'برامج جاهزة',
    'programs.sub': 'قوالب رحلات مختارة — اختر واحدة ونحسب لك البرنامج الأمثل مباشرة من أسعار التذاكر الرسمية. يمكنك تعديل كل شيء بعد ذلك.',

    'build.h1': 'صمّم رحلتك',
    'build.sub': 'حدّد ميزانيتك ووقتك — نحسب البرنامج الأمثل من معالم بأسعار رسمية. تفضّل قالبًا جاهزًا؟',
    'build.sub_link': 'شاهد البرامج الجاهزة.',
    'label.budget': 'الميزانية (ج.م، تذاكر)', 'label.days': 'الأيام',
    'label.hours': 'ساعات / اليوم', 'label.startdate': 'تاريخ البدء (اختياري)',
    'label.visitor': 'الزائر', 'opt.foreign': 'زائر أجنبي', 'opt.egyptian': 'مصري',
    'label.tickettype': 'نوع التذكرة', 'opt.adult': 'بالغ', 'opt.student': 'طالب',
    'label.spend': 'أسلوب الإنفاق', 'opt.value': 'اقتصادي',
    'opt.balanced': 'متوازن', 'opt.premium': 'فاخر (إسراف)',
    'label.interests': 'الاهتمامات (اضغط للتفضيل)',
    'chip.ancient': 'مصر القديمة', 'chip.islamic': 'القاهرة الإسلامية',
    'chip.coptic': 'التراث القبطي', 'chip.museum': 'المتاحف',
    'chip.palace': 'القصور', 'chip.experience': 'تجارب', 'chip.nature': 'الطبيعة والشواطئ',
    'build.submit': 'صمّم رحلتي',
    'build.footer': 'الأسعار من قائمة تذاكر وزارة السياحة والآثار المصرية؛ العناصر المعلّمة بـ * تقديرية بانتظار التأكيد. 📍 يفتح المكان في خرائط جوجل.',

    'status.computing': 'نحسب برنامجك الأمثل…',
    'summary.places': 'معالم', 'summary.of': 'من أصل', 'summary.budget': 'ميزانية',
    'summary.day': 'يوم', 'summary.days': 'أيام',
    'btn.login_to_save': 'سجّل الدخول للحفظ', 'btn.save_trip': 'احفظ هذه الرحلة',
    'btn.print': 'طباعة / PDF', 'btn.ics': 'أضف إلى التقويم (.ics)', 'label.currency': 'العملة',
    'prompt.name_trip': 'سمِّ هذه الرحلة:', 'trip.default_name': 'رحلة',
    'save.ok': 'تم حفظ الرحلة — انظر', 'save.fail': 'تعذّر الحفظ (هل ما زلت مسجّل الدخول؟)',
    'reset.all': 'إعادة تعيين الكل',

    'itin.day': 'اليوم', 'itin.route': 'المسار ↗', 'itin.done_by': 'ينتهي بحلول',
    'itin.after_hours': 'قد يتجاوز موعد الإغلاق',
    'itin.couldnt_fit': 'تعذّر تضمين:', 'itin.try_more': 'جرّب أيامًا أو ساعات أكثر.',
    'currency.free': 'مجاني',

    'mytrips.h1': 'رحلاتي',
    'mytrips.sub': 'رحلاتك المحفوظة. اضغط على أي رحلة لعرض الخطة الكاملة يومًا بيوم.',
    'mytrips.empty': 'لا توجد رحلات محفوظة بعد — صمّم واحدة واضغط «احفظ هذه الرحلة».',
    'mytrips.saved': 'حُفظت', 'mytrips.shared': 'مشاركة',
    'btn.view': 'عرض', 'btn.share': 'مشاركة', 'btn.copy_link': 'نسخ الرابط',
    'btn.unshare': 'إلغاء المشاركة', 'btn.delete': 'حذف',
    'confirm.unshare': 'إلغاء مشاركة هذه الرحلة؟ سيتوقف الرابط الحالي عن العمل.',
    'confirm.delete': 'حذف هذه الرحلة؟', 'mytrips.revoked': 'تم إلغاء الرابط.',
    'mytrips.link_copied': 'تم نسخ رابط المشاركة:', 'mytrips.link': 'رابط المشاركة:',

    'share.subtitle': 'برنامج مُشارَك', 'share.over': 'خلال',
    'share.in_tickets': 'في التذاكر',
    'share.invalid': 'رابط المشاركة غير صالح أو ألغاه صاحبه.',
    'share.missing': 'رمز المشاركة مفقود.',
    'share.footer': 'تمّت المشاركة عبر رفيق السائح',

    'login.tab_login': 'تسجيل الدخول', 'login.tab_register': 'إنشاء حساب',
    'label.name': 'الاسم', 'label.email': 'البريد الإلكتروني', 'label.password': 'كلمة المرور',
    'login.submit_login': 'تسجيل الدخول', 'login.submit_register': 'إنشاء حساب',
    'login.creating': 'جارٍ إنشاء حسابك…', 'login.logging': 'جارٍ تسجيل الدخول…',
    'login.bad_details': 'يرجى التحقق من بياناتك (كلمة المرور 8 أحرف على الأقل).',
  },
};

function getLang() { return localStorage.getItem('tc_lang') || 'en'; }

function t(key) {
  const l = getLang();
  return (I18N[l] && I18N[l][key]) || I18N.en[key] || key;
}

// day/days (or يوم/أيام) helper for counts
function tPlural(n) { return t(n === 1 ? 'summary.day' : 'summary.days'); }

(function () {                         // set dir/lang before paint, no flash
  const l = getLang();
  document.documentElement.setAttribute('lang', l);
  document.documentElement.setAttribute('dir', l === 'ar' ? 'rtl' : 'ltr');
})();

function translateDom(root) {
  root = root || document;
  root.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
  root.querySelectorAll('[data-i18n-html]').forEach(el => { el.innerHTML = t(el.dataset.i18nHtml); });
  root.querySelectorAll('[data-i18n-ph]').forEach(el => { el.setAttribute('placeholder', t(el.dataset.i18nPh)); });
  const tk = document.documentElement.dataset.i18nTitle;
  if (tk) document.title = t(tk);
}

function applyLang(lang) {
  localStorage.setItem('tc_lang', lang);
  document.documentElement.setAttribute('lang', lang);
  document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
  translateDom();
  updateLangToggles();
  document.dispatchEvent(new Event('langchange'));
}

function toggleLang() { applyLang(getLang() === 'ar' ? 'en' : 'ar'); }

function langToggleHtml() {
  const label = getLang() === 'ar' ? 'EN' : 'ع';
  return `<button class="lang-toggle" onclick="toggleLang()" aria-label="Switch language">${label}</button>`;
}

function updateLangToggles() {
  const label = getLang() === 'ar' ? 'EN' : 'ع';
  document.querySelectorAll('.lang-toggle').forEach(b => { b.textContent = label; });
}

document.addEventListener('DOMContentLoaded', () => { translateDom(); updateLangToggles(); });
