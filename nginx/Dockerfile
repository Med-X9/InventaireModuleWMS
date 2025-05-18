FROM nginx:1.25

# Suppression de la configuration par défaut
RUN rm /etc/nginx/conf.d/default.conf

# Copie des configurations
COPY nginx.conf /etc/nginx/conf.d/
COPY ssl.conf /etc/nginx/conf.d/

# Exposition des ports
EXPOSE 80 443

# Commande de démarrage
CMD ["nginx", "-g", "daemon off;"] 