// Add a new language by adding a key here and an option in LANGUAGES.
export const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिंदी' },
]

export const translations = {
  en: {
    appName: 'ArogyaAI',
    tagline: 'General health information in simple language',
    nav: {
      dashboard: 'Home', chat: 'Assistant', reports: 'Reports', medicines: 'Medicines',
      hospitals: 'Hospitals', tips: 'Health Tips', emergency: 'Emergency', profile: 'Profile',
      patients: 'Patients', users: 'Users', logout: 'Log out', login: 'Log in', register: 'Sign up',
    },
    common: {
      loading: 'Loading…', save: 'Save', cancel: 'Cancel', delete: 'Delete', edit: 'Edit', add: 'Add',
      retry: 'Try again', search: 'Search', close: 'Close', yes: 'Yes', no: 'No', language: 'Language',
      disclaimer: 'ArogyaAI gives general health information. It is not a doctor and cannot diagnose. In an emergency call 112.',
    },
    dashboard: {
      greeting: 'Namaste',
      subtitle: 'What would you like to do today?',
      cards: {
        chat: ['AI Health Assistant', 'Ask a health question by typing'],
        voice: ['Voice Assistant', 'Speak in Hindi or English'],
        reports: ['Upload Report', 'Read text from a report or prescription'],
        medicines: ['Medicine Reminder', 'Your medicines and times'],
        hospitals: ['Find Hospital', 'Clinics and pharmacies near you'],
        emergency: ['Emergency SOS', 'Call numbers and share location'],
        tips: ['Health Tips', 'Simple daily wellness advice'],
      },
    },
    auth: {
      email: 'Email', password: 'Password', name: 'Full name', phone: 'Phone (optional)',
      loginTitle: 'Log in', registerTitle: 'Create your account',
      noAccount: 'New here?', haveAccount: 'Already have an account?',
    },
  },
  hi: {
    appName: 'आरोग्यAI',
    tagline: 'सरल भाषा में सामान्य स्वास्थ्य जानकारी',
    nav: {
      dashboard: 'होम', chat: 'सहायक', reports: 'रिपोर्ट', medicines: 'दवाइयाँ',
      hospitals: 'अस्पताल', tips: 'स्वास्थ्य सुझाव', emergency: 'आपातकाल', profile: 'प्रोफ़ाइल',
      patients: 'मरीज़', users: 'उपयोगकर्ता', logout: 'लॉग आउट', login: 'लॉग इन', register: 'साइन अप',
    },
    common: {
      loading: 'लोड हो रहा है…', save: 'सहेजें', cancel: 'रद्द करें', delete: 'हटाएं', edit: 'बदलें', add: 'जोड़ें',
      retry: 'फिर कोशिश करें', search: 'खोजें', close: 'बंद करें', yes: 'हाँ', no: 'नहीं', language: 'भाषा',
      disclaimer: 'आरोग्यAI सामान्य स्वास्थ्य जानकारी देता है। यह डॉक्टर नहीं है और निदान नहीं कर सकता। आपातकाल में 112 पर कॉल करें।',
    },
    dashboard: {
      greeting: 'नमस्ते',
      subtitle: 'आज आप क्या करना चाहेंगे?',
      cards: {
        chat: ['एआई स्वास्थ्य सहायक', 'टाइप करके स्वास्थ्य प्रश्न पूछें'],
        voice: ['वॉइस सहायक', 'हिंदी या अंग्रेज़ी में बोलें'],
        reports: ['रिपोर्ट अपलोड करें', 'रिपोर्ट या पर्चे से पाठ पढ़ें'],
        medicines: ['दवा की याद', 'आपकी दवाइयाँ और समय'],
        hospitals: ['अस्पताल खोजें', 'पास के क्लिनिक और दवाखाने'],
        emergency: ['आपातकालीन SOS', 'कॉल नंबर और लोकेशन साझा करें'],
        tips: ['स्वास्थ्य सुझाव', 'रोज़ की सरल सलाह'],
      },
    },
    auth: {
      email: 'ईमेल', password: 'पासवर्ड', name: 'पूरा नाम', phone: 'फ़ोन (वैकल्पिक)',
      loginTitle: 'लॉग इन करें', registerTitle: 'अपना खाता बनाएं',
      noAccount: 'नए हैं?', haveAccount: 'पहले से खाता है?',
    },
  },
}
