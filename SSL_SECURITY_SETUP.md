# Guide d'Installation SSL/TLS et Sécurité - VPS Dev

Ce guide explique comment installer un certificat SSL/TLS (Let's Encrypt) et appliquer les normes de sécurité sur votre VPS de développement.

## 📋 Prérequis

- VPS avec accès root ou sudo
- Domaine pointant vers l'IP du VPS (ou utiliser l'IP directement)
- Ports 80 et 443 ouverts dans le firewall
- Nginx installé et configuré

## 🔐 Étape 1 : Installation de Certbot (Let's Encrypt)

### Sur le serveur VPS

```bash
# Mettre à jour les packages
apt update && apt upgrade -y

# Installer Certbot et le plugin Nginx
apt install -y certbot python3-certbot-nginx

# Vérifier l'installation
certbot --version
```

## 🌐 Étape 2 : Configuration Nginx pour SSL

### Option A : Avec un domaine

Si vous avez un domaine (ex: `dev.votre-domaine.com`) :

```bash
# Obtenir le certificat SSL
certbot --nginx -d dev.votre-domaine.com

# Suivre les instructions interactives :
# - Entrer votre email
# - Accepter les termes
# - Choisir de rediriger HTTP vers HTTPS (option 2 recommandé)
```

### Option B : Sans domaine (IP uniquement)

Let's Encrypt nécessite un domaine. Si vous n'avez pas de domaine :

**Option 1 : Utiliser un service de DNS dynamique (gratuit)**
- No-IP, DuckDNS, etc.

**Option 2 : Créer un certificat auto-signé (pour dev uniquement)**
```bash
# Générer un certificat auto-signé
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/nginx-selfsigned.key \
  -out /etc/ssl/certs/nginx-selfsigned.crt \
  -subj "/C=FR/ST=State/L=City/O=Organization/CN=YOUR_IP_OR_DOMAIN"
```

## ⚙️ Étape 3 : Configuration Nginx avec SSL

### Fichier de configuration Nginx avec SSL

Créez ou modifiez `/etc/nginx/sites-available/inventaire` :

```nginx
# Redirection HTTP vers HTTPS
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirection vers HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# Configuration HTTPS
server {
    listen 443 ssl http2;
    server_name YOUR_DOMAIN_OR_IP;

    # Certificats SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/YOUR_DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/YOUR_DOMAIN/privkey.pem;
    
    # Ou pour certificat auto-signé :
    # ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
    # ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;

    # Configuration SSL sécurisée
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # Headers de sécurité
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Proxy vers Backend Django
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
        
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }

    # Fichiers statiques
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /app/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Proxy vers Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Activer la configuration

```bash
# Créer le lien symbolique
ln -s /etc/nginx/sites-available/inventaire /etc/nginx/sites-enabled/

# Tester la configuration
nginx -t

# Recharger Nginx
systemctl reload nginx
```

## 🔒 Étape 4 : Configuration Firewall (UFW)

```bash
# Installer UFW si pas déjà installé
apt install -y ufw

# Autoriser SSH (important avant d'activer le firewall!)
ufw allow 22/tcp

# Autoriser HTTP et HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Autoriser le port 8000 pour Django (si nécessaire)
ufw allow 8000/tcp

# Activer le firewall
ufw enable

# Vérifier le statut
ufw status
```

## 🔄 Étape 5 : Renouvellement Automatique du Certificat

Let's Encrypt expire après 90 jours. Configurez le renouvellement automatique :

```bash
# Tester le renouvellement
certbot renew --dry-run

# Ajouter une tâche cron pour le renouvellement automatique
crontab -e

# Ajouter cette ligne (renouvelle 2 fois par jour)
0 0,12 * * * certbot renew --quiet --deploy-hook "systemctl reload nginx"
```

## ⚙️ Étape 6 : Mise à jour du fichier .env

Mettez à jour votre fichier `.env` sur le serveur :

```bash
# Éditer le fichier .env
nano /tmp/deployment/backend/.env
```

### Configuration pour HTTPS

```bash
# ============================================
# Configuration Django - PRODUCTION/DEV avec SSL
# ============================================
IS_PRODUCTION=True
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=your-secret-key-here

