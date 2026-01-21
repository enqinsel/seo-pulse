#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEO-Pulse: Profesyonel Web Performans İzleme ve Rekabet Analizi Aracı

Bu araç:
- sites tablosundaki web sitelerini tarar
- Google PageSpeed Insights API ile performans verilerini çeker
- Veritabanına kaydeder
- Rekabetçi analiz raporu hazırlayıp mail atar

Geliştirici: SEO-Pulse Team
Versiyon: 2.0.0
"""

import os
import sys
import time
import smtplib
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any
from email.message import EmailMessage
from email.header import Header
from email.utils import formataddr
from supabase import create_client, Client
from dotenv import load_dotenv

# ═══════════════════════════════════════════════════════════════════════════════
# YAPILANDIRMA VE SABİTLER
# ═══════════════════════════════════════════════════════════════════════════════

load_dotenv()

class Config:
    """Uygulama yapılandırma sabitleri."""
    
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    PAGESPEED_KEY: str = os.getenv("PAGESPEED_API_KEY", "")
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    
    # API Ayarları
    API_RATE_LIMIT_SECONDS: int = 5
    PAGESPEED_API_URL: str = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    STRATEGY: str = "mobile"
    
    # Site label sabitler
    MY_SITE_LABEL: str = "Benim Sitem"
    
    @classmethod
    def validate(cls) -> bool:
        """Gerekli yapılandırmaların mevcut olduğunu kontrol eder."""
        required = [cls.SUPABASE_URL, cls.SUPABASE_KEY, cls.PAGESPEED_KEY, 
                    cls.EMAIL_SENDER, cls.EMAIL_PASSWORD]
        return all(required)


# ═══════════════════════════════════════════════════════════════════════════════
# TÜRKÇE TAVSİYE ÇEVİRİLERİ
# ═══════════════════════════════════════════════════════════════════════════════

# PageSpeed audit ID'leri için Türkçe çeviriler ve aksiyonlar
AUDIT_TRANSLATIONS = {
    "render-blocking-resources": {
        "title": "🚫 Render Engelleyen Kaynakları Azaltın",
        "action": "CSS ve JavaScript dosyalarını async/defer ile yükleyin. Kritik CSS'i inline yapın."
    },
    "unused-javascript": {
        "title": "📦 Kullanılmayan JavaScript'i Kaldırın",
        "action": "Kullanılmayan JS kodlarını tespit edip silin. Code splitting uygulayın."
    },
    "unused-css-rules": {
        "title": "🎨 Kullanılmayan CSS'i Temizleyin",
        "action": "PurgeCSS veya benzeri araçlarla kullanılmayan stilleri kaldırın."
    },
    "unminified-javascript": {
        "title": "📉 JavaScript'i Sıkıştırın",
        "action": "Terser veya UglifyJS ile JS dosyalarını minify edin."
    },
    "unminified-css": {
        "title": "📉 CSS'i Sıkıştırın",
        "action": "CSS dosyalarını cssnano veya benzeri araçlarla minify edin."
    },
    "modern-image-formats": {
        "title": "🖼️ Modern Görsel Formatlarına Geçin",
        "action": "JPEG/PNG yerine WebP veya AVIF formatlarını kullanın. %25-50 tasarruf sağlar."
    },
    "uses-optimized-images": {
        "title": "🖼️ Görselleri Optimize Edin",
        "action": "Görselleri sıkıştırın (TinyPNG, ImageOptim). Boyutları küçültün."
    },
    "offscreen-images": {
        "title": "📸 Görünmeyen Görselleri Lazy Load Yapın",
        "action": "loading='lazy' özelliğini ekleyin. Viewport dışındaki görselleri erteleyin."
    },
    "uses-responsive-images": {
        "title": "📱 Responsive Görseller Kullanın",
        "action": "srcset ve sizes özelliklerini kullanarak farklı ekranlara uygun görseller sunun."
    },
    "efficiently-encode-images": {
        "title": "🔧 Görselleri Verimli Kodlayın",
        "action": "Görselleri JPEG quality 80-85 ile optimize edin."
    },
    "uses-text-compression": {
        "title": "📦 Metin Sıkıştırma (Gzip/Brotli) Etkinleştirin",
        "action": "Sunucu ayarlarından Gzip veya Brotli sıkıştırmayı aktif edin."
    },
    "uses-rel-preconnect": {
        "title": "🔗 Erken Bağlantı Kurulumunu Etkinleştirin",
        "action": "3. parti kaynaklara <link rel='preconnect'> ekleyin."
    },
    "uses-rel-preload": {
        "title": "⚡ Kritik Kaynakları Önceden Yükleyin",
        "action": "Önemli font ve CSS dosyalarına <link rel='preload'> ekleyin."
    },
    "server-response-time": {
        "title": "🖥️ Sunucu Yanıt Süresini Azaltın (TTFB)",
        "action": "CDN kullanın, veritabanı sorgularını optimize edin, caching ekleyin."
    },
    "redirects": {
        "title": "🔀 Yönlendirmeleri Azaltın",
        "action": "Gereksiz redirect zincirlerini kaldırın. Doğrudan URL'lere yönlendirin."
    },
    "uses-http2": {
        "title": "🌐 HTTP/2 Protokolünü Kullanın",
        "action": "Sunucunuzu HTTP/2 destekleyecek şekilde yapılandırın."
    },
    "dom-size": {
        "title": "📄 DOM Boyutunu Küçültün",
        "action": "Gereksiz HTML elementlerini kaldırın. Virtual scrolling uygulayın."
    },
    "critical-request-chains": {
        "title": "⛓️ Kritik İstek Zincirlerini Kısaltın",
        "action": "Kritik kaynakları inline yapın veya preload ile önceden yükleyin."
    },
    "bootup-time": {
        "title": "⏱️ JavaScript Çalışma Süresini Azaltın",
        "action": "Ağır JS işlemlerini Web Worker'lara taşıyın. Code splitting yapın."
    },
    "mainthread-work-breakdown": {
        "title": "🧵 Ana İş Parçacığı Yükünü Azaltın",
        "action": "JS çalışmasını optimize edin. Uzun görevleri parçalara ayırın."
    },
    "font-display": {
        "title": "🔤 Font Görüntüleme Stratejisini Optimize Edin",
        "action": "font-display: swap kullanarak FOIT sorununu önleyin."
    },
    "third-party-summary": {
        "title": "🔌 3. Parti Scriptleri Optimize Edin",
        "action": "Gereksiz 3. parti scriptleri kaldırın veya erteleyin (analytics, chat widget vb.)"
    },
    "largest-contentful-paint-element": {
        "title": "🎯 LCP Elementini Optimize Edin",
        "action": "Ana hero görselini preload yapın. CDN kullanın. Boyutunu küçültün."
    },
    "lcp-lazy-loaded": {
        "title": "⚠️ LCP Görseli Lazy Load Edilmiş",
        "action": "LCP (hero) görselinden loading='lazy' özelliğini kaldırın!"
    },
    "total-blocking-time": {
        "title": "⏳ Toplam Engelleme Süresini Azaltın",
        "action": "Uzun JavaScript görevlerini bölün. Ana thread'i serbest bırakın."
    },
    "cumulative-layout-shift": {
        "title": "📐 Görsel Kaymaları (CLS) Engelleyin",
        "action": "Görsel ve iframe'lere width/height ekleyin. Font FOUT'unu önleyin."
    },
    "prioritize-lcp-image": {
        "title": "🖼️ LCP Görselini Önceliklendirin",
        "action": "fetchpriority='high' ve preload ile LCP görselini önceliklendirin."
    },
    "legacy-javascript": {
        "title": "📜 Eski JavaScript Polyfill'leri Kaldırın",
        "action": "Modern tarayıcılar için gereksiz polyfill'leri kaldırın."
    },
    "duplicated-javascript": {
        "title": "📦 Tekrarlanan JS Modüllerini Temizleyin",
        "action": "Webpack/Rollup bundle analizi yapın, duplicate modülleri kaldırın."
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# LOGGER UTILITY
# ═══════════════════════════════════════════════════════════════════════════════

class Logger:
    """Detaylı ve renkli terminal log yöneticisi."""
    
    @staticmethod
    def _timestamp() -> str:
        """Geçerli zaman damgasını döndürür."""
        return datetime.now().strftime("%H:%M:%S")
    
    @staticmethod
    def info(message: str) -> None:
        """Bilgi mesajı loglar."""
        print(f"[{Logger._timestamp()}] ℹ️  {message}")
    
    @staticmethod
    def success(message: str) -> None:
        """Başarı mesajı loglar."""
        print(f"[{Logger._timestamp()}] ✅ {message}")
    
    @staticmethod
    def warning(message: str) -> None:
        """Uyarı mesajı loglar."""
        print(f"[{Logger._timestamp()}] ⚠️  {message}")
    
    @staticmethod
    def error(message: str) -> None:
        """Hata mesajı loglar."""
        print(f"[{Logger._timestamp()}] ❌ {message}")
    
    @staticmethod
    def progress(message: str) -> None:
        """İlerleme mesajı loglar."""
        print(f"[{Logger._timestamp()}] → {message}")
    
    @staticmethod
    def wait(message: str) -> None:
        """Bekleme mesajı loglar."""
        print(f"[{Logger._timestamp()}] ⏳ {message}")
    
    @staticmethod
    def separator() -> None:
        """Görsel ayırıcı yazdırır."""
        print("─" * 60)


# ═══════════════════════════════════════════════════════════════════════════════
# VERITABANI YÖNETİCİSİ
# ═══════════════════════════════════════════════════════════════════════════════

class DatabaseManager:
    """Supabase veritabanı işlemlerini yönetir."""
    
    def __init__(self):
        """Supabase bağlantısını başlatır."""
        try:
            self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
            Logger.success("Supabase bağlantısı kuruldu")
        except Exception as e:
            Logger.error(f"Supabase bağlantı hatası: {e}")
            raise
    
    def get_sites(self) -> List[Dict[str, Any]]:
        """Takip edilen tüm siteleri çeker."""
        try:
            response = self.client.table("sites").select("*").execute()
            sites = response.data
            Logger.info(f"{len(sites)} site bulundu")
            return sites
        except Exception as e:
            Logger.error(f"Siteler çekilemedi: {e}")
            return []
    
    def save_speed_log(self, site_id: int, metrics: Dict[str, Any]) -> Optional[int]:
        """
        Performans verilerini speed_logs tablosuna kaydeder.
        
        Args:
            site_id: Site ID'si
            metrics: Performans metrikleri (score, lcp, cls, recommendations)
            
        Returns:
            Eklenen kaydın ID'si veya None
        """
        try:
            data = {
                "site_id": site_id,
                "performance_score": metrics["score"],
                "lcp_speed": metrics["lcp"],
                "cls_score": metrics["cls"],
                "recommendations": metrics["recommendations"]
            }
            response = self.client.table("speed_logs").insert(data).execute()
            
            if response.data:
                record_id = response.data[0].get("id", "N/A")
                Logger.success(f"Veritabanına kaydedildi (ID: {record_id})")
                return record_id
            return None
        except Exception as e:
            Logger.error(f"Veritabanı kayıt hatası: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# PAGESPEED ANALİZCİ
# ═══════════════════════════════════════════════════════════════════════════════

class PageSpeedAnalyzer:
    """Google PageSpeed Insights API ile performans analizi yapar."""
    
    @staticmethod
    def extract_smart_recommendations(audits: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Zeki tavsiye sistemi: Google'dan gelen audits verileri içinden
        details.type == 'opportunity' olan ve skoru 0.9'un altındaki
        TÜM fırsatları tasarruf miktarına göre sıralayarak döndürür.
        
        Args:
            audits: Lighthouse audit verileri
            
        Returns:
            Tüm önemli tavsiyelerin listesi (başlık, aksiyon ve displayValue)
        """
        opportunities = []
        
        for audit_id, audit_data in audits.items():
            # Sadece opportunity tipindeki auditleri al
            details = audit_data.get("details", {})
            audit_type = details.get("type", "")
            
            # Score kontrolü (0.9'un altında olanlar sorunlu)
            score = audit_data.get("score")
            if score is None or score >= 0.9:
                continue
            
            # Opportunity tipi kontrolü veya önemli metrikler
            is_opportunity = audit_type == "opportunity"
            has_savings = "overallSavingsMs" in details or "overallSavingsBytes" in details
            
            if is_opportunity or has_savings:
                # Tasarruf miktarını hesapla (ms olarak)
                savings_ms = details.get("overallSavingsMs", 0)
                savings_bytes = details.get("overallSavingsBytes", 0)
                
                # Bytes'ı da ms eşdeğerine çevir (yaklaşık)
                total_savings = savings_ms + (savings_bytes / 1000)
                
                # Türkçe çeviri varsa kullan, yoksa orijinal başlığı kullan
                translation = AUDIT_TRANSLATIONS.get(audit_id, {})
                tr_title = translation.get("title", audit_data.get("title", "Bilinmeyen Tavsiye"))
                tr_action = translation.get("action", audit_data.get("description", "")[:150])
                
                # Tasarruf bilgisini formatla
                savings_text = ""
                display_value = audit_data.get("displayValue", "")
                
                if savings_ms > 0:
                    savings_text = f" (~{int(savings_ms)}ms tasarruf)"
                elif savings_bytes > 0:
                    savings_kb = savings_bytes / 1024
                    savings_text = f" (~{int(savings_kb)}KB tasarruf)"
                
                opportunities.append({
                    "audit_id": audit_id,
                    "title": tr_title,
                    "action": tr_action + savings_text,
                    "display_value": display_value,
                    "savings": total_savings,
                    "score": score,
                    "savings_ms": savings_ms,
                    "savings_bytes": savings_bytes
                })
        
        # Tasarruf miktarına göre sırala (yüksekten düşüğe)
        opportunities.sort(key=lambda x: x["savings"], reverse=True)
        
        # TÜM tavsiyeleri döndür (sınırlama yok)
        return [
            {
                "title": opp["title"],
                "action": opp["action"],
                "display_value": opp["display_value"],
                "savings_ms": opp["savings_ms"],
                "savings_bytes": opp["savings_bytes"]
            }
            for opp in opportunities
        ]
    
    @staticmethod
    def analyze(url: str) -> Optional[Dict[str, Any]]:
        """
        Belirtilen URL için PageSpeed analizi yapar.
        
        Args:
            url: Analiz edilecek site URL'si
            
        Returns:
            Performans metrikleri veya None (hata durumunda)
        """
        # URL'yi temizle (başta/sonda boşluk olabilir)
        url = url.strip()
        
        Logger.progress(f"Taranıyor: {url}")
        
        # URL'yi güvenli hale getir
        from urllib.parse import quote, urlencode
        safe_url = quote(url, safe=':/?=&')
        
        params = {
            "url": safe_url,
            "key": Config.PAGESPEED_KEY,
            "strategy": Config.STRATEGY,
            "category": "performance"
        }
        
        try:
            response = requests.get(Config.PAGESPEED_API_URL, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            # Lighthouse sonuçlarını çıkar
            lighthouse = data.get("lighthouseResult", {})
            categories = lighthouse.get("categories", {})
            audits = lighthouse.get("audits", {})
            
            # Performance skoru (0-100 arasında)
            perf_category = categories.get("performance", {})
            score = int((perf_category.get("score", 0) or 0) * 100)
            
            # LCP (Largest Contentful Paint) - saniye cinsinden
            lcp_audit = audits.get("largest-contentful-paint", {})
            lcp_ms = lcp_audit.get("numericValue", 0)
            lcp_seconds = round(lcp_ms / 1000, 2)  # ms -> saniye
            
            # CLS (Cumulative Layout Shift) - değişiklik skoru
            cls_audit = audits.get("cumulative-layout-shift", {})
            cls_value = round(cls_audit.get("numericValue", 0), 4)
            
            # Zeki tavsiye sistemi ile önerileri ayıkla
            recommendations = PageSpeedAnalyzer.extract_smart_recommendations(audits)
            
            # Sonuç logla
            Logger.success(f"Analiz tamamlandı: {score}/100 | LCP: {lcp_seconds}s | CLS: {cls_value}")
            
            return {
                "score": score,
                "lcp": lcp_seconds,
                "cls": cls_value,
                "recommendations": recommendations
            }
            
        except requests.exceptions.Timeout:
            Logger.error(f"Zaman aşımı: {url} - API yanıt vermedi")
            return None
        except requests.exceptions.HTTPError as e:
            # API anahtarını gizle
            safe_error = str(e).replace(Config.PAGESPEED_KEY, "REDACTED")
            Logger.error(f"HTTP hatası: {url}")
            Logger.error(f"  └─ Durum Kodu: {response.status_code}")
            
            # Detaylı hata mesajını göster
            try:
                error_json = response.json()
                error_message = error_json.get("error", {}).get("message", "Bilinmeyen hata")
                error_reason = error_json.get("error", {}).get("errors", [{}])[0].get("reason", "")
                Logger.error(f"  └─ API Mesajı: {error_message}")
                if error_reason:
                    Logger.error(f"  └─ Sebep: {error_reason}")
            except:
                # JSON parse edilemezse text olarak göster (anahtarı gizle)
                error_text = response.text[:300].replace(Config.PAGESPEED_KEY, "REDACTED")
                Logger.error(f"  └─ Yanıt: {error_text}")
            
            return None
        except requests.exceptions.RequestException as e:
            safe_error = str(e).replace(Config.PAGESPEED_KEY, "REDACTED")
            Logger.error(f"Bağlantı hatası: {url} - {safe_error}")
            return None
        except KeyError as e:
            Logger.error(f"Veri ayrıştırma hatası: {url} - Eksik alan: {e}")
            return None
        except Exception as e:
            safe_error = str(e).replace(Config.PAGESPEED_KEY, "REDACTED")
            Logger.error(f"Beklenmeyen hata: {url} - {safe_error}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# RAPOR OLUŞTURUCU
# ═══════════════════════════════════════════════════════════════════════════════

class ReportGenerator:
    """Profesyonel e-posta raporu oluşturur ve gönderir."""
    
    @staticmethod
    def generate_report(my_site: Dict[str, Any], competitors: List[Dict[str, Any]]) -> str:
        """
        Şık formatlı karşılaştırmalı rapor oluşturur.
        
        Args:
            my_site: Bizim sitemizin verileri
            competitors: Rakip sitelerin verileri
            
        Returns:
            Formatlanmış rapor metni
        """
        date_str = datetime.now().strftime("%d %B %Y")
        
        # Rapor başlığı
        report = []
        report.append("╔" + "═" * 58 + "╗")
        report.append("║" + "🚀 SEO-PULSE PERFORMANS RAPORU".center(58) + "║")
        report.append("║" + date_str.center(58) + "║")
        report.append("╠" + "═" * 58 + "╣")
        
        # Sitemiz bölümü
        report.append("║" + " 📊 SİTEMİZ".ljust(58) + "║")
        report.append("║" + f"    URL: {my_site['url']}".ljust(58) + "║")
        metrics_line = f"    Performance: {my_site['score']}/100 | LCP: {my_site['lcp']}s | CLS: {my_site['cls']}"
        report.append("║" + metrics_line.ljust(58) + "║")
        report.append("╠" + "═" * 58 + "╣")
        
        # Rakip karşılaştırması
        report.append("║" + " 🏁 RAKİP KARŞILAŞTIRMASI".ljust(58) + "║")
        report.append("║" + " ".ljust(58) + "║")
        
        for comp in competitors:
            diff = my_site['score'] - comp['score']
            if diff > 0:
                status = f"✅ {comp['label']}"
                detail = f"→ {comp['score']} puan ({diff} puan gerideler)"
            elif diff < 0:
                status = f"⚠️  {comp['label']}"
                detail = f"→ {comp['score']} puan ({abs(diff)} puan ÖNDEler!)"
            else:
                status = f"🔄 {comp['label']}"
                detail = f"→ {comp['score']} puan (Eşit)"
            
            line = f"    {status.ljust(25)} {detail}"
            report.append("║" + line.ljust(58) + "║")
        
        report.append("╠" + "═" * 58 + "╣")
        
        # Action Items bölümü
        report.append("║" + " 📋 YAPILMASI GEREKENLER (Action Items)".ljust(58) + "║")
        report.append("║" + " ".ljust(58) + "║")
        
        if my_site.get('recommendations'):
            total_recs = len(my_site['recommendations'])
            report.append("║" + f"    Toplam {total_recs} iyileştirme fırsatı bulundu:".ljust(58) + "║")
            report.append("║" + " ".ljust(58) + "║")
            
            for i, rec in enumerate(my_site['recommendations'], 1):
                # Öncelik belirleme ve emoji (ilk 3 kritik, sonrakiler normal)
                if i == 1:
                    priority_emoji = "🔴"
                elif i <= 3:
                    priority_emoji = "🟠"
                else:
                    priority_emoji = "🟡"
                
                # Tavsiye başlığı (kısa)
                title = rec.get('title', 'Bilinmeyen')
                # Emoji varsa koru, başlığı kısalt
                if len(title) > 48:
                    title = title[:45] + "..."
                
                # displayValue (Google'dan gelen tasarruf bilgisi)
                display_val = rec.get('display_value', '')
                if display_val:
                    display_val = f" [{display_val}]"
                
                # Numara + Başlık satırı
                title_line = f"    {priority_emoji} {i}. {title}"
                if len(title_line) > 56:
                    title_line = title_line[:53] + "..."
                report.append("║" + title_line.ljust(58) + "║")
                
                # displayValue göster (varsa)
                if display_val:
                    dv_line = f"       Potansiyel Kazanç: {display_val}"
                    if len(dv_line) > 56:
                        dv_line = dv_line[:53] + "..."
                    report.append("║" + dv_line.ljust(58) + "║")
                
                # Aksiyon satırı (ne yapılacağı) - sadece ilk 5 için detay göster
                if i <= 5:
                    action = rec.get('action', '')
                    if action:
                        # Aksiyonu satırlara böl (max 52 karakter)
                        words = action.split()
                        current_line = "       → "
                        for word in words:
                            if len(current_line + word) <= 54:
                                current_line += word + " "
                            else:
                                report.append("║" + current_line.ljust(58) + "║")
                                current_line = "         " + word + " "
                        if current_line.strip():
                            report.append("║" + current_line.ljust(58) + "║")
                
                # Boş satır (her 3 item'da bir)
                if i % 3 == 0 and i < total_recs:
                    report.append("║" + " ".ljust(58) + "║")
        else:
            report.append("║" + "    🎉 Harika! Kritik bir iyileştirme önerisi yok.".ljust(58) + "║")
        
        report.append("║" + " ".ljust(58) + "║")
        report.append("╚" + "═" * 58 + "╝")
        
        # LCP ve CLS özet tablosu
        report.append("")
        report.append("📈 METRİK DETAYLARI:")
        report.append("─" * 40)
        report.append(f"{'Site'.ljust(20)} {'Puan'.ljust(8)} {'LCP'.ljust(8)} {'CLS'.ljust(8)}")
        report.append("─" * 40)
        report.append(f"{my_site['label'][:18].ljust(20)} {str(my_site['score']).ljust(8)} {str(my_site['lcp']).ljust(8)} {str(my_site['cls']).ljust(8)}")
        
        for comp in competitors:
            report.append(f"{comp['label'][:18].ljust(20)} {str(comp['score']).ljust(8)} {str(comp['lcp']).ljust(8)} {str(comp['cls']).ljust(8)}")
        
        report.append("─" * 40)
        report.append("")
        report.append("Bu rapor SEO-Pulse tarafından otomatik oluşturulmuştur.")
        
        return "\n".join(report)
    
    @staticmethod
    def _sanitize_for_email(text: str) -> str:
        """
        E-posta için metni UTF-8 güvenli hale getirir.
        Tüm özel ve gizli karakterleri temizler.
        
        Args:
            text: Temizlenecek metin
            
        Returns:
            UTF-8 uyumlu temiz metin
        """
        if not text:
            return ""
        
        # Özel karakterleri değiştir
        replacements = {
            '\xa0': ' ',      # Non-breaking space
            '\u200b': '',     # Zero-width space
            '\u200c': '',     # Zero-width non-joiner
            '\u200d': '',     # Zero-width joiner
            '\ufeff': '',     # BOM
            '\u00a0': ' ',    # Another non-breaking space representation
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # UTF-8 encode/decode ile temizle
        try:
            text = text.encode('utf-8', errors='replace').decode('utf-8')
        except Exception:
            pass
        
        return text
    
    @staticmethod
    def send_email(report_content: str) -> bool:
        """
        Hazırlanan raporu e-posta olarak gönderir.
        Modern EmailMessage sınıfı ile UTF-8 tam uyum.
        
        Args:
            report_content: Gönderilecek rapor içeriği
            
        Returns:
            Başarı durumu
        """
        Logger.progress("E-posta raporu gönderiliyor...")
        
        try:
            # Agresif temizlik - tüm içeriğe uygula
            safe_content = ReportGenerator._sanitize_for_email(report_content)
            
            # Subject - emoji ve özel karakter temizliği
            subject_text = "SEO-Pulse Performans Raporu - {}".format(
                datetime.now().strftime('%d/%m/%Y')
            )
            subject_text = ReportGenerator._sanitize_for_email(subject_text)
            # Ekstra güvenlik: tüm non-ASCII karakterleri kontrol et
            subject_text = subject_text.encode('ascii', 'replace').decode('ascii')
            
            # Gönderen bilgisi - sadece e-posta adresi (isim olmadan)
            sender_email = Config.EMAIL_SENDER
            
            # Modern EmailMessage sınıfı kullan
            msg = EmailMessage()
            msg['From'] = sender_email
            msg['To'] = sender_email
            msg['Subject'] = subject_text
            
            # İçeriği UTF-8 olarak ayarla
            msg.set_content(safe_content, charset='utf-8')
            
            # Gmail SMTP ile gönder
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, Config.EMAIL_PASSWORD)
                # send_message EmailMessage ile en uyumlu yöntem
                server.send_message(msg)
            
            Logger.success("Rapor e-posta ile başarıyla gönderildi!")
            return True
            
        except smtplib.SMTPAuthenticationError:
            Logger.error("E-posta kimlik doğrulama hatası - Şifre/uygulama şifresi kontrol edin")
            return False
        except smtplib.SMTPException as e:
            Logger.error(f"SMTP hatası: {e}")
            return False
        except Exception as e:
            Logger.error(f"E-posta gönderim hatası: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# ANA ORKESTRATÖR
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """
    Ana uygulama akışını yönetir:
    1. Siteleri veritabanından çeker
    2. Her siteyi PageSpeed API ile analiz eder
    3. Sonuçları veritabanına kaydeder
    4. Karşılaştırmalı rapor oluşturup mail atar
    """
    Logger.separator()
    Logger.info("SEO-Pulse v2.0 başlatılıyor...")
    Logger.separator()
    
    # Yapılandırma kontrolü
    if not Config.validate():
        Logger.error("Eksik yapılandırma! .env dosyasını kontrol edin.")
        sys.exit(1)
    
    # Veritabanı bağlantısı
    try:
        db = DatabaseManager()
    except Exception:
        Logger.error("Veritabanı bağlantısı kurulamadı. Program sonlandırılıyor.")
        sys.exit(1)
    
    # Siteleri çek
    sites = db.get_sites()
    if not sites:
        Logger.warning("Takip edilecek site bulunamadı!")
        sys.exit(0)
    
    Logger.separator()
    
    # Sonuç toplama değişkenleri
    my_site_data: Optional[Dict[str, Any]] = None
    competitor_data: List[Dict[str, Any]] = []
    success_count = 0
    error_count = 0
    
    # Her siteyi analiz et
    for index, site in enumerate(sites):
        site_url = site.get("site_url", "")
        site_label = site.get("label", "Bilinmeyen")
        site_id = site.get("id")
        
        Logger.info(f"[{index + 1}/{len(sites)}] {site_label}")
        
        # PageSpeed analizi yap
        try:
            metrics = PageSpeedAnalyzer.analyze(site_url)
            
            if metrics:
                # Veritabanına kaydet
                db.save_speed_log(site_id, metrics)
                
                # Sonuçları topla
                result = {
                    "label": site_label,
                    "url": site_url,
                    "score": metrics["score"],
                    "lcp": metrics["lcp"],
                    "cls": metrics["cls"],
                    "recommendations": metrics["recommendations"]
                }
                
                # Bizim sitemiz mi rakip mi kontrol et
                if site_label == Config.MY_SITE_LABEL:
                    my_site_data = result
                else:
                    competitor_data.append(result)
                
                success_count += 1
            else:
                error_count += 1
                Logger.warning(f"{site_label} için veri alınamadı, atlanıyor...")
                
        except Exception as e:
            error_count += 1
            Logger.error(f"Beklenmeyen hata ({site_label}): {e}")
        
        # Son site değilse API rate limit bekle
        if index < len(sites) - 1:
            Logger.wait(f"API rate limit bekleniyor ({Config.API_RATE_LIMIT_SECONDS}s)...")
            time.sleep(Config.API_RATE_LIMIT_SECONDS)
    
    Logger.separator()
    Logger.info(f"Tarama tamamlandı: {success_count} başarılı, {error_count} hatalı")
    
    # Rapor oluştur ve gönder
    if my_site_data:
        Logger.separator()
        report = ReportGenerator.generate_report(my_site_data, competitor_data)
        
        # Konsola da yazdır
        print("\n" + report + "\n")
        
        # E-posta gönder
        ReportGenerator.send_email(report)
    else:
        Logger.warning(f"'{Config.MY_SITE_LABEL}' etiketli site bulunamadı, rapor oluşturulamadı.")
        Logger.info("sites tablosunda 'Benim Sitem' etiketine sahip bir site olduğundan emin olun.")
    
    Logger.separator()
    Logger.success("SEO-Pulse işlemi tamamlandı!")
    Logger.separator()


if __name__ == "__main__":
    main()