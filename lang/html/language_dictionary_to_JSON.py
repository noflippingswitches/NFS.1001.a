# Copyright (c) 2023 One DB Ventures, LLC (AKA, No Flipping Switches)

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json


# writes dictionary to a json file
def dictionary_to_json(python_dictionary, path_and_or_file_name_to_json):
    with open(path_and_or_file_name_to_json, "w") as outfile:
        # noinspection PyTypeChecker
        json.dump(python_dictionary, outfile)


# english
language_en = {
    "Network": "Network",
    "Scan": "Scan",
    "SSID_Network_Name": "SSID Network Name",
    "Password": "Password",
    "Static": "Static",
    "DHCP": "DHCP",
    "IP_Address": "IP Address",
    "Subnet_Mask": "Subnet Mask",
    "Gateway": "Gateway",
    "DNS_Server": "DNS Server",
    "Apply": "Apply",
    "WiFi": "Wifi",
    "Sensor": "Sensor",
    "Data": "Data",
    "Disconnecting_WiFi_access_point": "Disconnecting WiFi access point",
    "Scanning_WiFi_networks": "Scanning WiFi networks",
    "Webpage_will_automatically_refresh": "Webpage will automatically refresh",
    "Please_wait_x_seconds": "Please wait 15 seconds",
    "Signal_Quality": "Signal Quality",
    "Channel": "Channel",
    "Security": "Security",
    "Tempature": "Tempature",
    "Take_Reading_Every": "Take Reading Every",
    "Send_Readings_Every": "Send Readings Every",
    "Minutes": "Minutes",
    "Hours": "Hours"
}
dictionary_to_json(language_en, 'language_en.json')

# chinese
language_zh = {
    "Network": "网络",
    "Scan": "扫描",
    "SSID_Network_Name": "SSID 网络名称",
    "Password": "密码",
    "Static": "静止的",
    "DHCP": "DHCP",
    "IP_Address": "IP地址",
    "Subnet_Mask": "子网掩码",
    "Gateway": "网关",
    "DNS_Server": "域名系统",
    "Apply": "应用",
    "WiFi": "无线上网",
    "Sensor": "传感器",
    "Data": "数据",
    "Disconnecting_WiFi_access_point": "断开 无线上网 接入点",
    "Scanning_WiFi_networks": "扫描 无线上网 网络",
    "Webpage_will_automatically_refresh": "网页会自动刷新",
    "Please_wait_x_seconds": "请等待 15 秒",
    "Signal_Quality": "信号质量",
    "Channel": "频道",
    "Security": "安全",
    "Tempature": "温",
    "Take_Reading_Every": "进行测量各个",
    "Send_Readings_Every": "发送测量每",
    "Minutes": "分钟",
    "Hours": "小时"
}
dictionary_to_json(language_zh, 'language_zh.json')

# spanish
language_es = {
    "Network": "Red",
    "Scan": "Explorar",
    "SSID_Network_Name": "SSID Nombre de red",
    "Password": "Contraseña",
    "Static": "Estático",
    "DHCP": "DHCP",
    "IP_Address": "Dirección IP",
    "Subnet_Mask": "Máscara de subred",
    "Gateway": "Puerta",
    "DNS_Server": "Servidor DNS",
    "Apply": "Aplicar",
    "WiFi": "Wifi",
    "Sensor": "Sensor",
    "Data": "Datos",
    "Disconnecting_WiFi_access_point": "Desconectar el punto de acceso WiFi",
    "Scanning_WiFi_networks": "Escaneo de redes WiFi",
    "Webpage_will_automatically_refresh": "La página web se actualizará automáticamente",
    "Please_wait_x_seconds": "Espere 15 segundos",
    "Signal_Quality": "Calidad de la señal",
    "Channel": "Canal",
    "Security": "Seguridad",
    "Tempature": "Temperatura",
    "Take_Reading_Every": "Tomar lectura cada",
    "Send_Readings_Every": "Enviar lecturas cada",
    "Minutes": "Minutos",
    "Hours": "Horas"
}
dictionary_to_json(language_es, 'language_es.json')

