# Guide Pratique - Installation SSL et Sécurité sur VPS Dev

Guide étape par étape pour installer SSL/TLS et appliquer les normes de sécurité sur votre VPS de développement (147.93.55.221).

## 🚀 Commandes à Exécuter sur le VPS

### Étape 1 : Connexion au VPS

```bash
ssh root@147.93.55.221
# ou
ssh votre-utilisateur@147.93.55.221
```

### Étape 2 : Mise à jour du système

```bash
apt update && apt upgrade -y
```

### Étape 3 : Installation de Certbot (Let's Encrypt)

```bash
# Installer Certbot et le plugin Nginx
apt install -y certbot python3-certbot-nginx

# Vérifier l'installation
certbot --version
```

### Étape 4 : Configuration du Firewall (UFW)

```bash
# Installer UFW si pas déjà installé
apt install -y ufw

# Configurer le firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH (IMPORTANT avant d'activer!)
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8000/tcp  # Django (si nécessaire)

# Activer le firewall
ufw enable

# Vérifier le statut
ufw status
```

### Étape 5 : Obtenir le Certificat SSL

#### Option A : Avec un domaine (recommandé)

Si vous avez un domaine pointant vers 147.93.55.221 :

```bash
# Remplacer dev.votre-domaine.com par votre domaine
certbot --nginx -d dev.votre-domaine.com --non-interactive --agree-tos --email votre-email@example.com --redirect
```

#### Option B : Sans domaine (certificat auto-signé pour dev)

```bash
# Créer les répertoires
mkdir -p /etc/ssl/private
mkdir -p /etc/ssl/certs

# Générer un certificat auto-signé
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/nginx-selfsigned.key \
  -out /etc/ssl/certs/nginx-selfsigned.crt \
  -subj "/C=FR/ST=State/L=City/O=Organization/CN=147.93.55.221"
```

### Étape 6 : Configuration Nginx avec SSL

Éditer la configuration Nginx :

```bash
nano /etc/nginx/sites-available/default
# ou
nano /etc/nginx/conf.d/inventaire.conf
```

#### Configuration complète avec SSL :

```nginx
# Redirection HTTP vers HTTPS
server {
    listen 80;
    server_name 147.93.55.221;
    
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
    server_name 147.93.55.221;
    client_max_body_size 100M;

    # Certificats SSL
    # Pour Let's Encrypt (remplacer par votre domaine) :
    # ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;
    
    # Pour certificat auto-signé :
    ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;

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

    # Masquer la version de Nginx
    server_tokens off;

    upstream django_app {
        server web:8000;
    }

    upstream frontend_app {
        server frontend-app:80;
    }

    # Admin Django
    location /admin/ {
        proxy_pass http://django_app$request_uri;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # API Web
    location /web/api/ {
        proxy_pass http://django_app$request_uri;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # API Mobile
    location /mobile/api/ {
        proxy_pass http://django_app$request_uri;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # API Auth
    location /api/auth/ {
        proxy_pass http://django_app$request_uri;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # API Masterdata
    location /masterdata/api/ {
        proxy_pass http://django_app$request_uri;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Swagger
    location /swagger/ {
        proxy_pass http://django_app$request_uri;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Redoc
    location /redoc/ {
        proxy_pass http://django_app$request_uri;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Frontend
    location / {
        proxy_pass http://frontend_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_intercept_errors on;
        error_page 404 = @fallback;
    }

    location @fallback {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        rewrite ^ /index.html break;
        proxy_pass http://frontend_app;
    }

    # Fichiers statiques
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        access_log off;
        add_header Cache-Control "public, no-transform";
    }

    # Fichiers media
    location /media/ {
        alias /app/media/;
        expires 30d;
        access_log off;
        add_header Cache-Control "public, no-transform";
    }
}
```

### Étape 7 : Tester et Recharger Nginx

```bash
# Tester la configuration
nginx -t

# Si OK, recharger Nginx
systemctl reload nginx

# Vérifier le statut
systemctl status nginx
```

