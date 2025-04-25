FROM nginx:1.25-alpine

# Installation des outils nécessaires
RUN apk add --no-cache certbot certbot-nginx

# Suppression de la configuration par défaut
RUN rm /etc/nginx/conf.d/default.conf

# Copie des configurations
COPY nginx.conf /etc/nginx/conf.d/
COPY ssl.conf /etc/nginx/conf.d/

# Création des dossiers pour les certificats SSL
RUN mkdir -p /etc/letsencrypt/live/your-domain.com

# Exposition des ports
EXPOSE 80 443

# Commande de démarrage
CMD ["nginx", "-g", "daemon off;"] 