# arabic
language_ar = {
    "Network": "شبكة",
    "Scan": "تفحص",
    "SSID_Network_Name": "اسم شبكة SSID",
    "Password": "كلمة المرور",
    "Static": "جامد",
    "DHCP": "DHCP",
    "IP_Address": "عنوان IP",
    "Subnet_Mask": "قناع الشبكة الفرعية",
    "Gateway": "بوابة",
    "DNS_Server": "خادم DNS",
    "Apply": "طبق",
    "WiFi": "واي فاي",
    "Sensor": "المستشعر",
    "Data": "بيانات",
    "Disconnecting_WiFi_access_point": "فصل نقطة وصول واي فاي",
    "Scanning_WiFi_networks": "مسح شبكات واي فاي",
    "Webpage_will_automatically_refresh": "سيتم تحديث صفحة الويب تلقائيًا",
    "Please_wait_x_seconds": "من فضلك انتظر 15 ثانية",
    "Signal_Quality": "جودة إشارات",
    "Channel": "قناة",
    "Security": "حماية",
    "Tempature": "درجة حرارة",
    "Take_Reading_Every": "خذ قراءة كل",
    "Send_Readings_Every": "إرسال قراءات كل",
    "Minutes": "دقائق",
    "Hours": "ساعات"
}
dictionary_to_json(language_ar, 'language_ar.json')

# japanese
language_ja = {
    "Network": "通信網",
    "Scan": "スキャン",
    "SSID_Network_Name": "SSID ネットワーク名",
    "Password": "パスワード",
    "Static": "静的",
    "DHCP": "DHCP",
    "IP_Address": "IPアドレス",
    "Subnet_Mask": "サブネットマスク",
    "Gateway": "ゲートウェイ",
    "DNS_Server": "DNS サーバー",
    "Apply": "申し込み",
    "WiFi": "Wifi",
    "Sensor": "センサー",
    "Data": "データ",
    "Disconnecting_WiFi_access_point": "WiFiアクセスポイントの切断",
    "Scanning_WiFi_networks": "WiFi ネットワークのスキャン",
    "Webpage_will_automatically_refresh": "ウェブページは自動的に更新されます",
    "Please_wait_x_seconds": "15 秒お待ちください",
    "Signal_Quality": "信号品質",
    "Channel": "チャネル",
    "Security": "安全",
    "Tempature": "温度",
    "Take_Reading_Every": "測定間隔",
    "Send_Readings_Every": "送信間隔",
    "Minutes": "分",
    "Hours": "時間"
}
dictionary_to_json(language_ja, 'language_ja.json')

# german
language_de = {
    "Network": "Netzwerk",
    "Scan": "Scan",
    "SSID_Network_Name": "SSID-Netzwerkname",
    "Password": "Passwort",
    "Static": "Statische",
    "DHCP": "DHCP",
    "IP_Address": "IP Adresse",
    "Subnet_Mask": "Subnetzmaske",
    "Gateway": "Tor",
    "DNS_Server": "DNS Server",
    "Apply": "Anwenden",
    "WiFi": "W-lan",
    "Sensor": "Sensor",
    "Data": "Daten",
    "Disconnecting_WiFi_access_point": "WLAN-Zugangspunkt trennen",
    "Scanning_WiFi_networks": "WLAN-Netzwerke scannen",
    "Webpage_will_automatically_refresh": "Die Webseite wird automatisch aktualisiert",
    "Please_wait_x_seconds": "Bitte warten Sie 15 Sekunden",
    "Signal_Quality": "Signalqualität",
    "Channel": "Kanal",
    "Security": "Sicherheit",
    "Tempature": "Temperatur",
    "Take_Reading_Every": "Lesen Sie jeden",
    "Send_Readings_Every": "Messwerte senden alle",
    "Minutes": "Protokoll",
    "Hours": "stunden"
}
dictionary_to_json(language_de, 'language_de.json')

# russian
language_ru = {
    "Network": "сеть",
    "Scan": "Сканировать",
    "SSID_Network_Name": "Имя сети SSID",
    "Password": "Пароль",
    "Static": "Статический",
    "DHCP": "DHCP",
    "IP_Address": "Айпи адрес",
    "Subnet_Mask": "Маска подсети",
    "Gateway": "Шлюз",
    "DNS_Server": "DNS-сервер",
    "Apply": "Применять",
    "WiFi": "Wifi",
    "Sensor": "Датчик",
    "Data": "Данные",
    "Disconnecting_WiFi_access_point": "Отключение точки доступа Wi-Fi",
    "Scanning_WiFi_networks": "Сканирование WiFi-сетей",
    "Webpage_will_automatically_refresh": "Веб-страница будет автоматически обновляться",
    "Please_wait_x_seconds": "Пожалуйста, подождите 15 секунд",
    "Signal_Quality": "Качество сигнала",
    "Channel": "Канал",
    "Security": "Безопасность",
    "Tempature": "Температура",
    "Take_Reading_Every": "Возьмите чтение каждый",
    "Send_Readings_Every": "Отправляйте показания каждые",
    "Minutes": "Минуты",
    "Hours": "Часы"
}
dictionary_to_json(language_ru, 'language_ru.json')

