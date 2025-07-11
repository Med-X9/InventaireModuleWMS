FROM nginx:1.25

# Suppression de la configuration par défaut
RUN rm /etc/nginx/conf.d/default.conf

# Copie de la configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exposition du port
EXPOSE 80

# Commande de démarrage
CMD ["nginx", "-g", "daemon off;"] 