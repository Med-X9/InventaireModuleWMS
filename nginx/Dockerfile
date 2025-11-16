FROM nginx:1.25

# Supprimer la conf par défaut
RUN rm /etc/nginx/conf.d/default.conf

# Copier notre conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]