# hindi
language_hi = {
    "Network": "नेटवर्क",
    "Scan": "स्कैन",
    "SSID_Network_Name": "एसएसआईडी नेटवर्क का नाम",
    "Password": "पासवर्ड",
    "Static": "स्थिर",
    "DHCP": "DHCP",
    "IP_Address": "आईपी ​​पता",
    "Subnet_Mask": "सबनेट मास्क",
    "Gateway": "द्वार",
    "DNS_Server": "डीएनएस सर्वर",
    "Apply": "आवेदन करना",
    "WiFi": "Wifi",
    "Sensor": "सेंसर",
    "Data": "आंकड़े",
    "Disconnecting_WiFi_access_point": "वाईफाई एक्सेस प्वाइंट को डिस्कनेक्ट कर रहा है",
    "Scanning_WiFi_networks": "वाईफाई नेटवर्क स्कैन कर रहा है",
    "Webpage_will_automatically_refresh": "वेबपेज अपने आप रिफ्रेश हो जाएगा",
    "Please_wait_x_seconds": "कृपया 15 सेकंड प्रतीक्षा करें",
    "Signal_Quality": "सिग्नल की गुणवत्ता",
    "Channel": "चैनल",
    "Security": "सुरक्षा",
    "Tempature": "तापमान",
    "Take_Reading_Every": "प्रत्येक पढ़ना लो",
    "Send_Readings_Every": " रीडिंग हर भेजें",
    "Minutes": "मिनट",
    "Hours": "घंटे"
}
dictionary_to_json(language_hi, 'language_hi.json')

# portuguese
language_pt = {
    "Network": "rede",
    "Scan": "Varredura",
    "SSID_Network_Name": "Nome da rede SSID",
    "Password": "Senha",
    "Static": "Estático",
    "DHCP": "DHCP",
    "IP_Address": "Endereço de IP",
    "Subnet_Mask": "máscara de sub-rede",
    "Gateway": "Porta de entrada",
    "DNS_Server": "Servidor dns",
    "Apply": "Aplicar",
    "WiFi": "Wifi",
    "Sensor": "Sensor",
    "Data": "Dados",
    "Disconnecting_WiFi_access_point": "Desconectando o ponto de acesso WiFi",
    "Scanning_WiFi_networks": "Escaneando redes Wi-Fi",
    "Webpage_will_automatically_refresh": "A página da Web será atualizada automaticamente",
    "Please_wait_x_seconds": "Aguarde 15 segundos",
    "Signal_Quality": "Qualidade do sinal",
    "Channel": "Canal",
    "Security": "Segurança",
    "Tempature": "Temperatura",
    "Take_Reading_Every": "Faça a leitura a cada",
    "Send_Readings_Every": "Enviar leituras a cada",
    "Minutes": "Minutos",
    "Hours": "Horas"
}
dictionary_to_json(language_pt, 'language_pt.json')

# french
language_fr = {
    "Network": "Réseau",
    "Scan": "Analyse",
    "SSID_Network_Name": "Nom du réseau SSID",
    "Password": "Mot de passe",
    "Static": "Statique",
    "DHCP": "DHCP",
    "IP_Address": "Adresse IP",
    "Subnet_Mask": "Masque de sous-réseau",
    "Gateway": "passerelle",
    "DNS_Server": "Serveur DNS",
    "Apply": "Appliquer",
    "WiFi": "Wifi",
    "Sensor": "détecteur",
    "Data": "Donnés",
    "Disconnecting_WiFi_access_point": "Déconnexion du point d'accès WiFi",
    "Scanning_WiFi_networks": "Balayage des réseaux Wi-Fi",
    "Webpage_will_automatically_refresh": "La page Web sera automatiquement actualisée",
    "Please_wait_x_seconds": "Veuillez patienter 15 secondes",
    "Signal_Quality": "Qualidade do sinal",
    "Channel": "Canal",
    "Security": "Segurança",
    "Tempature": "Température",
    "Take_Reading_Every": "Prenez la lecture chaque",
    "Send_Readings_Every": "Envoyer des lectures chaque",
    "Minutes": "Minutes",
    "Hours": "Heures"
}
dictionary_to_json(language_fr, 'language_fr.json')
