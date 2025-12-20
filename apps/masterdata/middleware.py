"""
Middleware pour injecter le script JavaScript du bouton "Créer des équipes"
"""
from django.utils.deprecation import MiddlewareMixin


class CreateTeamsButtonMiddleware(MiddlewareMixin):
    """
    Middleware qui injecte le script JavaScript pour ajouter le bouton
    "Créer des équipes" dans la page admin UserApp
    """
    
    def process_response(self, request, response):
        # Vérifier si on est sur la page UserApp changelist
        if (request.path.startswith('/admin/users/userapp/') and 
            '/create-teams' not in request.path and
            hasattr(response, 'content')):
            
            try:
                content = response.content.decode('utf-8')
                
                # Script JavaScript pour ajouter le bouton
                script = """
                <script>
                (function() {
                    function addButton() {
                        const objectTools = document.querySelector('ul.object-tools');
                        if (!objectTools) {
                            return false;
                        }
                        if (objectTools.querySelector('a[href*="create-teams"]')) {
                            return true;
                        }
                        const li = document.createElement('li');
                        const link = document.createElement('a');
                        link.href = '/admin/users/userapp/create-teams/';
                        link.className = 'addlink';
                        link.style.cssText = 'background-color: #28a745 !important; color: white !important; padding: 8px 15px !important; border-radius: 4px !important; text-decoration: none !important;';
                        link.textContent = '👥 Créer des équipes';
                        li.appendChild(link);
                        objectTools.appendChild(li);
                        console.log('✅ Bouton "Créer des équipes" ajouté');
                        return true;
                    }
                    function tryAdd() {
                        if (!addButton()) {
                            setTimeout(tryAdd, 300);
                        }
                    }
                    if (document.readyState === 'loading') {
                        document.addEventListener('DOMContentLoaded', tryAdd);
                    } else {
                        tryAdd();
                    }
                    setTimeout(tryAdd, 500);
                    setTimeout(tryAdd, 1500);
                    setTimeout(tryAdd, 3000);
                })();
                </script>
                """
                
                # Injecter le script avant la fermeture de </body>
                if '</body>' in content:
                    content = content.replace('</body>', script + '</body>')
                    response.content = content.encode('utf-8')
                    
            except (UnicodeDecodeError, AttributeError):
                # Si le contenu n'est pas du texte ou n'a pas d'attribut content, ignorer
                pass
        
        return response