# Utiliser votre domaine ou IP
DJANGO_ALLOWED_HOSTS=YOUR_DOMAIN_OR_IP,www.YOUR_DOMAIN_OR_IP

# ============================================
# Sécurité SSL/TLS - ACTIVÉ
# ============================================
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# IMPORTANT : Si derrière Nginx (reverse proxy)
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')

# Origines CSRF autorisées (utiliser HTTPS)
CSRF_TRUSTED_ORIGINS=https://YOUR_DOMAIN_OR_IP,https://www.YOUR_DOMAIN_OR_IP

# ============================================
# CORS - Configuration sécurisée
# ============================================
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://YOUR_DOMAIN_OR_IP,https://www.YOUR_DOMAIN_OR_IP

CORS_ALLOW_CREDENTIALS=True
```

## 🔧 Étape 7 : Mise à jour de project/settings.py

Vérifiez que `project/settings.py` supporte le header proxy SSL :

```python
# Dans project/settings.py, décommenter si derrière Nginx :
SECURE_PROXY_SSL_HEADER = config('SECURE_PROXY_SSL_HEADER', default=None)
if SECURE_PROXY_SSL_HEADER:
    SECURE_PROXY_SSL_HEADER = eval(SECURE_PROXY_SSL_HEADER)
```

## ✅ Étape 8 : Vérifications de Sécurité

### Tester le certificat SSL

```bash
# Vérifier le certificat
openssl s_client -connect YOUR_DOMAIN_OR_IP:443 -servername YOUR_DOMAIN_OR_IP

# Tester avec curl
curl -I https://YOUR_DOMAIN_OR_IP
```

### Vérifier les headers de sécurité

```bash
# Vérifier les headers
curl -I https://YOUR_DOMAIN_OR_IP

# Devrait retourner :
# - Strict-Transport-Security
# - X-Frame-Options
# - X-Content-Type-Options
# - X-XSS-Protection
```

### Tester en ligne

- [SSL Labs](https://www.ssllabs.com/ssltest/) - Test complet du certificat SSL
- [SecurityHeaders.com](https://securityheaders.com/) - Vérification des headers de sécurité

## 🛡️ Étape 9 : Sécurisation Supplémentaire

### Désactiver les versions SSL/TLS obsolètes

Dans la configuration Nginx, assurez-vous d'utiliser uniquement TLS 1.2 et 1.3 :

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
```

### Limiter les méthodes HTTP

```nginx
# Autoriser uniquement les méthodes nécessaires
if ($request_method !~ ^(GET|HEAD|POST|PUT|DELETE|OPTIONS)$ ) {
    return 405;
}
```

### Masquer la version de Nginx

```nginx
# Dans http {} block
server_tokens off;
```

## 📝 Checklist de Sécurité

- [ ] Certificat SSL installé et valide
- [ ] Redirection HTTP → HTTPS configurée
- [ ] Headers de sécurité ajoutés (HSTS, X-Frame-Options, etc.)
- [ ] Firewall configuré (UFW)
- [ ] Renouvellement automatique du certificat configuré
- [ ] `.env` mis à jour avec les settings HTTPS
- [ ] `SECURE_PROXY_SSL_HEADER` configuré dans Django
- [ ] CORS configuré avec les origines HTTPS
- [ ] CSRF_TRUSTED_ORIGINS avec HTTPS
- [ ] Test SSL réussi (SSL Labs)
- [ ] Headers de sécurité vérifiés

## 🚨 Dépannage

### Problème : Certbot ne peut pas obtenir le certificat

**Solution** :
```bash
# Vérifier que le port 80 est ouvert
ufw status
netstat -tulpn | grep :80

# Vérifier que Nginx écoute sur le port 80
systemctl status nginx
```

### Problème : Erreur "redirect loop"

**Solution** : Vérifier que `SECURE_SSL_REDIRECT` n'est pas activé si Nginx gère déjà la redirection.

### Problème : Certificat auto-signé non accepté

**Solution** : Pour le développement, vous pouvez :
1. Ajouter une exception dans le navigateur
2. Utiliser un service comme Let's Encrypt avec un domaine
3. Utiliser un certificat signé par une autorité interne

## 📚 Ressources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://eff-certbot.readthedocs.io/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)

