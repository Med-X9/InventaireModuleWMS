"""
Middleware pour injecter le script JavaScript du bouton "Générer des personnes"
"""
from django.utils.deprecation import MiddlewareMixin


class CreatePersonnesButtonMiddleware(MiddlewareMixin):
    """
    Middleware qui injecte le script JavaScript pour ajouter le bouton
    "Générer des personnes" dans la page admin Personne
    """
    
    def process_response(self, request, response):
        # Vérifier si on est sur la page Personne changelist
        if (request.path.startswith('/admin/inventory/personne/') and 
            '/create-personnes' not in request.path and
            hasattr(response, 'content')):
            
            try:
                content = response.content.decode('utf-8')
                
                # Script JavaScript pour ajouter le bouton
                script = """
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
                <script>
                (function() {
                    console.log('🟢 Middleware CreatePersonnesButton exécuté');
                    
                    function addButton() {
                        // Vérifier si le bouton existe déjà
                        if (document.querySelector('a[href*="create-personnes"]')) {
                            console.log('✅ Bouton existe déjà');
                            return true;
                        }
                        
                        // Méthode 1: Chercher ul.object-tools (Django classique)
                        let container = document.querySelector('ul.object-tools');
                        
                        // Méthode 2: Chercher le conteneur des boutons Jazzmin (à côté du bouton "Ajouter")
                        if (!container) {
                            // Chercher le bouton "Ajouter personne"
                            const addButton = document.querySelector('a[href*="/add/"]');
                            if (addButton) {
                                container = addButton.parentElement;
                                console.log('🔍 Conteneur trouvé via bouton Ajouter:', container);
                            }
                        }
                        
                        // Méthode 3: Chercher directement dans le breadcrumb/header
                        if (!container) {
                            container = document.querySelector('.breadcrumb, .object-tools, .submit-row, div[style*="float"]');
                            console.log('🔍 Conteneur alternatif trouvé:', container);
                        }
                        
                        if (!container) {
                            console.warn('⚠️ Aucun conteneur trouvé pour le bouton');
                            return false;
                        }
                        
                        console.log('✅ Conteneur trouvé:', container);
                        
                        // Créer le bouton
                        const link = document.createElement('a');
                        link.href = '/admin/inventory/personne/create-personnes/';
                        link.className = 'btn btn-success addlink';
                        link.style.cssText = 'background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important; color: white !important; padding: 10px 20px !important; border-radius: 8px !important; text-decoration: none !important; display: inline-flex !important; align-items: center !important; gap: 8px !important; font-weight: 600 !important; box-shadow: 0 4px 12px rgba(17, 153, 142, 0.3) !important; transition: all 0.3s ease !important; border: none !important; margin-left: 10px !important;';
                        link.innerHTML = '<i class="fas fa-user-plus"></i> Générer des personnes';
                        
                        // Insérer le bouton
                        if (container.tagName === 'UL') {
                            const li = document.createElement('li');
                            li.appendChild(link);
                            container.appendChild(li);
                        } else {
                            // Insérer directement dans le conteneur
                            container.appendChild(link);
                        }
                        
                        console.log('✅ Bouton "Générer des personnes" ajouté avec succès');
                        return true;
                    }
                    
                    let attempts = 0;
                    const maxAttempts = 20;
                    
                    function tryAdd() {
                        attempts++;
                        console.log(`🔄 Tentative ${attempts}/${maxAttempts} d'ajout du bouton...`);
                        
                        if (addButton()) {
                            console.log('✅ Bouton ajouté avec succès!');
                            return;
                        }
                        
                        if (attempts < maxAttempts) {
                            setTimeout(tryAdd, 300);
                        } else {
                            console.error('❌ Impossible d\'ajouter le bouton après', maxAttempts, 'tentatives');
                        }
                    }
                    
                    if (document.readyState === 'loading') {
                        document.addEventListener('DOMContentLoaded', tryAdd);
                    } else {
                        tryAdd();
                    }
                    
                    // Tentatives supplémentaires pour s'assurer que le DOM est complètement chargé
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