### Étape 8 : Configuration Fail2Ban (Protection contre les attaques)

```bash
# Installer Fail2Ban
apt install -y fail2ban

# Créer la configuration
cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
EOF

# Activer et démarrer Fail2Ban
systemctl enable fail2ban
systemctl restart fail2ban

# Vérifier le statut
fail2ban-client status
```

### Étape 9 : Mise à jour du fichier .env

```bash
# Aller dans le répertoire de déploiement
cd /tmp/deployment/backend

# Éditer le fichier .env
nano .env
```

Mettre à jour avec ces valeurs :

```bash
# ============================================
# Configuration Django - DEV avec SSL
# ============================================
IS_PRODUCTION=True
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=votre-clé-secrète-ici

# Utiliser l'IP du serveur
DJANGO_ALLOWED_HOSTS=147.93.55.221,localhost,127.0.0.1

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
CSRF_TRUSTED_ORIGINS=https://147.93.55.221

# ============================================
# CORS - Configuration sécurisée
# ============================================
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://147.93.55.221

CORS_ALLOW_CREDENTIALS=True
```

### Étape 10 : Redémarrer les Containers Docker

```bash
# Aller dans le répertoire de déploiement
cd /tmp/deployment/backend

# Redémarrer les containers
docker-compose down
docker-compose up -d

# Vérifier les logs
docker-compose logs -f
```

### Étape 11 : Renouvellement Automatique du Certificat (Let's Encrypt)

Si vous utilisez Let's Encrypt :

```bash
# Tester le renouvellement
certbot renew --dry-run

# Configurer le renouvellement automatique
crontab -e

# Ajouter cette ligne (renouvelle 2 fois par jour)
0 0,12 * * * certbot renew --quiet --deploy-hook "systemctl reload nginx"
```

## ✅ Vérifications

### Tester le certificat SSL

```bash
# Vérifier avec curl
curl -I https://147.93.55.221

# Devrait retourner les headers de sécurité
```

### Vérifier les headers de sécurité

```bash
curl -I https://147.93.55.221 | grep -i "strict-transport-security"
curl -I https://147.93.55.221 | grep -i "x-frame-options"
```

### Tester en ligne

- Visiter : `https://147.93.55.221`
- Vérifier le certificat dans le navigateur
- Tester avec [SSL Labs](https://www.ssllabs.com/ssltest/) (si vous avez un domaine)

## 🔧 Dépannage

### Problème : Nginx ne démarre pas

```bash
# Vérifier les erreurs
nginx -t

# Vérifier les logs
tail -f /var/log/nginx/error.log
```

### Problème : Certificat non accepté (auto-signé)

C'est normal pour un certificat auto-signé. Le navigateur affichera un avertissement. Pour le développement, vous pouvez :
1. Cliquer sur "Avancé" puis "Continuer vers le site"
2. Ou utiliser un domaine avec Let's Encrypt

### Problème : Erreur 502 Bad Gateway

```bash
# Vérifier que les containers Docker tournent
docker ps

# Vérifier les logs des containers
docker-compose logs web
docker-compose logs nginx
```

## 📝 Checklist Finale

- [ ] Certbot installé
- [ ] Certificat SSL obtenu (Let's Encrypt ou auto-signé)
- [ ] Nginx configuré avec SSL
- [ ] Firewall (UFW) configuré
- [ ] Fail2Ban installé et configuré
- [ ] Headers de sécurité ajoutés
- [ ] Fichier .env mis à jour avec HTTPS
- [ ] Containers Docker redémarrés
- [ ] Renouvellement automatique configuré (Let's Encrypt)
- [ ] Test HTTPS réussi
- [ ] Headers de sécurité vérifiés

## 🎯 Résultat Attendu

Après ces étapes, vous devriez avoir :
- ✅ HTTPS activé sur votre VPS
- ✅ Redirection automatique HTTP → HTTPS
- ✅ Headers de sécurité configurés
- ✅ Protection contre les attaques (Fail2Ban)
- ✅ Firewall configuré
- ✅ Application accessible via `https://147.93.55.221`

